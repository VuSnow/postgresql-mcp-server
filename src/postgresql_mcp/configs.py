from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class SecurityProfile(str, Enum):
    """Security profile determines default strictness of guardrails."""

    GENERAL = "general"
    TEXT2SQL = "text2sql"
    SENSITIVE = "sensitive"


class ServerConfigs(BaseSettings):
    """Configuration for the PostgreSQL MCP Server."""

    connection_string: str = Field(
        ...,
        alias="POSTGRESQL_CONNECTION_STRING",
        description="PostgreSQL connection URI, e.g. postgresql://user:pass@host:5432/dbname",
    )

    # ─── Security Profile ────────────────────────────────────────────────────

    security_profile: SecurityProfile = Field(
        SecurityProfile.GENERAL,
        alias="SECURITY_PROFILE",
        description=(
            "Security mode: 'general' (permissive, backward compatible), "
            "'text2sql' (strict column policy, metadata filtering), "
            "'sensitive' (strict + require policy file + all guards on)."
        ),
    )

    # ─── Write Policy ────────────────────────────────────────────────────────

    read_only: bool = Field(
        True,
        alias="READ_ONLY",
        description="When enabled, only read and metadata operations are allowed.",
    )

    allow_destructive: bool = Field(
        False,
        alias="ALLOW_DESTRUCTIVE",
        description=(
            "When enabled (and READ_ONLY=false), allows destructive operations "
            "such as delete, truncate_table. "
            "Default: false — only safe writes (insert, update) are allowed."
        ),
    )

    write_allowlist: Optional[str] = Field(
        None,
        alias="WRITE_ALLOWLIST",
        description=(
            "Comma-separated list of schema.table patterns allowed for write operations. "
            "Patterns: 'public.users' (exact), 'public.*' (all tables in schema), '*' (allow all). "
            "Empty or unset = allow all (when READ_ONLY=false)."
        ),
    )

    enable_write_tools: bool = Field(
        False,
        alias="ENABLE_WRITE_TOOLS",
        description=(
            "When false, write tools (insert/update/delete/truncate) are not registered "
            "with MCP — they don't appear in tool list at all."
        ),
    )

    # ─── Query Guardrails ────────────────────────────────────────────────────

    default_limit: int = Field(
        100,
        alias="DEFAULT_LIMIT",
        description="Default LIMIT injected into queries without one.",
    )

    max_limit: int = Field(
        1000,
        alias="MAX_LIMIT",
        description="Maximum allowed LIMIT value.",
    )

    max_query_length: int = Field(
        10000,
        alias="MAX_QUERY_LENGTH",
        description="Maximum SQL query length in characters.",
    )

    query_timeout_seconds: int = Field(
        300,
        alias="QUERY_TIMEOUT_SECONDS",
        description="Max execution time per query in seconds.",
    )

    rate_limit_max_calls: int = Field(
        100,
        alias="RATE_LIMIT_MAX_CALLS",
        description="Max queries allowed per rate limit window.",
    )

    rate_limit_window_seconds: int = Field(
        3600,
        alias="RATE_LIMIT_WINDOW_SECONDS",
        description="Rate limit sliding window in seconds.",
    )

    pii_rules: Optional[str] = Field(
        None,
        alias="PII_RULES",
        description=(
            'JSON array of PII masking rules. '
            'Example: [{"column":"email","method":"hash"},{"column":"ssn","method":"redact"}]'
        ),
    )

    log_level: str = Field(
        "INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )

    # ─── Phase 10: SQL Security Hardening ────────────────────────────────────

    block_select_star: bool = Field(
        True,
        alias="BLOCK_SELECT_STAR",
        description="Reject SELECT * — force agent to list columns explicitly.",
    )

    block_subqueries: bool = Field(
        True,
        alias="BLOCK_SUBQUERIES",
        description="Reject subqueries in SELECT/FROM/WHERE/HAVING.",
    )

    allow_cte: bool = Field(
        False,
        alias="ALLOW_CTE",
        description="Allow CTE (WITH) queries. Ignored until CTE body validation is implemented.",
    )

    allow_set_operations: bool = Field(
        False,
        alias="ALLOW_SET_OPERATIONS",
        description="Allow UNION/INTERSECT/EXCEPT. Same safety interlock as CTE.",
    )

    allow_recursive_cte: bool = Field(
        False,
        alias="ALLOW_RECURSIVE_CTE",
        description="Allow recursive CTE. Requires ALLOW_CTE=true.",
    )

    column_policy: Optional[str] = Field(
        None,
        alias="COLUMN_POLICY",
        description="JSON: per-table column/filter/limit policy with sampleable_columns.",
    )

    column_policy_file: Optional[str] = Field(
        None,
        alias="COLUMN_POLICY_FILE",
        description="Path to policy JSON file (takes priority over COLUMN_POLICY).",
    )

    column_policy_mode: Optional[str] = Field(
        None,
        alias="COLUMN_POLICY_MODE",
        description=(
            "'permissive': unlisted tables allowed. 'strict': unlisted tables rejected. "
            "If unset, derived from SECURITY_PROFILE."
        ),
    )

    allowed_functions: Optional[str] = Field(
        None,
        alias="ALLOWED_FUNCTIONS",
        description="JSON array of allowed SQL functions (allowlist mode).",
    )

    max_offset: int = Field(
        10000,
        alias="MAX_OFFSET",
        description="Maximum allowed OFFSET value.",
    )

    max_result_rows: int = Field(
        100,
        alias="MAX_RESULT_ROWS",
        description="Hard cap on rows returned (post-execute fallback).",
    )

    max_result_bytes: int = Field(
        1048576,
        alias="MAX_RESULT_BYTES",
        description="Max total serialized result size in bytes (1MB default).",
    )

    max_cell_length: int = Field(
        4096,
        alias="MAX_CELL_LENGTH",
        description="Truncate individual cell values exceeding this length.",
    )

    max_columns_returned: int = Field(
        50,
        alias="MAX_COLUMNS_RETURNED",
        description="Reject query if SELECT has too many columns.",
    )

    default_schema: str = Field(
        "public",
        alias="DEFAULT_SCHEMA",
        description="Default schema for unqualified table names in policy lookup.",
    )

    user_context_variable: Optional[str] = Field(
        None,
        alias="USER_CONTEXT_VARIABLE",
        description="PostgreSQL variable for RLS context (e.g. 'app.current_user_id').",
    )

    # ─── Resolved Properties ─────────────────────────────────────────────────

    @property
    def effective_column_policy_mode(self) -> str:
        """Resolve column policy mode from explicit config or security profile."""
        if self.column_policy_mode is not None:
            return self.column_policy_mode
        if self.security_profile in (SecurityProfile.TEXT2SQL, SecurityProfile.SENSITIVE):
            return "strict"
        return "permissive"

    @property
    def effective_metadata_filtering(self) -> bool:
        """Whether metadata tools should filter results by policy."""
        return self.security_profile in (SecurityProfile.TEXT2SQL, SecurityProfile.SENSITIVE)

    @property
    def effective_function_control(self) -> str:
        """Function control mode: 'allowlist' or 'blacklist'."""
        if self.allowed_functions is not None:
            return "allowlist"
        if self.security_profile in (SecurityProfile.TEXT2SQL, SecurityProfile.SENSITIVE):
            return "allowlist"
        return "blacklist"

    @model_validator(mode="after")
    def _validate_security_profile(self) -> "ServerConfigs":
        """Enforce constraints for sensitive profile."""
        if self.security_profile == SecurityProfile.SENSITIVE:
            if not self.column_policy and not self.column_policy_file:
                raise ValueError(
                    "SECURITY_PROFILE=sensitive requires COLUMN_POLICY or COLUMN_POLICY_FILE to be set."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


configs = ServerConfigs()
