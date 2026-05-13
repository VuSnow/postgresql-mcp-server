from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class ServerConfigs(BaseSettings):
    """Configuration for the PostgreSQL MCP Server."""

    connection_string: str = Field(
        ...,
        alias="POSTGRESQL_CONNECTION_STRING",
        description="PostgreSQL connection URI, e.g. postgresql://user:pass@host:5432/dbname",
    )

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

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


configs = ServerConfigs()
