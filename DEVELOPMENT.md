# Development Guide

## Quick Start

```bash
git clone https://gitlab.com/articat1066/pinescript-v6-mcp
cd pinescript-v6-mcp
uv sync
uv run python -m pinescript_mcp          # stdio mode
uv run python -m pinescript_mcp --http   # HTTP mode (test at localhost:8000/health)
```

## Project Structure

```
pinescript-mcp/
├── src/pinescript_mcp/
│   ├── __init__.py          # Package version
│   ├── __main__.py          # python -m entrypoint
│   ├── server.py            # All MCP tools + lint rules + middleware
│   └── docs/                # Bundled documentation (frozen per version)
│       ├── LLM_MANIFEST.md  # Topic routing index for LLMs
│       ├── pine_v6_functions.json  # Function allowlist
│       ├── concepts/        # Execution model, timeframes, etc.
│       ├── reference/       # Types, variables, functions/
│       ├── visuals/         # Plots, drawings, tables
│       └── writing_scripts/ # Style guide, debugging
├── pyproject.toml           # Package metadata + dependencies
├── server.json              # MCP Registry manifest
├── Dockerfile               # HTTP server container
├── fly.toml                 # Fly.io deployment + metrics scraping
└── .bumpversion.toml        # Version sync across 4 files
```

See [README.md](README.md) for the full tools list and user-facing documentation.

## Adding a Tool

1. Add `@mcp.tool()` function in `server.py`
2. Write a clear docstring — this is what the consumer LLM sees
3. Add to `TOPIC_MAP` if the tool introduces new routable terms
4. Test locally, bump version, publish

## Updating Bundled Docs

1. Edit docs in main repo (`docs/concepts/`, `docs/reference/`, etc.)
2. Run `./sync-docs.sh` to copy to `src/pinescript_mcp/docs/`
3. Update `LLM_MANIFEST.md` if adding new topics
4. Update `pine_v6_functions.json` if adding function references
5. Bump version, publish

## Architecture

- **Framework:** `fastmcp.FastMCP` ([gofastmcp.com](https://gofastmcp.com)) — not the official `mcp` SDK
- **Transport:** Streamable HTTP at `/mcp` only ([spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports.md)). Legacy HTTP+SSE (`/sse` + `/messages/`) was dropped — it ran stateful sessions that are incompatible with Fly.io multi-instance routing (no sticky sessions). `stateless_http=True` for stateless Fly.io routing.
- **Middleware:** Rate limiting → structured logging → response limiting (order matters)
- **Transforms:** `ResourcesAsTools` + `PromptsAsTools` (applied globally, module level) — 4 synthetic tools for clients without native resource/prompt support
- **Resources:** 3 MCP resources (`docs://manifest`, `docs://functions`, `docs://{path*}`) expose docs corpus directly
- **Metrics:** Prometheus via `_timed_tool` context manager → `/metrics` endpoint → Fly.io Grafana
- **Docs loading:** `importlib.resources` at startup, no external fetching
- **DNS rebinding:** Disabled for public server access

## Consumer Integration Pattern

This repo proves a reusable pattern for domain-specific MCP servers backed by ai-ready-data.
Use this as the template for `property-mcp`, `legal-mcp`, `warden`, or any future domain server.

**Boundary rule:** ai-ready-data owns the data platform (ingest, enrichment, chunking, embedding,
Postgres, Qdrant). The consumer repo owns the domain tool surface (MCP tools, prompt templates,
bundled reference docs). The REST API is the only coupling point.

### The 6-step pattern

1. **ai-ready-data prepares the dataset.** Ingest → enrich → chunk → embed → index. The consumer
   repo has no knowledge of how data reaches the vector store.

2. **Consumer repo adds `AiReadyClient` + `AiReadySettings`.** A thin async HTTP client that calls
   `/datasets/{dataset}/search`. See `src/pinescript_mcp/ai_ready.py` for the reference
   implementation. Copy and adapt — do not publish as a shared library until the interface
   stabilises across 3+ consumers.

3. **Consumer repo keeps deterministic/domain tools.** Tools like `get_doc()`, `validate_function()`,
   `resolve_topic()` are powered by bundled files and rule-based logic. These work offline and never
   depend on the REST API.

4. **Consumer repo adds `semantic_search_{domain}()`.** One thin semantic search tool that delegates
   to `AiReadyClient.search()`. Raises `ToolError` when unconfigured so the LLM gets a clear signal
   rather than a silent empty result.

5. **Consumer repo adds one higher-level domain workflow tool.** e.g. `explain_pine_error()` —
   combines deterministic bundled content (always included, first) with optional semantic results
   (when configured). Always include the bundled fallback unconditionally; never put it inside a
   `if results:` branch.

6. **Consumer repo does not ingest, enrich, embed, or own vector storage.** No OpenAI calls, no
   Qdrant client, no chunking logic. If the data needs updating, update it in ai-ready-data and
   re-index; the consumer picks up the new index automatically.

### Key invariant — deterministic fallback for critical reference content

For tools that combine semantic results with bundled reference material (e.g. `explain_pine_error`
always includes `common_errors.md`), the bundled block must be unconditional:

```python
# Always include bundled reference — regardless of semantic search results or configuration.
reference = _get_doc_content("concepts/common_errors.md")
parts.append(reference[:4000])
```

Lock this with a test: `AI_READY_BASE_URL` configured, semantic search returns unrelated results,
bundled content is still present. See `tests/test_server_tools.py`.
