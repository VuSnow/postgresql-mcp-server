"""Tests for AuditLogger — structured logging."""

import pytest
from postgresql_mcp.guardrails.audit_logger import AuditLogger, AuditEntry


class TestLogExecution:
    def test_logs_successful_execution(self):
        al = AuditLogger()
        al.log_execution("SELECT 1", duration_ms=5.2, rows_returned=1)
        assert len(al.entries) == 1
        entry = al.entries[0]
        assert entry.query == "SELECT 1"
        assert entry.duration_ms == 5.2
        assert entry.rows_returned == 1
        assert entry.blocked is False

    def test_multiple_entries(self):
        al = AuditLogger()
        al.log_execution("q1", 1.0, 10)
        al.log_execution("q2", 2.0, 20)
        assert len(al.entries) == 2


class TestLogBlocked:
    def test_logs_blocked_query(self):
        al = AuditLogger()
        al.log_blocked("DROP TABLE x", "DDL not allowed")
        entry = al.entries[0]
        assert entry.blocked is True
        assert entry.blocked_reason == "DDL not allowed"
        assert entry.duration_ms is None


class TestLogError:
    def test_logs_error(self):
        al = AuditLogger()
        al.log_error("bad query", "syntax error", duration_ms=1.5)
        entry = al.entries[0]
        assert entry.error == "syntax error"
        assert entry.duration_ms == 1.5


class TestAuditEntryToDict:
    def test_to_dict_execution(self):
        entry = AuditEntry(query="SELECT 1", duration_ms=3.14, rows_returned=5)
        d = entry.to_dict()
        assert d["query"] == "SELECT 1"
        assert d["duration_ms"] == 3.14
        assert d["rows_returned"] == 5
        assert d["blocked"] is False
        assert "blocked_reason" not in d
        assert "error" not in d

    def test_to_dict_blocked(self):
        entry = AuditEntry(query="DROP TABLE x", blocked=True, blocked_reason="forbidden")
        d = entry.to_dict()
        assert d["blocked"] is True
        assert d["blocked_reason"] == "forbidden"

    def test_query_truncated(self):
        long_query = "SELECT " + "x" * 1000
        entry = AuditEntry(query=long_query)
        d = entry.to_dict()
        assert len(d["query"]) == 500


class TestClear:
    def test_clear_removes_all(self):
        al = AuditLogger()
        al.log_execution("q1", 1.0, 1)
        al.log_blocked("q2", "reason")
        al.clear()
        assert len(al.entries) == 0
