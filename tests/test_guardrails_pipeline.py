"""Tests for GuardrailsPipeline — end-to-end orchestration."""

import pytest
from postgresql_mcp.guardrails import GuardrailsPipeline, create_pipeline


@pytest.fixture
def pipeline():
    return create_pipeline(
        max_calls=10,
        window_seconds=3600,
        max_query_length=1000,
        read_only=True,
        default_limit=100,
        max_limit=500,
        pii_rules_json='[{"column":"email","method":"hash"}]',
    )


class TestPreExecute:
    def test_valid_select_allowed(self, pipeline):
        result = pipeline.pre_execute("SELECT * FROM users")
        assert result.allowed is True
        assert "LIMIT 100" in result.rewritten_query

    def test_blocked_by_security(self, pipeline):
        result = pipeline.pre_execute("DROP TABLE users")
        assert result.allowed is False
        assert "Forbidden keyword" in result.blocked_reason

    def test_blocked_by_rate_limit(self):
        p = create_pipeline(max_calls=2, window_seconds=3600, read_only=True)
        # Use up quota via post_execute recording
        p.pre_execute("SELECT 1")
        p.post_execute("SELECT 1", [{"x": 1}], ["x"], 1.0)
        p.pre_execute("SELECT 2")
        p.post_execute("SELECT 2", [{"x": 2}], ["x"], 1.0)

        result = p.pre_execute("SELECT 3")
        assert result.allowed is False
        assert "Rate limit" in result.blocked_reason

    def test_query_rewritten_with_limit(self, pipeline):
        result = pipeline.pre_execute("SELECT * FROM users WHERE id = 1")
        assert result.allowed is True
        assert "LIMIT 100" in result.rewritten_query

    def test_existing_limit_preserved(self, pipeline):
        result = pipeline.pre_execute("SELECT * FROM users LIMIT 50")
        assert result.allowed is True
        assert "LIMIT 50" in result.rewritten_query

    def test_excessive_limit_capped(self, pipeline):
        result = pipeline.pre_execute("SELECT * FROM users LIMIT 9999")
        assert result.allowed is True
        assert "LIMIT 500" in result.rewritten_query


class TestPostExecute:
    def test_masks_pii_columns(self, pipeline):
        rows = [{"id": 1, "email": "user@example.com"}]
        result = pipeline.post_execute("SELECT *", rows, ["id", "email"], 5.0)
        assert result.rows[0]["email"] != "user@example.com"
        assert result.rows[0]["id"] == 1

    def test_records_audit(self, pipeline):
        pipeline.post_execute("SELECT 1", [{"x": 1}], ["x"], 2.5)
        entries = pipeline.audit_logger.entries
        assert len(entries) == 1
        assert entries[0].rows_returned == 1
        assert entries[0].duration_ms == 2.5

    def test_returns_duration(self, pipeline):
        result = pipeline.post_execute("q", [], [], 10.5)
        assert result.duration_ms == 10.5


class TestLogError:
    def test_logs_error(self, pipeline):
        pipeline.log_error("bad query", "timeout", duration_ms=30000.0)
        entries = pipeline.audit_logger.entries
        assert len(entries) == 1
        assert entries[0].error == "timeout"


class TestCreatePipeline:
    def test_default_factory(self):
        p = create_pipeline()
        assert p is not None
        result = p.pre_execute("SELECT 1")
        assert result.allowed is True

    def test_write_mode_factory(self):
        p = create_pipeline(read_only=False)
        result = p.pre_execute("INSERT INTO t VALUES (1)")
        assert result.allowed is True
