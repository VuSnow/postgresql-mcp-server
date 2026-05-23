"""
Phase 10.17 — Critical Pattern Blocking (defense-in-depth).

Fast regex pre-check that catches dangerous patterns BEFORE AST parsing.
This layer defends against:
- Parse-error bypass (sqlglot fails → pattern slips through)
- Encoding/obfuscation tricks (dollar-quoting, hex escapes, Unicode)
- PostgreSQL-specific attack vectors not caught by function allowlist

Designed to run EARLY in the pipeline (before AST-based checks).
Overlaps intentionally with security_validator.py for defense-in-depth.
"""

import re
from typing import Optional

from postgresql_mcp.guardrails.models import GuardrailResult

# ─── Critical patterns ─────────────────────────────────────────────────────
# Each tuple: (compiled regex, human-readable reason)

_CRITICAL_PATTERNS: list[tuple[re.Pattern, str]] = [
    # ── File system access ──────────────────────────────────────────────────
    (
        re.compile(r"\bpg_read_file\b", re.IGNORECASE),
        "pg_read_file: server-side file read is blocked.",
    ),
    (
        re.compile(r"\bpg_read_binary_file\b", re.IGNORECASE),
        "pg_read_binary_file: server-side binary file read is blocked.",
    ),
    (
        re.compile(r"\bpg_write_file\b", re.IGNORECASE),
        "pg_write_file: server-side file write is blocked.",
    ),
    (
        re.compile(r"\bpg_ls_dir\b", re.IGNORECASE),
        "pg_ls_dir: server-side directory listing is blocked.",
    ),
    (
        re.compile(r"\bpg_stat_file\b", re.IGNORECASE),
        "pg_stat_file: server-side file stat is blocked.",
    ),
    # ── Large object operations ─────────────────────────────────────────────
    (
        re.compile(r"\blo_import\b", re.IGNORECASE),
        "lo_import: large object import is blocked.",
    ),
    (
        re.compile(r"\blo_export\b", re.IGNORECASE),
        "lo_export: large object export is blocked.",
    ),
    (
        re.compile(r"\blo_unlink\b", re.IGNORECASE),
        "lo_unlink: large object deletion is blocked.",
    ),
    # ── Command execution / library loading ─────────────────────────────────
    (
        re.compile(r"\bpg_execute_server_program\b", re.IGNORECASE),
        "pg_execute_server_program: OS command execution is blocked.",
    ),
    (
        re.compile(r"\bCOPY\b.+\b(TO|FROM)\b", re.IGNORECASE | re.DOTALL),
        "COPY TO/FROM: file-based data import/export is blocked.",
    ),
    # ── Backend/session manipulation ────────────────────────────────────────
    (
        re.compile(r"\bpg_terminate_backend\b", re.IGNORECASE),
        "pg_terminate_backend: backend termination is blocked.",
    ),
    (
        re.compile(r"\bpg_cancel_backend\b", re.IGNORECASE),
        "pg_cancel_backend: backend cancellation is blocked.",
    ),
    (
        re.compile(r"\bpg_reload_conf\b", re.IGNORECASE),
        "pg_reload_conf: server config reload is blocked.",
    ),
    (
        re.compile(r"\bpg_sleep\b", re.IGNORECASE),
        "pg_sleep: time-delay attacks are blocked.",
    ),
    # ── Advisory locks (DoS vector) ────────────────────────────────────────
    (
        re.compile(r"\bpg_advisory_(xact_)?lock\b", re.IGNORECASE),
        "pg_advisory_lock: advisory locks are blocked (DoS vector).",
    ),
    (
        re.compile(r"\bpg_try_advisory_(xact_)?lock\b", re.IGNORECASE),
        "pg_try_advisory_lock: advisory locks are blocked.",
    ),
    # ── Data exfiltration via XML ───────────────────────────────────────────
    (
        re.compile(r"\bdatabase_to_xml\b", re.IGNORECASE),
        "database_to_xml: bulk data exfiltration is blocked.",
    ),
    (
        re.compile(r"\bquery_to_xml\b", re.IGNORECASE),
        "query_to_xml: query-based data exfiltration is blocked.",
    ),
    (
        re.compile(r"\btable_to_xml\b", re.IGNORECASE),
        "table_to_xml: table data exfiltration is blocked.",
    ),
    (
        re.compile(r"\bschema_to_xml\b", re.IGNORECASE),
        "schema_to_xml: schema data exfiltration is blocked.",
    ),
    # ── External network access ─────────────────────────────────────────────
    (
        re.compile(r"\bdblink\b", re.IGNORECASE),
        "dblink: external database connections are blocked.",
    ),
    (
        re.compile(r"\bdblink_exec\b", re.IGNORECASE),
        "dblink_exec: external command execution is blocked.",
    ),
    # ── Sensitive catalog tables ────────────────────────────────────────────
    (
        re.compile(r"\bpg_shadow\b", re.IGNORECASE),
        "pg_shadow: access to password hashes is blocked.",
    ),
    (
        re.compile(r"\bpg_authid\b", re.IGNORECASE),
        "pg_authid: access to authentication data is blocked.",
    ),
    # ── Obfuscation / evasion patterns ──────────────────────────────────────
    (
        re.compile(r"\$\$.*\$\$", re.DOTALL),
        "Dollar-quoted strings are blocked (potential code injection).",
    ),
    (
        re.compile(r"\\x[0-9a-fA-F]{2}", re.IGNORECASE),
        "Hex escape sequences are blocked (potential obfuscation).",
    ),
    (
        re.compile(r"U&['\"]", re.IGNORECASE),
        "Unicode escape strings are blocked (potential obfuscation).",
    ),
    (
        re.compile(r"E'[^']*\\\\[^']*'", re.IGNORECASE),
        "Escape string constants with backslashes are blocked.",
    ),
]


def check_critical_patterns(
    sql: str,
    enabled: bool = True,
) -> GuardrailResult:
    """
    Scan raw SQL for critical dangerous patterns via regex.

    This is a defense-in-depth layer that runs on the RAW query text
    (before any AST parsing) to catch patterns that might bypass
    sqlglot parsing.

    Args:
        sql: Raw SQL query (not comment-stripped — patterns in comments
             are also suspicious and worth blocking).
        enabled: Master switch. When False, always passes.

    Returns:
        GuardrailResult — blocked if any critical pattern matches.
    """
    if not enabled:
        return GuardrailResult(is_blocked=False)

    for pattern, reason in _CRITICAL_PATTERNS:
        if pattern.search(sql):
            return GuardrailResult(is_blocked=True, reason=reason)

    return GuardrailResult(is_blocked=False)
