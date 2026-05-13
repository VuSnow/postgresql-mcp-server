import re

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def validate_identifier(value: str) -> str:
    """
    Validate SQL identifiers such as schema/table/column names.

    This is needed because PostgreSQL identifiers cannot be passed as
    asyncpg parameters like $1, $2.
    """
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid SQL identifier: {value}")
    return value
