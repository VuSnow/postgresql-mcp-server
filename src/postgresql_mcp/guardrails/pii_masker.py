"""
PIIMasker — masks sensitive columns in query results.

Methods:
- hash: SHA-256 truncated to 12 chars (preserves uniqueness for joins)
- redact: replaces with '***REDACTED***'

Rules are configured via PII_RULES env var as JSON array:
  [{"column": "email", "method": "hash"}, {"column": "ssn", "method": "redact"}]
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

REDACTED_VALUE = "***REDACTED***"
HASH_LENGTH = 12


@dataclass
class PIIRule:
    """A single PII masking rule."""
    column: str  # case-insensitive match
    method: str  # "hash" or "redact"

    def __post_init__(self):
        self.column = self.column.lower()
        if self.method not in ("hash", "redact"):
            raise ValueError(f"Invalid PII method '{self.method}'. Must be 'hash' or 'redact'.")


def parse_pii_rules(rules_json: str | None) -> list[PIIRule]:
    """Parse PII_RULES JSON string into list of PIIRule objects."""
    if not rules_json:
        return []

    try:
        raw = json.loads(rules_json)
    except json.JSONDecodeError as e:
        logger.error(f"[pii] Failed to parse PII_RULES JSON: {e}")
        return []

    rules = []
    for item in raw:
        try:
            rules.append(PIIRule(column=item["column"], method=item["method"]))
        except (KeyError, ValueError) as e:
            logger.warning(f"[pii] Skipping invalid rule {item}: {e}")

    return rules


def _hash_value(value: Any) -> str:
    """Hash a value using SHA-256, truncated."""
    raw = str(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:HASH_LENGTH]


def _redact_value(value: Any) -> str:
    """Replace value with redaction marker."""
    return REDACTED_VALUE


class PIIMasker:
    """Masks PII columns in query result rows."""

    def __init__(self, rules: list[PIIRule] | None = None):
        self._rules = rules or []
        # Build lookup: lowercase column name → masking function
        self._column_mask: dict[str, callable] = {}
        for rule in self._rules:
            if rule.method == "hash":
                self._column_mask[rule.column] = _hash_value
            else:
                self._column_mask[rule.column] = _redact_value

    @property
    def has_rules(self) -> bool:
        return len(self._column_mask) > 0

    def mask_rows(
        self,
        rows: list[dict[str, Any]],
        columns: list[str],
    ) -> list[dict[str, Any]]:
        """
        Apply PII masking to result rows.
        Matches column names case-insensitively.
        Returns new list (does not mutate input).
        """
        if not self._column_mask or not rows:
            return rows

        # Determine which result columns need masking
        columns_to_mask: dict[str, callable] = {}
        for col in columns:
            mask_fn = self._column_mask.get(col.lower())
            if mask_fn:
                columns_to_mask[col] = mask_fn

        if not columns_to_mask:
            return rows

        logger.debug(f"[pii] Masking columns: {list(columns_to_mask.keys())}")

        masked_rows = []
        for row in rows:
            new_row = dict(row)
            for col, mask_fn in columns_to_mask.items():
                if col in new_row and new_row[col] is not None:
                    new_row[col] = mask_fn(new_row[col])
            masked_rows.append(new_row)

        return masked_rows
