"""
Tests for pinescript_mcp.ai_ready — client, settings, normalisation.

All httpx calls are mocked via respx; no live network required.
"""

import os
import pytest
import respx
import httpx

from pinescript_mcp.ai_ready import (
    AiReadyClient,
    AiReadySettings,
    AiReadyError,
    AiReadyResult,
    _normalise_result,
    _parse_response,
    get_client,
    get_settings,
)


# ---------------------------------------------------------------------------
# AiReadySettings
# ---------------------------------------------------------------------------

class TestAiReadySettings:
    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("AI_READY_BASE_URL", raising=False)
        monkeypatch.delenv("AI_READY_DATASET", raising=False)
        monkeypatch.delenv("AI_READY_TIMEOUT", raising=False)
        monkeypatch.delenv("AI_READY_TOP_K", raising=False)
        monkeypatch.delenv("AI_READY_API_KEY", raising=False)
        s = AiReadySettings()
        assert s.base_url == ""
        assert s.dataset == "pinescript-v06"
        assert s.timeout == 10.0
        assert s.top_k == 5
        assert s.api_key == ""
        assert not s.configured

    def test_configured_when_base_url_set(self, monkeypatch):
        monkeypatch.setenv("AI_READY_BASE_URL", "http://localhost:8000")
        s = AiReadySettings()
        assert s.configured
        assert s.base_url == "http://localhost:8000"

    def test_trailing_slash_stripped(self, monkeypatch):
        monkeypatch.setenv("AI_READY_BASE_URL", "http://localhost:8000/")
        s = AiReadySettings()
        assert s.base_url == "http://localhost:8000"

    def test_custom_dataset(self, monkeypatch):
        monkeypatch.setenv("AI_READY_BASE_URL", "http://x")
        monkeypatch.setenv("AI_READY_DATASET", "my-dataset")
        s = AiReadySettings()
        assert s.dataset == "my-dataset"

    def test_api_key(self, monkeypatch):
        monkeypatch.setenv("AI_READY_BASE_URL", "http://x")
        monkeypatch.setenv("AI_READY_API_KEY", "secret")
        s = AiReadySettings()
        assert s.api_key == "secret"


# ---------------------------------------------------------------------------
# _normalise_result
# ---------------------------------------------------------------------------

class TestNormaliseResult:
    def test_canonical_fields(self):
        raw = {
            "chunk_id": "abc123",
            "score": 0.95,
            "text": "Pine Script uses series types.",
            "title": "Series types",
            "path": "reference/types.md",
            "summary": "Type overview",
            "metadata": {"source": "v6"},
        }
        r = _normalise_result(raw)
        assert r.chunk_id == "abc123"
        assert r.score == pytest.approx(0.95)
        assert r.text == "Pine Script uses series types."
        assert r.title == "Series types"
        assert r.path == "reference/types.md"
        assert r.summary == "Type overview"

    def test_alternate_field_names(self):
        raw = {
            "id": "xyz",
            "relevance_score": 0.7,
            "content": "Some content here.",
            "section": "Usage",
            "doc_path": "concepts/execution_model.md",
        }
        r = _normalise_result(raw)
        assert r.chunk_id == "xyz"
        assert r.score == pytest.approx(0.7)
        assert r.text == "Some content here."
        assert r.title == "Usage"
        assert r.path == "concepts/execution_model.md"

    def test_bare_list_field_names(self):
        raw = {
            "similarity": 0.5,
            "chunk": "chunk content",
            "header": "My header",
            "file": "concepts/methods.md",
        }
        r = _normalise_result(raw)
        assert r.score == pytest.approx(0.5)
        assert r.text == "chunk content"
        assert r.title == "My header"
        assert r.path == "concepts/methods.md"

    def test_unknown_fields_go_to_metadata(self):
        raw = {"text": "content", "custom_field": "value", "another": 42}
        r = _normalise_result(raw)
        assert r.metadata["custom_field"] == "value"
        assert r.metadata["another"] == 42

    def test_integer_chunk_id_coerced(self):
        raw = {"id": 7, "text": "text"}
        r = _normalise_result(raw)
        assert r.chunk_id == "7"


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_results_key(self):
        body = {"results": [{"text": "hello"}, {"text": "world"}]}
        results = _parse_response(body)
        assert len(results) == 2
        assert results[0].text == "hello"

    def test_bare_list(self):
        body = [{"text": "one"}, {"text": "two"}]
        results = _parse_response(body)
        assert len(results) == 2

    def test_hits_key(self):
        body = {"hits": [{"text": "hit one"}]}
        results = _parse_response(body)
        assert len(results) == 1

    def test_empty_results(self):
        assert _parse_response({"results": []}) == []

    def test_malformed_entries_skipped(self):
        body = {"results": [{"text": "valid"}, "not a dict", {"text": ""}]}
        results = _parse_response(body)
        # "valid" kept; "not a dict" skipped; empty text raises validation → skipped
        assert len(results) == 1
        assert results[0].text == "valid"

    def test_unknown_body_type(self):
        assert _parse_response("just a string") == []
        assert _parse_response(42) == []


