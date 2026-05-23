"""
Column policy enforcement.

Per-table policy controlling what columns an agent can access via execute_query.
Uses AST parsing to extract columns from SELECT/WHERE and validate against policy.

Policy modes:
- permissive: tables not in policy → allow all (backward compatible)
- strict: tables not in policy → rejected
"""

import json
from pathlib import Path
from typing import Optional

import sqlglot
from sqlglot import exp

from postgresql_mcp.guardrails.models import (
    GuardrailResult,
    TablePolicy,
    ColumnPolicyConfig,
)
from postgresql_mcp.guardrails.sql_parser import (
    parse_query,
    ParsedQuery,
    is_aggregate_expression,
    is_pure_aggregate,
    extract_select_columns,
    extract_group_by_columns,
    extract_where_filter_columns,
    resolve_table_alias,
    has_tautological_where,
)

# Backward-compatible alias
PolicyCheckResult = GuardrailResult


def load_column_policy(
    policy_json: Optional[str] = None,
    policy_file: Optional[str] = None,
    mode: str = "permissive",
    default_schema: str = "public",
) -> ColumnPolicyConfig:
    """
    Load column policy from JSON string or file.

    Args:
        policy_json: Inline JSON string (COLUMN_POLICY env var).
        policy_file: Path to JSON file (COLUMN_POLICY_FILE, takes priority).
        mode: "permissive" or "strict".
        default_schema: Default schema for normalization.

    Returns:
        ColumnPolicyConfig with parsed policies.
    """
    raw: dict = {}

    if policy_file:
        path = Path(policy_file)
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
    elif policy_json:
        raw = json.loads(policy_json)

    policies: dict[str, TablePolicy] = {}
    for table_name, table_config in raw.items():
        # Normalize table name
        normalized = _normalize_table_name(table_name, default_schema)
        policies[normalized] = TablePolicy(
            allowed_columns=[c.lower() for c in table_config.get("allowed_columns", [])],
            sampleable_columns=[c.lower() for c in table_config.get("sampleable_columns", [])],
            required_filter_columns=[c.lower() for c in table_config.get("required_filter_columns", [])],
            allow_aggregates_without_filter=table_config.get("allow_aggregates_without_filter", False),
            group_by_columns=[c.lower() for c in table_config.get("group_by_columns", [])],
            max_rows=table_config.get("max_rows"),
        )

    return ColumnPolicyConfig(policies=policies, mode=mode, default_schema=default_schema)


# ─── Policy Enforcement ─────────────────────────────────────────────────────


