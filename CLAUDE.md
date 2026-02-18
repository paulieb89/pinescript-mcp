# CLAUDE.md - pinescript-mcp

MCP server providing Pine Script v6 documentation to AI assistants.

**PyPI:** https://pypi.org/project/pinescript-mcp/
**Fly.io:** https://pinescript-mcp.fly.dev/mcp

## Key Files

- `src/pinescript_mcp/server.py` - All MCP tools. **Tool docstrings = AI-visible descriptions**
- `pyproject.toml` - Package metadata, dependencies
- `.bumpversion.toml` - Version sync (pyproject.toml, __init__.py, server.json)
- `Dockerfile` - For Fly.io HTTP deployment

## MCP Tools (9 total)

| Tool | Purpose |
|------|---------|
| `resolve_topic` | START HERE - natural language → doc routing |
| `search_docs` | Grep for exact strings |
| `get_doc` | Read a specific doc file (limit/offset) |
| `get_section` | Get section by markdown header |
| `list_docs` | List all available docs |
| `get_functions` | List valid Pine v6 functions by namespace |
| `validate_function` | Check if function name is valid |
| `get_manifest` | Get LLM_MANIFEST.md routing guide |
| `lint_script` | Lint Pine Script (free, no API) |

## Commands

```bash
# Run locally
uv run python -m pinescript_mcp              # stdio
uv run python -m pinescript_mcp --http       # HTTP

# Version bump (requires clean git)
uvx bump-my-version bump patch               # 0.2.2 → 0.2.3

# Build and publish
uv build && uvx twine upload dist/*

# Deploy
fly deploy

# Test with inspector
uvx mcp-inspector uvx pinescript-mcp
```

## Logging

Tools log to stderr (visible in VSCode output panel, `fly logs`):
```
[TOOL] {"event": "tool_call", "tool": "resolve_topic", "query": "...", "duration_ms": 5}
```

## Common Tasks

### Adding a tool
1. Add `@mcp.tool()` function in `server.py`
2. Write clear docstring (this is what AI sees!)
3. Test locally, bump version, publish

### Updating bundled docs
1. Edit docs in main repo (`concepts/`, `reference/`)
2. Copy to `src/pinescript_mcp/docs/`
3. Bump version, publish
