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

## MCP Surface (12 tools, 3 resources, 3 prompts)

### Tools (8 direct + 4 synthetic)

| Tool | Purpose |
|------|---------|
| `resolve_topic` | Fast lookup for exact API terms (`ta.rsi`, `repainting`) |
| `search_docs` | Grep for exact strings |
| `list_docs` | List all available docs |
| `list_sections` | List `##` headers in a doc (navigate large files) |
| `get_doc` | Read a specific doc file (limit/offset) |
| `get_section` | Get section by markdown header |
| `get_functions` | List valid Pine v6 functions by namespace |
| `validate_function` | Check if function name is valid |
| `list_resources` | *Synthetic* — list available doc resources |
| `read_resource` | *Synthetic* — read a doc resource by URI |
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

## Observability

- Tool calls log JSON to stderr via `_timed_tool` context manager
- Prometheus metrics at `/metrics` (counters + histograms per tool)
- Fly.io scrapes every 15s → fly-metrics.net Grafana

## Design Decisions

- `TOPIC_MAP` is intentionally narrow (exact API terms only) — natural language routing is the LLM's job via the `docs://manifest` resource
- `DOC_COMPANIONS` kept to 2 entries (strategy→execution_model, request→timeframes) — more causes noise
- `list_sections` filters to `##` headers only — `###` subsections are noise for navigation
- Custom `CollectorRegistry` for Prometheus — avoids default Python GC/process metrics
- No BM25SearchTransform — 14 tools is small enough for direct visibility; BM25 hid tools and broke client interop
- `stateless_http=True` on both HTTP apps — Fly.io routes across instances, no session affinity needed
- ResourcesAsTools + PromptsAsTools applied globally — STDIO clients lack resource/prompt UI too

See @DEVELOPMENT.md for project structure and contributor workflows.
