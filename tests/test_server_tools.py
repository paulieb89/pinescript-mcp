"""Tests for explain_pine_error tool — verifying the deterministic common_errors.md fallback.

The contract: common_errors.md is ALWAYS included in the output, regardless of whether
AI_READY_BASE_URL is configured and regardless of what semantic search returns.
This protects against regressions where the bundled block is accidentally moved
inside a conditional branch.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pinescript_mcp.server import explain_pine_error
from pinescript_mcp.ai_ready import AiReadyResult, AiReadyError


def _make_result(text: str, path: str = "reference/types.md", title: str = "Types") -> AiReadyResult:
    return AiReadyResult(text=text, score=0.9, title=title, path=path)


def _configured_settings():
    s = MagicMock()
    s.configured = True
    return s


def _unconfigured_settings():
    s = MagicMock()
    s.configured = False
    return s


def _mock_client(results: list[AiReadyResult]) -> MagicMock:
    client = MagicMock()
    client.search = AsyncMock(return_value=results)
    return client


# ---------------------------------------------------------------------------
# Deterministic fallback — common_errors.md always present
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestExplainPineErrorFallback:
    async def test_common_errors_included_when_semantic_returns_other_results(self):
        """AI_READY configured + search returns results NOT from common_errors.md → still included."""
        results = [_make_result("Pine Script uses series types.", path="reference/types.md")]

        with patch("pinescript_mcp.ai_ready.get_settings", return_value=_configured_settings()), \
             patch("pinescript_mcp.ai_ready.get_client", return_value=_mock_client(results)):
            output = await explain_pine_error("compile error: mismatched input ')'")

        assert "## Bundled common errors reference" in output
        # Known text from concepts/common_errors.md
        assert "if statement is too long" in output.lower() or "error messages" in output.lower()

    async def test_common_errors_included_when_semantic_returns_empty(self):
        """AI_READY configured + search returns no results → bundled block still present."""
        with patch("pinescript_mcp.ai_ready.get_settings", return_value=_configured_settings()), \
             patch("pinescript_mcp.ai_ready.get_client", return_value=_mock_client([])):
            output = await explain_pine_error("undeclared identifier 'close2'")

        assert "## Bundled common errors reference" in output
        assert "if statement is too long" in output.lower() or "error messages" in output.lower()

    async def test_common_errors_included_when_not_configured(self):
        """AI_READY_BASE_URL not set → semantic search skipped but bundled block still present."""
        with patch("pinescript_mcp.ai_ready.get_settings", return_value=_unconfigured_settings()):
            output = await explain_pine_error("type error: cannot use 'float' where 'series int' expected")

        assert "## Bundled common errors reference" in output
        assert "if statement is too long" in output.lower() or "error messages" in output.lower()

    async def test_common_errors_included_when_semantic_raises(self):
        """Semantic search fails with AiReadyError → bundled block still present."""
        client = MagicMock()
        client.search = AsyncMock(side_effect=AiReadyError("timeout", retryable=True))

        with patch("pinescript_mcp.ai_ready.get_settings", return_value=_configured_settings()), \
             patch("pinescript_mcp.ai_ready.get_client", return_value=client):
            output = await explain_pine_error("runtime error: array index out of bounds")

        assert "## Bundled common errors reference" in output
        assert "if statement is too long" in output.lower() or "error messages" in output.lower()

    async def test_error_text_always_echoed(self):
        """The submitted error text is always included verbatim in the output."""
        error = "Cannot call `ta.sma()` with argument 'length'=series float"

        with patch("pinescript_mcp.ai_ready.get_settings", return_value=_unconfigured_settings()):
            output = await explain_pine_error(error)

        assert error in output

    async def test_code_section_included_when_provided(self):
        """Optional code block is included when the caller supplies it."""
        with patch("pinescript_mcp.ai_ready.get_settings", return_value=_unconfigured_settings()):
            output = await explain_pine_error(
                "type error",
                code="//@version=6\nplot(close)"
            )

        assert "## Code submitted" in output
        assert "plot(close)" in output
