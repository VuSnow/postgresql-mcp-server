"""
SecurityValidator — blocks dangerous SQL before execution.

Checks:
- Forbidden keywords (DDL, DCL, destructive DML)
- SQL injection patterns
- Dangerous functions (pg_sleep, lo_export, etc.)
- Query length limit
- Comment stripping for analysis
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ─── Forbidden keyword sets ────────────────────────────────────────────────

# DDL keywords that should never appear in read queries
DDL_KEYWORDS = frozenset([
    "CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME",
    "COMMENT", "REINDEX",
])

# DCL keywords — privilege manipulation
DCL_KEYWORDS = frozenset([
    "GRANT", "REVOKE", "REASSIGN",
])

# Destructive DML — blocked in read-only mode
DESTRUCTIVE_DML = frozenset([
    "INSERT", "UPDATE", "DELETE", "MERGE",
])

# Transaction/session control
SESSION_KEYWORDS = frozenset([
    "SET", "RESET", "DISCARD", "LOAD",
    "COPY", "VACUUM", "ANALYZE", "CLUSTER",
    "LISTEN", "NOTIFY", "UNLISTEN",
])

# All forbidden keywords for read-only mode
ALL_FORBIDDEN_READONLY = DDL_KEYWORDS | DCL_KEYWORDS | DESTRUCTIVE_DML | SESSION_KEYWORDS

# ─── Dangerous functions ───────────────────────────────────────────────────

DANGEROUS_FUNCTIONS = frozenset([
    "pg_sleep",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_reload_conf",
    "pg_rotate_logfile",
    "lo_import",
    "lo_export",
    "lo_unlink",
    "dblink",
    "dblink_exec",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_write_file",
    "pg_ls_dir",
    "pg_stat_file",
    "inet_server_addr",
    "inet_server_port",
])

# ─── Injection patterns ───────────────────────────────────────────────────

INJECTION_PATTERNS = [
    re.compile(r";\s*(DROP|ALTER|CREATE|INSERT|UPDATE|DELETE|GRANT|TRUNCATE)", re.IGNORECASE),
    re.compile(r"UNION\s+(ALL\s+)?SELECT", re.IGNORECASE),
    re.compile(r"INTO\s+(OUT|DUMP)FILE", re.IGNORECASE),
    re.compile(r"EXEC(\s|\(|UTE)", re.IGNORECASE),
    re.compile(r"xp_cmdshell", re.IGNORECASE),
    re.compile(r"0x[0-9a-fA-F]{8,}"),  # long hex literals (shellcode)
]

# ─── Comment stripping ─────────────────────────────────────────────────────

_LINE_COMMENT_RE = re.compile(r"--[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def strip_comments(sql: str) -> str:
    """Remove SQL comments for security analysis."""
    sql = _BLOCK_COMMENT_RE.sub(" ", sql)
    sql = _LINE_COMMENT_RE.sub(" ", sql)
    return sql


def _extract_first_keyword(sql: str) -> str | None:
    """Extract the first SQL keyword from a normalized query."""
    stripped = strip_comments(sql).strip()
    match = re.match(r"[A-Za-z_]+", stripped)
    return match.group(0).upper() if match else None


@dataclass
class ValidationResult:
    """Result of security validation."""
    is_valid: bool
    reason: str | None = None


class SecurityValidator:
    """Validates SQL queries against security rules."""

    def __init__(
        self,
        max_query_length: int = 10000,
        read_only: bool = True,
        allow_destructive: bool = False,
    ):
        self._max_query_length = max_query_length
        self._read_only = read_only
        self._allow_destructive = allow_destructive

    def validate(self, query: str) -> ValidationResult:
        """
        Run all security checks on a query.
        Returns ValidationResult with is_valid=False and reason if blocked.
        """
        # 1. Query length
        if len(query) > self._max_query_length:
            return ValidationResult(
                is_valid=False,
                reason=f"Query exceeds maximum length ({len(query)} > {self._max_query_length})",
            )

        # 2. Strip comments for analysis
        normalized = strip_comments(query)

        # 3. Check forbidden keywords
        keyword_result = self._check_forbidden_keywords(normalized)
        if not keyword_result.is_valid:
            return keyword_result

        # 4. Check dangerous functions
        func_result = self._check_dangerous_functions(normalized)
        if not func_result.is_valid:
            return func_result

        # 5. Check injection patterns
        injection_result = self._check_injection_patterns(normalized)
        if not injection_result.is_valid:
            return injection_result

        return ValidationResult(is_valid=True)

    def _check_forbidden_keywords(self, normalized_sql: str) -> ValidationResult:
        """Check for forbidden SQL keywords based on mode."""
        first_kw = _extract_first_keyword(normalized_sql)
        if not first_kw:
            return ValidationResult(is_valid=True)

        if self._read_only:
            # In read-only mode, block everything except SELECT, EXPLAIN, WITH, SHOW
            allowed = {"SELECT", "EXPLAIN", "WITH", "SHOW", "TABLE"}
            if first_kw in ALL_FORBIDDEN_READONLY:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Forbidden keyword '{first_kw}' in read-only mode.",
                )
            # Also check if it's not in our allowed set (catch unknown statements)
            if first_kw not in allowed and first_kw in ALL_FORBIDDEN_READONLY:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Statement type '{first_kw}' is not allowed in read-only mode.",
                )
        else:
            # In write mode, still block DDL and DCL
            if first_kw in DDL_KEYWORDS:
                return ValidationResult(
                    is_valid=False,
                    reason=f"DDL statement '{first_kw}' is not allowed.",
                )
            if first_kw in DCL_KEYWORDS:
                return ValidationResult(
                    is_valid=False,
                    reason=f"DCL statement '{first_kw}' is not allowed.",
                )
            # Block destructive DML unless allowed
            if first_kw in DESTRUCTIVE_DML and not self._allow_destructive:
                if first_kw in ("DELETE", "TRUNCATE"):
                    return ValidationResult(
                        is_valid=False,
                        reason=f"Destructive operation '{first_kw}' requires ALLOW_DESTRUCTIVE=true.",
                    )

        return ValidationResult(is_valid=True)

    def _check_dangerous_functions(self, normalized_sql: str) -> ValidationResult:
        """Check for dangerous PostgreSQL functions."""
        sql_lower = normalized_sql.lower()
        for func in DANGEROUS_FUNCTIONS:
            # Match function call pattern: func_name followed by (
            pattern = re.compile(rf"\b{re.escape(func)}\s*\(", re.IGNORECASE)
            if pattern.search(sql_lower):
                return ValidationResult(
                    is_valid=False,
                    reason=f"Dangerous function '{func}' is not allowed.",
                )
        return ValidationResult(is_valid=True)

    def _check_injection_patterns(self, normalized_sql: str) -> ValidationResult:
        """Check for common SQL injection patterns."""
        for pattern in INJECTION_PATTERNS:
            if pattern.search(normalized_sql):
                return ValidationResult(
                    is_valid=False,
                    reason=f"Potential SQL injection detected (pattern: {pattern.pattern}).",
                )
        return ValidationResult(is_valid=True)
