# CLAUDE.md - pinescript-mcp

MCP server providing Pine Script v6 documentation to AI assistants.

**PyPI:** https://pypi.org/project/pinescript-mcp/
**Fly.io:** https://pinescript-mcp.fly.dev/mcp

## Key Files

- `src/pinescript_mcp/server.py` - All MCP tools, lint rules, middleware. **Tool docstrings = AI-visible descriptions**
- `pyproject.toml` - Package metadata, dependencies
- `.bumpversion.toml` - Version sync (pyproject.toml, __init__.py, server.json, mcp.json)
- `fly.toml` - Fly.io deployment config + `[metrics]` for Prometheus scraping

## .gitignore - Files exist that you may not see;

- .claude/ 
- reddit/
- dist/

## MCP Tools (10 total)

| Tool | Purpose |
|------|---------|
| `get_manifest` | START HERE for natural language questions — routing guide |
| `resolve_topic` | Fast lookup for exact API terms (`ta.rsi`, `repainting`) |
| `search_docs` | Grep for exact strings |
| `list_docs` | List all available docs |
| `list_sections` | List `##` headers in a doc (navigate large files) |
| `get_doc` | Read a specific doc file (limit/offset) |
| `get_section` | Get section by markdown header |
| `get_functions` | List valid Pine v6 functions by namespace |
| `validate_function` | Check if function name is valid |
| `lint_script` | Lint Pine Script (17 rules, free, no API) |

## Commands

```bash
uv run python -m pinescript_mcp              # Run locally (stdio)
uv run python -m pinescript_mcp --http       # Run locally (HTTP)
uvx bump-my-version bump patch               # Version bump
rm -rf dist/ && uv build && uvx twine upload dist/*  # Publish PyPI
fly deploy                                   # Deploy Fly.io
uvx mcp-inspector uvx pinescript-mcp         # Test with inspector
```

## Observability

- Tool calls log JSON to stderr via `_timed_tool` context manager
- Prometheus metrics at `/metrics` (counters + histograms per tool)
- Fly.io scrapes every 15s → fly-metrics.net Grafana

## Design Decisions

- `TOPIC_MAP` is intentionally narrow (exact API terms only) — natural language routing is the LLM's job via `get_manifest()`
- `DOC_COMPANIONS` kept to 2 entries (strategy→execution_model, request→timeframes) — more causes noise
- `list_sections` filters to `##` headers only — `###` subsections are noise for navigation
- Custom `CollectorRegistry` for Prometheus — avoids default Python GC/process metrics

See @DEVELOPMENT.md for project structure and contributor workflows.
