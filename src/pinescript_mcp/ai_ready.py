"""
ai-ready-data client for pinescript-mcp.

Consumes the pinescript-v06 dataset from an ai-ready-data service via
POST /datasets/{dataset}/search. All existing deterministic tools are
unaffected — this module is only imported by the two semantic tools.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Settings — loaded from environment at first client instantiation
# ---------------------------------------------------------------------------

class AiReadySettings:
    """Reads ai-ready connection config from environment variables."""

    def __init__(self) -> None:
        self.base_url: str = os.getenv("AI_READY_BASE_URL", "").rstrip("/")
        self.dataset: str = os.getenv("AI_READY_DATASET", "pinescript-v06")
        self.timeout: float = float(os.getenv("AI_READY_TIMEOUT", "10.0"))
        self.top_k: int = int(os.getenv("AI_READY_TOP_K", "5"))
        self.api_key: str = os.getenv("AI_READY_API_KEY", "")

    @property
    def configured(self) -> bool:
        return bool(self.base_url)


# ---------------------------------------------------------------------------
# Normalised result model — shields the MCP tools from API response changes
# ---------------------------------------------------------------------------

class AiReadyResult(BaseModel):
    chunk_id: str | None = None
    score: float | None = None
    text: str
    title: str | None = None
    path: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = {}

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("result text is empty")
        return v


def _normalise_result(raw: dict[str, Any]) -> AiReadyResult:
    """Map one raw result dict to AiReadyResult regardless of response shape."""
    # Text — try common field names
    text = (
        raw.get("text")
        or raw.get("content")
        or raw.get("chunk")
        or raw.get("passage")
        or ""
    )
    # Score — try common field names
    score_raw = raw.get("score") or raw.get("relevance_score") or raw.get("similarity")
    score = float(score_raw) if score_raw is not None else None

    # Path / source
    path = (
        raw.get("path")
        or raw.get("doc_path")
        or raw.get("file")
        or raw.get("source")
    )
    # Title / section header
    title = (
        raw.get("title")
        or raw.get("section")
        or raw.get("header")
    )
    # Chunk id
    chunk_id = (
        raw.get("chunk_id")
        or raw.get("id")
    )
    if chunk_id is not None:
        chunk_id = str(chunk_id)

    # Everything else goes into metadata
    known = {"text", "content", "chunk", "passage", "score", "relevance_score",
             "similarity", "path", "doc_path", "file", "source",
             "title", "section", "header", "chunk_id", "id",
             "summary", "metadata"}
    leftover = {k: v for k, v in raw.items() if k not in known}
    metadata = {**raw.get("metadata", {}), **leftover}

    return AiReadyResult(
        chunk_id=chunk_id,
        score=score,
        text=str(text),
        title=title,
        path=str(path) if path else None,
        summary=raw.get("summary"),
        metadata=metadata,
    )


def _parse_response(body: Any) -> list[AiReadyResult]:
    """Parse API response — tolerates {results: [...]} or bare list."""
    if isinstance(body, dict):
        items = body.get("results") or body.get("hits") or body.get("chunks") or []
    elif isinstance(body, list):
        items = body
    else:
        return []

    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            results.append(_normalise_result(item))
        except Exception:
            # Skip malformed entries rather than failing the whole call
            continue
    return results


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class AiReadyError(Exception):
    """Raised when the ai-ready service returns an error."""
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class AiReadyClient:
    """Async httpx wrapper for the ai-ready-data search endpoint."""

    def __init__(self, settings: AiReadySettings) -> None:
        self._settings = settings
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"
        self._http = httpx.AsyncClient(
            base_url=settings.base_url,
            headers=headers,
            timeout=settings.timeout,
        )

    async def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
    ) -> list[AiReadyResult]:
        """POST /datasets/{dataset}/search and return normalised results."""
        dataset = self._settings.dataset
        k = top_k if top_k is not None else self._settings.top_k
        url = f"/datasets/{dataset}/search"
        payload = {"query": query, "top_k": k}

        try:
            resp = await self._http.post(url, json=payload)
            resp.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AiReadyError(
                f"ai-ready request timed out after {self._settings.timeout}s",
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            retryable = exc.response.status_code >= 500
            raise AiReadyError(
                f"ai-ready returned HTTP {exc.response.status_code}: {exc.response.text[:200]}",
                retryable=retryable,
            ) from exc
        except httpx.RequestError as exc:
            raise AiReadyError(
                f"ai-ready connection error: {exc}",
                retryable=True,
            ) from exc

        try:
            body = resp.json()
        except Exception as exc:
            raise AiReadyError(
                "ai-ready returned non-JSON response",
                retryable=False,
            ) from exc

        return _parse_response(body)

    async def aclose(self) -> None:
        await self._http.aclose()


# ---------------------------------------------------------------------------
# Lazy singleton — created on first tool call, never at import time
# ---------------------------------------------------------------------------

_client: AiReadyClient | None = None


def get_client() -> AiReadyClient:
    """Return the shared AiReadyClient, creating it on first call."""
    global _client
    if _client is None:
        _client = AiReadyClient(AiReadySettings())
    return _client


def get_settings() -> AiReadySettings:
    """Return settings without creating a client (for guard checks)."""
    return AiReadySettings()
