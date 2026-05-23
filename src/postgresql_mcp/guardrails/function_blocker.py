"""
Function allowlist/blocklist enforcement.

Modes:
- allowlist: Only explicitly allowed functions can be called (text2sql/sensitive default)
- blacklist: Only known dangerous functions are blocked (general default, backward compat)

When ALLOWED_FUNCTIONS env var is set (JSON array), allowlist mode is used.
Otherwise, security profile determines mode.
"""

import json
from typing import Optional

from postgresql_mcp.guardrails.models import GuardrailResult
from postgresql_mcp.guardrails.sql_parser import parse_query

# ─── Default Allowlist (safe for text2sql) ───────────────────────────────────

DEFAULT_ALLOWED_FUNCTIONS: frozenset[str] = frozenset([
    # Aggregates
    "count", "sum", "avg", "min", "max",
    "array_agg", "string_agg", "json_agg", "jsonb_agg",
    "bool_and", "bool_or",
    # String
    "lower", "upper", "length", "trim", "ltrim", "rtrim",
    "substring", "left", "right", "replace", "concat",
    "concat_ws", "initcap", "repeat", "reverse", "split_part",
    "position", "strpos", "translate", "format",
    "starts_with", "ends_with", "regexp_replace", "regexp_match",
    # Date/Time
    "now", "current_date", "current_timestamp",
    "date_trunc", "date_part", "extract", "age",
    "to_char", "to_date", "to_timestamp",
    "make_date", "make_timestamp", "make_interval",
    # Math
    "round", "ceil", "ceiling", "floor", "abs",
    "mod", "power", "sqrt", "sign", "trunc",
    "greatest", "least", "random",
    # Null handling
    "coalesce", "nullif",
    # Type casting (sqlglot represents these as functions)
    "cast", "try_cast",
    # Conditional
    "case",
    # JSON
    "json_build_object", "jsonb_build_object",
    "json_build_array", "jsonb_build_array",
    "json_extract_path_text", "jsonb_extract_path_text",
    "json_array_length", "jsonb_array_length",
    "to_json", "to_jsonb", "row_to_json",
    # Array
    "array_length", "array_position", "unnest",
    "array_to_string", "string_to_array",
    # Window functions (safe for read)
    "row_number", "rank", "dense_rank", "ntile",
    "lag", "lead", "first_value", "last_value", "nth_value",
    # Boolean / comparison (sqlglot internals)
    "if", "iff", "ifnull",
    # Misc safe
    "generate_series", "exists",
])

# ─── Dangerous Functions (blacklist mode, backward compat) ────────────────────

DANGEROUS_FUNCTIONS: frozenset[str] = frozenset([
    "pg_sleep",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_reload_conf",
    "pg_rotate_logfile",
    "lo_import", "lo_export", "lo_unlink",
    "dblink", "dblink_exec",
    "pg_read_file", "pg_read_binary_file",
    "pg_write_file",
    "pg_ls_dir", "pg_stat_file",
    "inet_server_addr", "inet_server_port",
    "pg_advisory_lock", "pg_advisory_xact_lock",
    "pg_advisory_unlock", "pg_advisory_unlock_all",
    "current_setting", "set_config",
    "pg_notify",
])


def load_allowed_functions(allowed_functions_json: Optional[str]) -> Optional[frozenset[str]]:
    """
    Parse ALLOWED_FUNCTIONS JSON into a frozenset.

    Returns None if not configured (use mode-based default).
    """
    if not allowed_functions_json:
        return None
    funcs = json.loads(allowed_functions_json)
    return frozenset(f.lower() for f in funcs)


def check_functions(
    sql: str,
    mode: str = "blacklist",
    allowed_functions: Optional[frozenset[str]] = None,
    default_schema: str = "public",
) -> GuardrailResult:
    """
    Validate function calls in a SQL query.

    Args:
        sql: Raw SQL query.
        mode: "allowlist" or "blacklist".
        allowed_functions: Custom allowlist (overrides default if provided).
        default_schema: Default schema for parsing.

    Returns:
        GuardrailResult — blocked if disallowed function is found.
    """
    parsed = parse_query(sql, default_schema)
    if parsed.parse_error:
        return GuardrailResult(is_blocked=False)

    if not parsed.functions:
        return GuardrailResult(is_blocked=False)

    if mode == "allowlist":
        allowlist = allowed_functions if allowed_functions is not None else DEFAULT_ALLOWED_FUNCTIONS
        for func_name in parsed.functions:
            if func_name not in allowlist:
                return GuardrailResult(
                    is_blocked=True,
                    reason=(
                        f"Function '{func_name}' is not in the allowed functions list. "
                        f"Only allowlisted functions can be used."
                    ),
                )
    else:
        # Blacklist mode
        for func_name in parsed.functions:
            if func_name in DANGEROUS_FUNCTIONS:
                return GuardrailResult(
                    is_blocked=True,
                    reason=f"Function '{func_name}' is blocked (dangerous function).",
                )

    return GuardrailResult(is_blocked=False)


# Backward-compatible alias
FunctionCheckResult = GuardrailResult
