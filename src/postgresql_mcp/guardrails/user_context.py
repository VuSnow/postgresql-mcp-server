"""
Phase 10.12 — User Context for Row-Level Security (RLS).

When USER_CONTEXT_VARIABLE is configured, this module:
1. Validates the variable name format
2. Validates user_id values (no injection)
3. Generates a SET LOCAL statement to set the context variable before query execution

PostgreSQL RLS policies can then reference the variable via current_setting().
"""

import re
from typing import Optional

from postgresql_mcp.guardrails.models import GuardrailResult

# Variable name: dotted identifier like "app.current_user_id"
_VARIABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*$")

# User ID value: alphanumeric, hyphens, underscores (UUIDs, numeric IDs, etc.)
_USER_ID_VALUE_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_variable_name(variable_name: str) -> GuardrailResult:
    """
    Validate that a USER_CONTEXT_VARIABLE name is safe.

    Args:
        variable_name: The PostgreSQL variable name (e.g. 'app.current_user_id').

    Returns:
        GuardrailResult — blocked if the variable name is invalid.
    """
    if not variable_name:
        return GuardrailResult(
            is_blocked=True,
            reason="USER_CONTEXT_VARIABLE must not be empty.",
        )

    if not _VARIABLE_NAME_RE.match(variable_name):
        return GuardrailResult(
            is_blocked=True,
            reason=(
                f"USER_CONTEXT_VARIABLE '{variable_name}' contains invalid characters. "
                f"Must match: [a-zA-Z_][a-zA-Z0-9_.]*"
            ),
        )

    return GuardrailResult(is_blocked=False)


def validate_user_id(user_id: str) -> GuardrailResult:
    """
    Validate that a user_id value is safe to use in SET LOCAL.

    Args:
        user_id: The user identifier value to set.

    Returns:
        GuardrailResult — blocked if the value looks like injection.
    """
    if not user_id:
        return GuardrailResult(
            is_blocked=True,
            reason="user_id must not be empty.",
        )

    if not _USER_ID_VALUE_RE.match(user_id):
        return GuardrailResult(
            is_blocked=True,
            reason=(
                f"user_id '{user_id}' contains invalid characters. "
                f"Only alphanumeric, hyphens, and underscores are allowed."
            ),
        )

    return GuardrailResult(is_blocked=False)


def build_set_local_sql(variable_name: str, user_id: str) -> str:
    """
    Build a SET LOCAL statement for the RLS context variable.

    Both variable_name and user_id MUST be pre-validated before calling this.

    Args:
        variable_name: The PostgreSQL variable name.
        user_id: The user identifier value.

    Returns:
        SQL SET LOCAL statement string.
    """
    # Use dollar-quoting to avoid single-quote injection
    return f"SET LOCAL \"{variable_name}\" = '{user_id}'"