# ---------------------------------------------------------------------------
# AiReadyClient — search() with mocked httpx
# ---------------------------------------------------------------------------

BASE = "http://localhost:8000"
DATASET = "pinescript-v06"


def _make_settings(**overrides):
    defaults = dict(base_url=BASE, dataset=DATASET, timeout=5.0, top_k=5, api_key="")
    defaults.update(overrides)
    s = AiReadySettings.__new__(AiReadySettings)
    s.__dict__.update(defaults)
    return s


@pytest.mark.asyncio
class TestAiReadyClientSearch:
    @respx.mock
    async def test_successful_search(self):
        route = respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"text": "repainting happens when...", "score": 0.9, "path": "concepts/timeframes.md"},
                        {"text": "use lookahead=barmerge.lookahead_off", "score": 0.8},
                    ]
                },
            )
        )
        client = AiReadyClient(_make_settings())
        results = await client.search("repainting prevention", top_k=2)
        assert route.called
        assert len(results) == 2
        assert results[0].score == pytest.approx(0.9)
        assert results[0].path == "concepts/timeframes.md"
        await client.aclose()

    @respx.mock
    async def test_bearer_token_sent_when_api_key_set(self):
        route = respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        client = AiReadyClient(_make_settings(api_key="mytoken"))
        await client.search("anything")
        assert route.calls[0].request.headers["authorization"] == "Bearer mytoken"
        await client.aclose()

    @respx.mock
    async def test_no_auth_header_without_api_key(self):
        route = respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        client = AiReadyClient(_make_settings(api_key=""))
        await client.search("anything")
        assert "authorization" not in route.calls[0].request.headers
        await client.aclose()

    @respx.mock
    async def test_uses_default_top_k(self):
        route = respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        client = AiReadyClient(_make_settings(top_k=7))
        await client.search("query")
        import json
        body = json.loads(route.calls[0].request.content)
        assert body["top_k"] == 7
        await client.aclose()

    @respx.mock
    async def test_explicit_top_k_overrides_default(self):
        route = respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        client = AiReadyClient(_make_settings(top_k=5))
        await client.search("query", top_k=3)
        import json
        body = json.loads(route.calls[0].request.content)
        assert body["top_k"] == 3
        await client.aclose()

    @respx.mock
    async def test_bare_list_response(self):
        respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(200, json=[{"text": "bare item", "score": 0.5}])
        )
        client = AiReadyClient(_make_settings())
        results = await client.search("q")
        assert len(results) == 1
        assert results[0].text == "bare item"
        await client.aclose()

    @respx.mock
    async def test_timeout_raises_retryable_error(self):
        respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        client = AiReadyClient(_make_settings())
        with pytest.raises(AiReadyError) as exc_info:
            await client.search("q")
        assert exc_info.value.retryable
        await client.aclose()

    @respx.mock
    async def test_5xx_raises_retryable_error(self):
        respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(503, text="Service Unavailable")
        )
        client = AiReadyClient(_make_settings())
        with pytest.raises(AiReadyError) as exc_info:
            await client.search("q")
        assert exc_info.value.retryable
        await client.aclose()

    @respx.mock
    async def test_4xx_raises_non_retryable_error(self):
        respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(400, text="Bad Request")
        )
        client = AiReadyClient(_make_settings())
        with pytest.raises(AiReadyError) as exc_info:
            await client.search("q")
        assert not exc_info.value.retryable
        await client.aclose()

    @respx.mock
    async def test_non_json_response_raises_error(self):
        respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            return_value=httpx.Response(200, content=b"not json", headers={"content-type": "text/plain"})
        )
        client = AiReadyClient(_make_settings())
        with pytest.raises(AiReadyError) as exc_info:
            await client.search("q")
        assert not exc_info.value.retryable
        await client.aclose()

    @respx.mock
    async def test_connection_error_raises_retryable(self):
        respx.post(f"{BASE}/datasets/{DATASET}/search").mock(
            side_effect=httpx.ConnectError("refused")
        )
        client = AiReadyClient(_make_settings())
        with pytest.raises(AiReadyError) as exc_info:
            await client.search("q")
        assert exc_info.value.retryable
        await client.aclose()


# ---------------------------------------------------------------------------
# get_settings / get_client helpers
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_get_settings_not_configured(self, monkeypatch):
        monkeypatch.delenv("AI_READY_BASE_URL", raising=False)
        s = get_settings()
        assert not s.configured

    def test_get_settings_configured(self, monkeypatch):
        monkeypatch.setenv("AI_READY_BASE_URL", "http://x")
        s = get_settings()
        assert s.configured
