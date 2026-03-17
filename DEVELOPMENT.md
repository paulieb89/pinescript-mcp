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
- **Transport:** streamable-http in production (SSE is deprecated)
- **Middleware:** Rate limiting → structured logging → response limiting → response caching (order matters)
- **Metrics:** Prometheus via `_timed_tool` context manager → `/metrics` endpoint → Fly.io Grafana
- **Docs loading:** `importlib.resources` at startup, no external fetching
- **Caching:** `ResponseCachingMiddleware` with 1hr TTL + disk persistence (survives Fly suspend)
- **DNS rebinding:** Disabled for public server access
