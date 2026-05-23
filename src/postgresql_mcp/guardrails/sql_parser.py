"""
SQL AST parser using sqlglot.

Extracts structural information from SQL queries for security validation:
- Tables referenced (FROM, JOIN, subqueries)
- Columns selected
- Functions called
- WHERE conditions
- LIMIT/OFFSET values
- Query shape (CTE, UNION, subquery, etc.)
"""

from dataclasses import dataclass, field
from typing import Optional

import sqlglot
from sqlglot import exp


@dataclass
class ParsedQuery:
    """Structural information extracted from a parsed SQL query."""

    tables: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    has_star: bool = False
    has_cte: bool = False
    has_recursive_cte: bool = False
    has_subquery: bool = False
    has_set_operation: bool = False
    has_lateral: bool = False
    limit: Optional[int] = None
    offset: Optional[int] = None
    statement_count: int = 0
    parse_error: Optional[str] = None


def parse_query(sql: str, default_schema: str = "public") -> ParsedQuery:
    """
    Parse a SQL query and extract structural information.

    Args:
        sql: SQL query string.
        default_schema: Default schema for unqualified table names.

    Returns:
        ParsedQuery with extracted information.
    """
    result = ParsedQuery()

    try:
        statements = sqlglot.parse(sql, dialect="postgres")
    except sqlglot.errors.ParseError as e:
        result.parse_error = str(e)
        return result

    # Filter out None statements (empty strings)
    statements = [s for s in statements if s is not None]
    result.statement_count = len(statements)

    if not statements:
        result.parse_error = "No valid SQL statements found."
        return result

    stmt = statements[0]

    # Extract tables
    result.tables = extract_tables(stmt, default_schema)

    # Detect star/wildcard
    result.has_star = _has_star_select(stmt)

    # Detect CTE
    result.has_cte = _has_cte(stmt)
    result.has_recursive_cte = _has_recursive_cte(stmt)

    # Detect subqueries
    result.has_subquery = _has_subquery(stmt)

    # Detect set operations (UNION, INTERSECT, EXCEPT)
    result.has_set_operation = _has_set_operation(stmt)

    # Detect LATERAL
    result.has_lateral = _has_lateral(stmt)

    # Extract LIMIT/OFFSET
    result.limit = _extract_limit(stmt)
    result.offset = _extract_offset(stmt)

    # Extract functions
    result.functions = _extract_functions(stmt)

    # Extract columns
    result.columns = _extract_columns(stmt)

    return result


def extract_tables(statement: exp.Expression, default_schema: str = "public") -> list[str]:
    """
    Extract all table references from a SQL statement.

    Normalizes to schema.table format. Searches FROM, JOIN, subqueries, CTEs.

    Args:
        statement: Parsed sqlglot expression.
        default_schema: Schema to prepend for unqualified table names.

    Returns:
        List of normalized table names (e.g. ["public.users", "pg_catalog.pg_shadow"]).
    """
    tables = set()

    for table in statement.find_all(exp.Table):
        table_name = table.name
        if not table_name:
            continue

        # Get schema (catalog.schema.table or schema.table or table)
        db = table.db  # schema in sqlglot's terminology for PostgreSQL
        catalog = table.catalog

        if catalog:
            # catalog.schema.table → catalog.schema.table
            normalized = f"{catalog}.{db}.{table_name}"
        elif db:
            # schema.table → schema.table
            normalized = f"{db}.{table_name}"
        else:
            # unqualified → default_schema.table
            normalized = f"{default_schema}.{table_name}"

        tables.add(normalized.lower())

    return sorted(tables)


