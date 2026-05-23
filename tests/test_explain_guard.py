"""
Phase 10.10 — EXPLAIN Safety Guard tests.

Tests EXPLAIN/EXPLAIN ANALYZE blocking by security profile.
"""

import pytest

from postgresql_mcp.guardrails.explain_guard import check_explain


# ═══════════════════════════════════════════════════════════════════════════
# BLOCK_EXPLAIN_ANALYZE (default True)
# ═══════════════════════════════════════════════════════════════════════════


class TestBlockExplainAnalyze:
    """EXPLAIN ANALYZE is blocked by default."""

    def test_analyze_blocked_by_default(self):
        r = check_explain(analyze=True)
        assert r.is_blocked is True
        assert "EXPLAIN ANALYZE" in r.reason

    def test_analyze_blocked_explicit(self):
        r = check_explain(analyze=True, block_explain_analyze=True)
        assert r.is_blocked is True

    def test_analyze_allowed_when_unblocked(self):
        r = check_explain(analyze=True, block_explain_analyze=False)
        assert r.is_blocked is False

    def test_plain_explain_allowed_when_analyze_blocked(self):
        """Plain EXPLAIN should still work even if ANALYZE is blocked."""
        r = check_explain(analyze=False, block_explain_analyze=True)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# BLOCK_EXPLAIN (entire EXPLAIN blocked)
# ═══════════════════════════════════════════════════════════════════════════


class TestBlockExplain:
    """BLOCK_EXPLAIN=true blocks all EXPLAIN variants."""

    def test_plain_explain_blocked(self):
        r = check_explain(analyze=False, block_explain=True)
        assert r.is_blocked is True
        assert "EXPLAIN" in r.reason

    def test_analyze_explain_blocked(self):
        r = check_explain(analyze=True, block_explain=True)
        assert r.is_blocked is True

    def test_explain_allowed_by_default(self):
        """BLOCK_EXPLAIN defaults to False."""
        r = check_explain(analyze=False, block_explain=False)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Security profile scenarios
# ═══════════════════════════════════════════════════════════════════════════


class TestProfileScenarios:
    """Simulate behavior per security profile."""

    def test_sensitive_profile_blocks_all(self):
        """Sensitive profile: EXPLAIN blocked entirely."""
        r = check_explain(analyze=False, block_explain=True, block_explain_analyze=True)
        assert r.is_blocked is True

    def test_sensitive_profile_blocks_analyze(self):
        r = check_explain(analyze=True, block_explain=True, block_explain_analyze=True)
        assert r.is_blocked is True

    def test_text2sql_profile_allows_plain(self):
        """Text2SQL: EXPLAIN allowed, ANALYZE blocked."""
        r = check_explain(analyze=False, block_explain=False, block_explain_analyze=True)
        assert r.is_blocked is False

    def test_text2sql_profile_blocks_analyze(self):
        r = check_explain(analyze=True, block_explain=False, block_explain_analyze=True)
        assert r.is_blocked is True

    def test_general_profile_allows_plain(self):
        """General: EXPLAIN allowed, ANALYZE blocked by default."""
        r = check_explain(analyze=False, block_explain=False, block_explain_analyze=True)
        assert r.is_blocked is False

    def test_general_profile_analyze_when_allowed(self):
        """General with BLOCK_EXPLAIN_ANALYZE=false: everything allowed."""
        r = check_explain(analyze=True, block_explain=False, block_explain_analyze=False)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Config integration
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigIntegration:
    """Test effective_block_explain config property."""

    def test_sensitive_profile_effective(self):
        from postgresql_mcp.configs import ServerConfigs, SecurityProfile

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="sensitive",
            COLUMN_POLICY='{"users": {"allowed_columns": ["id"]}}',
        )
        assert configs.effective_block_explain is True

    def test_text2sql_profile_effective(self):
        from postgresql_mcp.configs import ServerConfigs, SecurityProfile

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="text2sql",
        )
        assert configs.effective_block_explain is False

    def test_general_profile_effective(self):
        from postgresql_mcp.configs import ServerConfigs, SecurityProfile

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="general",
        )
        assert configs.effective_block_explain is False

    def test_explicit_override(self):
        from postgresql_mcp.configs import ServerConfigs

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="general",
            BLOCK_EXPLAIN=True,
        )
        assert configs.effective_block_explain is True

    def test_sensitive_override_false(self):
        """Can explicitly allow EXPLAIN even in sensitive mode."""
        from postgresql_mcp.configs import ServerConfigs

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="sensitive",
            BLOCK_EXPLAIN=False,
            COLUMN_POLICY='{"users": {"allowed_columns": ["id"]}}',
        )
        assert configs.effective_block_explain is False
