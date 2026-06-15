# CLAUDE.md - pinescript-mcp

MCP server providing Pine Script v6 documentation to AI assistants.

**PyPI:** https://pypi.org/project/pinescript-mcp/
**Fly.io:** https://pinescript-mcp.fly.dev/mcp

## Key Files

- `src/pinescript_mcp/server.py` - All MCP tools and middleware. **Tool docstrings = AI-visible descriptions**
- `pyproject.toml` - Package metadata, dependencies
- `.bumpversion.toml` - Version sync (pyproject.toml, __init__.py, server.json, mcp.json)
- `fly.toml` - Fly.io deployment config + `[metrics]` for Prometheus scraping

## .gitignore - Files exist that you may not see;

- .claude/ 
- reddit/
- dist/

## MCP Surface (10 tools, 3 resources, 3 prompts)

### Tools (8 direct + 2 synthetic)

| Tool | Purpose |
|------|---------|
| `resolve_topic` | Fast lookup for exact API terms (`ta.rsi`, `repainting`) |
| `search_docs` | Search docs — multi-word queries use AND logic |
| `list_docs` | List all available docs |
| `list_sections` | List `##` headers in a doc (navigate large files) |
| `get_doc` | Read a specific doc file (limit/offset) |
| `get_section` | Get section by markdown header |
| `get_functions` | List valid Pine v6 functions by namespace |
| `validate_function` | Check if function name is valid (known replacements for common mistakes) |
| `list_prompts` | *Synthetic* — list prompt templates |
| `get_prompt` | *Synthetic* — render a prompt with arguments |

### Resources

| URI | Content |
|-----|---------|
| `docs://manifest` | **START HERE** — LLM routing guide for Pine Script questions |
| `docs://functions` | pine_v6_functions.json allowlist |
| `docs://{path*}` | Any doc file (e.g. `concepts/timeframes.md`) |

### Prompts

| Prompt | Purpose |
|--------|---------|
| `debug_error` | Analyze Pine Script compilation errors |
| `convert_v5_to_v6` | Guide v5 → v6 migration |
| `explain_function` | Explain a Pine Script function in detail |

## Commands

```bash
uv run python -m pinescript_mcp              # Run locally (stdio)
uv run python -m pinescript_mcp --http       # Run locally (HTTP)
uvx bump-my-version bump patch               # Version bump
rm -rf dist/ && uv build && uvx twine upload dist/*  # Publish PyPI
fly deploy                                   # Deploy Fly.io
uvx mcp-inspector uvx pinescript-mcp         # Test with inspector
```

## Known Issues / Pending Fixes (before June 2, 2026)

- `.github/workflows/release.yml`: rename `skip_existing` → `skip-existing` in `pypa/gh-action-pypi-publish` (deprecated input)
- `.github/workflows/release.yml`: update `actions/checkout@v4` and `astral-sh/setup-uv@v5` to Node.js 24-compatible versions (Node.js 20 runners removed September 16, 2026)

## Observability

- Tool calls log JSON to stderr via `_timed_tool` context manager
- Prometheus metrics at `/metrics` (counters + histograms per tool)
- Fly.io scrapes every 15s → fly-metrics.net Grafana

## Design Decisions

- `TOPIC_MAP` is intentionally narrow (exact API terms only) — `resolve_topic()` falls back to a doc scan when TOPIC_MAP misses, so unknown terms still get a best-effort match
- `KNOWN_REPLACEMENTS` maps common invalid/renamed functions (e.g. `ta.adx` → `ta.dmi`, `security` → `request.security`) to specific suggestions in `validate_function()`
- Error handling uses `ToolError` (sets MCP `isError: true`) instead of returning error strings as normal content
- `DOC_COMPANIONS` kept to 2 entries (strategy→execution_model, request→timeframes) — more causes noise
- `list_sections` filters to `##` headers only — `###` subsections are noise for navigation
- Custom `CollectorRegistry` for Prometheus — avoids default Python GC/process metrics
- No BM25SearchTransform — 14 tools is small enough for direct visibility; BM25 hid tools and broke client interop
- `stateless_http=True` on Streamable HTTP app — Fly.io routes across instances without sticky sessions. Legacy SSE transport (`/sse` + `/messages/`) was dropped: it ran stateful sessions incompatible with multi-instance routing, causing ~98% tool errors via that transport
- PromptsAsTools applied globally — ResourcesAsTools intentionally omitted (companion tools already cover all 3 resources with pagination/filtering)

See @DEVELOPMENT.md for project structure and contributor workflows.