def _has_star_select(stmt: exp.Expression) -> bool:
    """Detect SELECT * or table.* (but NOT COUNT(*))."""
    for star in stmt.find_all(exp.Star):
        # Check if this star is inside an aggregate function like COUNT(*)
        parent = star.parent
        if isinstance(parent, exp.Anonymous) or isinstance(parent, exp.Count):
            continue
        # Check parent chain for any aggregate function
        node = parent
        is_in_function = False
        while node is not None:
            if isinstance(node, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
                is_in_function = True
                break
            if isinstance(node, exp.Select):
                break
            node = node.parent
        if not is_in_function:
            return True
    return False


def _has_cte(stmt: exp.Expression) -> bool:
    """Detect WITH clause."""
    return stmt.find(exp.With) is not None


def _has_recursive_cte(stmt: exp.Expression) -> bool:
    """Detect recursive CTE."""
    with_clause = stmt.find(exp.With)
    if with_clause is None:
        return False
    return with_clause.args.get("recursive", False)


def _has_subquery(stmt: exp.Expression) -> bool:
    """Detect subqueries (nested SELECT in SELECT list, FROM, WHERE, HAVING)."""
    # Find all Subquery nodes that aren't the top-level statement or CTE
    for subquery in stmt.find_all(exp.Subquery):
        # Skip CTE definitions
        parent = subquery.parent
        if isinstance(parent, exp.With):
            continue
        return True
    # Also check for IN (SELECT ...), EXISTS (SELECT ...), etc.
    for select in stmt.find_all(exp.Select):
        if select is stmt.find(exp.Select):
            continue  # Skip the outermost SELECT
        # Check it's not a CTE body
        node = select.parent
        is_cte = False
        is_set_op = False
        while node is not None:
            if isinstance(node, exp.CTE):
                is_cte = True
                break
            if isinstance(node, (exp.Union, exp.Intersect, exp.Except)):
                is_set_op = True
                break
            if node is stmt:
                break
            node = node.parent
        if not is_cte and not is_set_op:
            return True
    return False


def _has_set_operation(stmt: exp.Expression) -> bool:
    """Detect UNION, INTERSECT, EXCEPT."""
    return stmt.find(exp.Union) is not None or stmt.find(exp.Intersect) is not None or stmt.find(exp.Except) is not None


def _has_lateral(stmt: exp.Expression) -> bool:
    """Detect LATERAL joins."""
    return stmt.find(exp.Lateral) is not None


def _extract_limit(stmt: exp.Expression) -> Optional[int]:
    """Extract LIMIT value from top-level query."""
    limit_node = stmt.find(exp.Limit)
    if limit_node is None:
        return None
    limit_expr = limit_node.expression
    if isinstance(limit_expr, exp.Literal) and limit_expr.is_int:
        return int(limit_expr.this)
    return None


def _extract_offset(stmt: exp.Expression) -> Optional[int]:
    """Extract OFFSET value from top-level query."""
    offset_node = stmt.find(exp.Offset)
    if offset_node is None:
        return None
    offset_expr = offset_node.expression
    if isinstance(offset_expr, exp.Literal) and offset_expr.is_int:
        return int(offset_expr.this)
    return None


def _extract_functions(stmt: exp.Expression) -> list[str]:
    """Extract all function names called in the query."""
    functions = set()
    for func in stmt.find_all(exp.Func):
        if isinstance(func, exp.Anonymous):
            # Anonymous nodes hold user-defined / unrecognized function names in .name
            name = func.name
        else:
            # Generate in postgres dialect to get the real PostgreSQL function name
            generated = func.sql(dialect="postgres")
            if "(" in generated:
                name = generated.split("(")[0].strip()
            else:
                name = func.sql_name() if hasattr(func, "sql_name") else type(func).__name__.lower()
        if name:
            functions.add(name.lower())
    return sorted(functions)


def _extract_columns(stmt: exp.Expression) -> list[str]:
    """Extract column references from SELECT list."""
    columns = set()
    select = stmt.find(exp.Select)
    if select is None:
        return []

    for expr in select.expressions:
        for col in expr.find_all(exp.Column):
            col_name = col.name
            table_ref = col.table
            if table_ref:
                columns.add(f"{table_ref}.{col_name}".lower())
            else:
                columns.add(col_name.lower())
    return sorted(columns)


# ─── Reusable AST Helpers (used by column_policy and other guardrails) ───────


def is_aggregate_expression(expr: exp.Expression) -> bool:
    """Check if an expression is purely an aggregate (or alias of aggregate)."""
    if isinstance(expr, exp.Alias):
        expr = expr.this
    if isinstance(expr, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
        return True
    if isinstance(expr, exp.Anonymous):
        name = expr.name.lower() if expr.name else ""
        if name in ("count", "sum", "avg", "min", "max", "array_agg", "string_agg", "json_agg", "jsonb_agg"):
            return True
    return False


def is_pure_aggregate(stmt: exp.Expression) -> bool:
    """
    Check if ALL selected expressions are aggregate functions.

    Pure aggregate = every expression in SELECT is an aggregate (COUNT, SUM, AVG, etc.)
    with no row-level column references outside of aggregates.
    """
    select = stmt.find(exp.Select)
    if select is None:
        return False
    for expr in select.expressions:
        if not is_aggregate_expression(expr):
            return False
    return True


def is_inside_aggregate(node: exp.Expression) -> bool:
    """Check if a node is inside an aggregate function."""
    parent = node.parent
    while parent is not None:
        if isinstance(parent, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
            return True
        if isinstance(parent, exp.Select):
            break
        parent = parent.parent
    return False


def extract_select_columns(stmt: exp.Expression) -> list[str]:
    """
    Extract column references from SELECT expressions, skipping aggregate internals.

    Returns column names (possibly qualified like table.col).
    """
    columns = []
    select = stmt.find(exp.Select)
    if select is None:
        return columns

    for expr in select.expressions:
        if is_aggregate_expression(expr):
            continue
        inner = expr.this if isinstance(expr, exp.Alias) else expr
        for col in inner.find_all(exp.Column):
            if is_inside_aggregate(col):
                continue
            col_name = col.name
            table_ref = col.table
            if table_ref:
                columns.append(f"{table_ref}.{col_name}")
            else:
                columns.append(col_name)
    return columns


def extract_group_by_columns(stmt: exp.Expression) -> list[str]:
    """Extract column references from GROUP BY clause."""
    columns = []
    group = stmt.find(exp.Group)
    if group is None:
        return columns
    for expr in group.expressions:
        for col in expr.find_all(exp.Column):
            col_name = col.name
            table_ref = col.table
            if table_ref:
                columns.append(f"{table_ref}.{col_name}")
            else:
                columns.append(col_name)
    return columns


def extract_where_filter_columns(stmt: exp.Expression) -> list[str]:
    """
    Extract column names from WHERE clause that are compared to concrete values.

    Looks for: column = literal, column IN (...), column > literal, etc.
    """
    columns = []
    where = stmt.find(exp.Where)
    if where is None:
        return columns

    for comparison in where.find_all((exp.EQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.NEQ, exp.Is, exp.In, exp.Like)):
        left = comparison.left if hasattr(comparison, "left") else None
        right = comparison.right if hasattr(comparison, "right") else None

        if left and isinstance(left, exp.Column):
            if right and _is_concrete_value(right):
                columns.append(left.name)
        elif right and isinstance(right, exp.Column):
            if left and _is_concrete_value(left):
                columns.append(right.name)

    for in_expr in where.find_all(exp.In):
        col = in_expr.this
        if isinstance(col, exp.Column):
            columns.append(col.name)

    return columns


def _is_concrete_value(expr: exp.Expression) -> bool:
    """Check if an expression is a concrete value (literal, parameter, list)."""
    if isinstance(expr, exp.Literal):
        return True
    if isinstance(expr, exp.Parameter):
        return True
    if isinstance(expr, exp.Placeholder):
        return True
    if isinstance(expr, exp.Neg) and isinstance(expr.this, exp.Literal):
        return True
    if isinstance(expr, exp.Tuple):
        return True
    return False


def resolve_table_alias(
    alias_or_name: str, stmt: exp.Expression, default_schema: str
) -> Optional[str]:
    """Resolve a table alias or name to the normalized schema.table form."""
    alias_lower = alias_or_name.lower()

    for table in stmt.find_all(exp.Table):
        table_alias = table.alias
        table_name = table.name

        if table_alias and table_alias.lower() == alias_lower:
            db = table.db
            if db:
                return f"{db}.{table_name}".lower()
            return f"{default_schema}.{table_name}".lower()

        if table_name and table_name.lower() == alias_lower:
            db = table.db
            if db:
                return f"{db}.{table_name}".lower()
            return f"{default_schema}.{table_name}".lower()

    return None


def has_tautological_where(stmt: exp.Expression) -> bool:
    """
    Detect trivial tautological WHERE clauses that bypass filter intent.

    Detects:
    - WHERE 1=1, WHERE '1'='1', WHERE 'a'='a' (literal = same literal)
    - WHERE true, WHERE TRUE (bare boolean)
    - WHERE id = id (column self-reference)
    - WHERE NOT false

    Not a security boundary — catches common LLM mistakes.
    """
    where = stmt.find(exp.Where)
    if where is None:
        return False

    # Check top-level WHERE expression
    condition = where.this
    return _is_tautology(condition)


def _is_tautology(expr: exp.Expression) -> bool:
    """Check if an expression is always true (tautology)."""
    # WHERE true / WHERE TRUE
    if isinstance(expr, exp.Boolean) and expr.this:
        return True

    # Literal TRUE string
    if isinstance(expr, exp.Literal) and expr.this.lower() in ("true", "1"):
        return True

    # WHERE 1=1, WHERE 'a'='a', WHERE id=id
    if isinstance(expr, exp.EQ):
        left = expr.left
        right = expr.right
        # Literal = same literal
        if isinstance(left, exp.Literal) and isinstance(right, exp.Literal):
            if left.this == right.this:
                return True
        # Column = same column (self-reference)
        if isinstance(left, exp.Column) and isinstance(right, exp.Column):
            if left.name == right.name and left.table == right.table:
                return True

    # WHERE NOT false
    if isinstance(expr, exp.Not):
        inner = expr.this
        if isinstance(inner, exp.Boolean) and not inner.this:
            return True
        if isinstance(inner, exp.Literal) and inner.this.lower() in ("false", "0"):
            return True

    # AND: tautology if ALL parts are tautologies (e.g. WHERE 1=1 AND true)
    if isinstance(expr, exp.And):
        return _is_tautology(expr.left) and _is_tautology(expr.right)

    # OR: tautology if ANY part is a tautology (e.g. WHERE false OR 1=1)
    if isinstance(expr, exp.Or):
        return _is_tautology(expr.left) or _is_tautology(expr.right)

    return False