def check_column_policy(sql: str, policy: ColumnPolicyConfig) -> PolicyCheckResult:
    """
    Validate a SQL query against column policy.

    Checks:
    1. All tables in query are in policy (strict mode) or allowed (permissive)
    2. All columns in SELECT are in allowed_columns for their table
    3. required_filter_columns are present in WHERE with concrete values
    4. Aggregate exception for pure aggregate queries

    Args:
        sql: Raw SQL query string.
        policy: Loaded column policy configuration.

    Returns:
        PolicyCheckResult indicating whether the query is blocked.
    """
    if not policy.policies:
        # No policy configured — allow all
        return PolicyCheckResult(is_blocked=False)

    parsed = parse_query(sql, policy.default_schema)
    if parsed.parse_error:
        return PolicyCheckResult(
            is_blocked=True,
            reason=f"Failed to parse query: {parsed.parse_error}",
        )

    # ─── 1. Table access check ───────────────────────────────────────────
    for table in parsed.tables:
        if table not in policy.policies:
            if policy.mode == "strict":
                return PolicyCheckResult(
                    is_blocked=True,
                    reason=f"Table '{table}' is not in the column policy. Access denied in strict mode.",
                )
            # permissive mode: allow tables not in policy

    # Get tables that ARE in policy (we'll validate columns for these)
    policy_tables = [t for t in parsed.tables if t in policy.policies]
    if not policy_tables:
        # No policy tables referenced — in permissive mode, allow
        return PolicyCheckResult(is_blocked=False)

    # ─── 2. Parse the actual statement for column validation ─────────────
    try:
        statements = sqlglot.parse(sql, dialect="postgres")
        statements = [s for s in statements if s is not None]
        if not statements:
            return PolicyCheckResult(is_blocked=True, reason="No valid statements.")
        stmt = statements[0]
    except sqlglot.errors.ParseError as e:
        return PolicyCheckResult(is_blocked=True, reason=f"Parse error: {e}")

    # ─── 3. Check if pure aggregate (skip filter requirement) ────────────
    is_agg = is_pure_aggregate(stmt)
    group_by_cols = extract_group_by_columns(stmt)

    # ─── 4. Column validation ────────────────────────────────────────────
    selected_columns = extract_select_columns(stmt)
    for col_ref in selected_columns:
        table_name, col_name = _resolve_column_table(
            col_ref, parsed.tables, policy, stmt
        )
        if table_name and table_name in policy.policies:
            table_policy = policy.policies[table_name]
            if col_name.lower() not in table_policy.allowed_columns:
                return PolicyCheckResult(
                    is_blocked=True,
                    reason=(
                        f"Column '{col_name}' is not allowed for table '{table_name}'. "
                        f"Allowed columns: {table_policy.allowed_columns}"
                    ),
                )

    # ─── 5. GROUP BY validation ──────────────────────────────────────────
    if group_by_cols:
        for col_ref in group_by_cols:
            table_name, col_name = _resolve_column_table(
                col_ref, parsed.tables, policy, stmt
            )
            if table_name and table_name in policy.policies:
                table_policy = policy.policies[table_name]
                if col_name.lower() not in table_policy.group_by_columns:
                    return PolicyCheckResult(
                        is_blocked=True,
                        reason=(
                            f"Column '{col_name}' is not allowed in GROUP BY for table '{table_name}'. "
                            f"Allowed GROUP BY columns: {table_policy.group_by_columns}"
                        ),
                    )

    # ─── 6. Tautology detection ────────────────────────────────────────────
    has_required_filter_tables = any(
        policy.policies[t].required_filter_columns for t in policy_tables
    )
    if has_required_filter_tables and has_tautological_where(stmt):
        return PolicyCheckResult(
            is_blocked=True,
            reason="Tautological WHERE clause detected (e.g. 1=1, true, id=id). Use a real filter.",
        )

    # ─── 7. Required filter columns check ────────────────────────────────
    for table in policy_tables:
        table_policy = policy.policies[table]
        if not table_policy.required_filter_columns:
            continue

        # Aggregate exception: skip filter if query is aggregate-safe
        if table_policy.allow_aggregates_without_filter:
            if is_agg and not group_by_cols:
                # Pure aggregate with no GROUP BY (e.g. SELECT COUNT(*) FROM users)
                continue
            if group_by_cols:
                # GROUP BY present — check all GROUP BY cols are allowed dimensions
                all_group_by_allowed = True
                for col_ref in group_by_cols:
                    _, col_name = _resolve_column_table(col_ref, parsed.tables, policy, stmt)
                    if col_name.lower() not in table_policy.group_by_columns:
                        all_group_by_allowed = False
                        break
                if all_group_by_allowed and _is_aggregate_with_dimensions(stmt, table_policy):
                    continue

        # Check WHERE references a required filter column with concrete value
        where_columns = extract_where_filter_columns(stmt)
        has_required_filter = any(
            col.lower() in table_policy.required_filter_columns
            for col in where_columns
        )
        if not has_required_filter:
            return PolicyCheckResult(
                is_blocked=True,
                reason=(
                    f"Query on '{table}' requires a WHERE filter on one of: "
                    f"{table_policy.required_filter_columns}"
                ),
            )

    # ─── 8. Max rows check ───────────────────────────────────────────────
    for table in policy_tables:
        table_policy = policy.policies[table]
        if table_policy.max_rows is not None and parsed.limit is not None:
            if parsed.limit > table_policy.max_rows:
                return PolicyCheckResult(
                    is_blocked=True,
                    reason=(
                        f"LIMIT {parsed.limit} exceeds max_rows ({table_policy.max_rows}) "
                        f"for table '{table}'."
                    ),
                )

    return PolicyCheckResult(is_blocked=False)


# ─── Internal Helpers ────────────────────────────────────────────────────────


def _normalize_table_name(name: str, default_schema: str) -> str:
    """Normalize table name to schema.table format."""
    parts = name.strip().lower().split(".")
    if len(parts) == 1:
        return f"{default_schema}.{parts[0]}"
    return ".".join(parts)


def _is_aggregate_with_dimensions(stmt: exp.Expression, table_policy: "TablePolicy") -> bool:
    """
    Check if every non-aggregate column in SELECT is in the table's group_by_columns.

    Handles: SELECT department, COUNT(*) FROM users GROUP BY department
    """
    select = stmt.find(exp.Select)
    if select is None:
        return False

    for expr in select.expressions:
        if is_aggregate_expression(expr):
            continue
        col_name = _get_column_name_from_expr(expr)
        if col_name is None:
            return False
        if col_name.lower() not in table_policy.group_by_columns:
            return False
    return True


def _get_column_name_from_expr(expr: exp.Expression) -> str | None:
    """Extract column name from a simple column expression (possibly aliased)."""
    if isinstance(expr, exp.Alias):
        expr = expr.this
    if isinstance(expr, exp.Column):
        return expr.name
    return None


def _resolve_column_table(
    col_ref: str,
    tables: list[str],
    policy: ColumnPolicyConfig,
    stmt: exp.Expression,
) -> tuple[Optional[str], str]:
    """
    Resolve a column reference to its table.

    If qualified (table.col or alias.col), resolve alias → real table.
    If unqualified and single policy table, assume that table.
    """
    parts = col_ref.split(".", 1)
    if len(parts) == 2:
        table_ref, col_name = parts
        real_table = resolve_table_alias(table_ref, stmt, policy.default_schema)
        return (real_table, col_name)
    else:
        col_name = parts[0]
        policy_tables = [t for t in tables if t in policy.policies]
        if len(policy_tables) == 1:
            return (policy_tables[0], col_name)
        return (None, col_name)
