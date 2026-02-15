# CLAUDE.md

This is the **pinescript-mcp** package - an MCP server that provides Pine Script v6 documentation to AI assistants.

## Package Structure

```
src/pinescript_mcp/
├── __init__.py          # Version: __version__
├── __main__.py          # Entry point for `python -m pinescript_mcp`
├── server.py            # Main MCP server with all tools
└── docs/                # Bundled documentation (copied at build time)
```

## Key Files

- `server.py` - All MCP tools defined here. Tool docstrings are what AI sees.
- `pyproject.toml` - Package metadata, dependencies, build config
- `.bumpversion.toml` - Version bumping config (syncs pyproject.toml, __init__.py, server.json)
- `server.json` - MCP server manifest for registry/discovery
- `Dockerfile` - For Fly.io HTTP deployment

## MCP Tools (7 total)

| Tool | Purpose |
|------|---------|
| `list_docs` | List all available doc files |
| `get_doc` | Read a specific doc file (supports limit/offset) |
| `search_docs` | Grep for exact strings |
| `resolve_topic` | Natural language → doc routing (START HERE) |
| `get_manifest` | Get LLM_MANIFEST.md routing guide |
| `get_functions` | List valid Pine v6 functions by namespace |
| `validate_function` | Check if a function name is valid |

## Development Commands

```bash
# Run locally (stdio)
uv run python -m pinescript_mcp

# Run locally (HTTP)
uv run python -m pinescript_mcp --http --port 8000

# Bump version (requires clean git state)
uvx bump-my-version bump patch  # 0.2.2 → 0.2.3
uvx bump-my-version bump minor  # 0.2.2 → 0.3.0

# Build package
uv build

# Publish to PyPI
uvx twine upload dist/*

# Deploy to Fly.io
fly deploy
```

## Testing Changes

After editing `server.py`, test locally:
```bash
# Quick test with MCP inspector
uvx mcp-inspector uvx pinescript-mcp

# Or add to .mcp.json and reload Claude Code session
```

## Transport Modes

- **stdio** (default): For local Claude Desktop/Cursor/etc.
- **HTTP**: For remote access via Fly.io (`--http` flag)

## Deployment

- **PyPI**: https://pypi.org/project/pinescript-mcp/
- **Fly.io**: https://pinescript-mcp.fly.dev/mcp (HTTP transport)
- **GitLab**: https://gitlab.com/articat1066/pinescript-v6-mcp

## Common Tasks

### Adding a new tool
1. Add function with `@mcp.tool()` decorator in `server.py`
2. Write clear docstring (this is what AI sees!)
3. Test locally, bump version, publish

### Updating docs
Docs are copied from parent repo at build time. To update:
1. Edit docs in main repo (`concepts/`, `reference/`, etc.)
2. Run build script or manually copy to `src/pinescript_mcp/docs/`
3. Bump version, publish

### Fixing tool descriptions
Tool docstrings in `server.py` are the descriptions AI models see. Edit them to improve AI behavior, then bump version and republish.
