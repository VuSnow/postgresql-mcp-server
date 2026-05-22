"""Tests for PIIMasker — hash, redact, column matching."""

import pytest
from postgresql_mcp.guardrails.pii_masker import (
    PIIMasker,
    PIIRule,
    parse_pii_rules,
    REDACTED_VALUE,
    HASH_LENGTH,
)


class TestParseRules:
    def test_parse_valid_json(self):
        rules = parse_pii_rules('[{"column":"email","method":"hash"},{"column":"ssn","method":"redact"}]')
        assert len(rules) == 2
        assert rules[0].column == "email"
        assert rules[0].method == "hash"
        assert rules[1].column == "ssn"
        assert rules[1].method == "redact"

    def test_parse_none(self):
        assert parse_pii_rules(None) == []

    def test_parse_empty_string(self):
        assert parse_pii_rules("") == []

    def test_parse_invalid_json(self):
        assert parse_pii_rules("not json") == []

    def test_parse_skips_invalid_rules(self):
        rules = parse_pii_rules('[{"column":"email","method":"hash"},{"bad":"rule"}]')
        assert len(rules) == 1

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Invalid PII method"):
            PIIRule(column="x", method="encrypt")


class TestMaskingHash:
    @pytest.fixture
    def masker(self):
        return PIIMasker(rules=[PIIRule(column="email", method="hash")])

    def test_hashes_email_column(self, masker):
        rows = [{"id": 1, "email": "user@example.com", "name": "Alice"}]
        result = masker.mask_rows(rows, ["id", "email", "name"])
        assert result[0]["email"] != "user@example.com"
        assert len(result[0]["email"]) == HASH_LENGTH
        assert result[0]["name"] == "Alice"  # untouched

    def test_hash_is_deterministic(self, masker):
        rows1 = [{"email": "test@test.com"}]
        rows2 = [{"email": "test@test.com"}]
        r1 = masker.mask_rows(rows1, ["email"])
        r2 = masker.mask_rows(rows2, ["email"])
        assert r1[0]["email"] == r2[0]["email"]

    def test_different_values_different_hashes(self, masker):
        rows = [{"email": "a@b.com"}, {"email": "x@y.com"}]
        result = masker.mask_rows(rows, ["email"])
        assert result[0]["email"] != result[1]["email"]


class TestMaskingRedact:
    @pytest.fixture
    def masker(self):
        return PIIMasker(rules=[PIIRule(column="ssn", method="redact")])

    def test_redacts_column(self, masker):
        rows = [{"id": 1, "ssn": "123-45-6789"}]
        result = masker.mask_rows(rows, ["id", "ssn"])
        assert result[0]["ssn"] == REDACTED_VALUE
        assert result[0]["id"] == 1

    def test_null_values_not_masked(self, masker):
        rows = [{"ssn": None}]
        result = masker.mask_rows(rows, ["ssn"])
        assert result[0]["ssn"] is None


class TestCaseInsensitivity:
    def test_column_match_case_insensitive(self):
        masker = PIIMasker(rules=[PIIRule(column="Email", method="redact")])
        rows = [{"EMAIL": "test@x.com"}]
        # Column names in result are "EMAIL" but rule is "Email"
        result = masker.mask_rows(rows, ["EMAIL"])
        assert result[0]["EMAIL"] == REDACTED_VALUE


class TestNoRules:
    def test_no_rules_returns_unchanged(self):
        masker = PIIMasker(rules=[])
        rows = [{"email": "test@x.com", "ssn": "123"}]
        result = masker.mask_rows(rows, ["email", "ssn"])
        assert result == rows

    def test_has_rules_property(self):
        assert PIIMasker(rules=[]).has_rules is False
        assert PIIMasker(rules=[PIIRule(column="x", method="hash")]).has_rules is True


class TestDoesNotMutateInput:
    def test_original_rows_unchanged(self):
        masker = PIIMasker(rules=[PIIRule(column="email", method="redact")])
        original = [{"email": "secret@x.com"}]
        masker.mask_rows(original, ["email"])
        assert original[0]["email"] == "secret@x.com"


class TestEmptyInput:
    def test_empty_rows(self):
        masker = PIIMasker(rules=[PIIRule(column="email", method="hash")])
        assert masker.mask_rows([], ["email"]) == []

    def test_no_matching_columns(self):
        masker = PIIMasker(rules=[PIIRule(column="email", method="hash")])
        rows = [{"name": "Alice"}]
        result = masker.mask_rows(rows, ["name"])
        assert result == rows
