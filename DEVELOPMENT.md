# Development Guide

## Quick Start

```bash
git clone https://gitlab.com/articat1066/pinescript-v6-mcp
cd pinescript-v6-mcp
pip install -e .
pinescript-mcp  # runs stdio server
```

## Project Structure

```
pinescript-mcp/
├── src/pinescript_mcp/
│   ├── __init__.py          # Package version
│   ├── __main__.py           # python -m entrypoint
│   ├── server.py             # MCP server implementation
│   └── docs/                 # Bundled documentation
│       ├── LLM_MANIFEST.md   # Topic routing index
│       ├── concepts/         # Execution model, timeframes, etc.
│       ├── reference/        # Types, variables, functions
│       ├── visuals/          # Plots, drawings, tables
│       └── writing_scripts/  # Style guide, debugging
├── pyproject.toml            # Package metadata
├── server.json               # MCP Registry manifest
├── Dockerfile                # HTTP server container
├── fly.toml                  # Fly.io deployment config
└── .bumpversion.toml         # Version management
```

## Running Locally

### stdio mode (for Claude Code/Desktop)

```bash
pinescript-mcp
```

### HTTP mode (for testing public server)

```bash
pinescript-mcp --http --port 8000
```

Then test:
```bash
curl http://localhost:8000/health
```

## Tools Overview

| Tool | Purpose |
|------|---------|
| `list_docs()` | List all doc files with descriptions |
| `get_doc(path)` | Read a specific doc file |
| `search_docs(query)` | Full-text search across docs |
| `get_functions(namespace)` | List valid functions (ta, strategy, etc.) |
| `validate_function(name)` | Check if function exists in Pine v6 |
| `resolve_topic(query)` | Map question to relevant doc files |
| `get_manifest()` | Get LLM routing guidance |

## Adding Documentation

1. Add markdown files to `src/pinescript_mcp/docs/`
2. Update `LLM_MANIFEST.md` if adding new topics
3. Update `pine_v6_functions.json` if adding function references

Documentation is bundled in the package - no external fetching.

## Version Bumping

Uses [bump-my-version](https://github.com/callowayproject/bump-my-version):

```bash
# Install once
pipx install bump-my-version

# Bump and tag
bump-my-version patch  # 0.2.1 → 0.2.2
bump-my-version minor  # 0.2.1 → 0.3.0

# Push with tags
git push && git push --tags
```

This updates:
- `pyproject.toml`
- `src/pinescript_mcp/__init__.py`
- `server.json` (both version fields)

## Publishing to PyPI

```bash
# Build
uv build

# Publish (requires API token)
uvx twine upload --config-file .pypirc dist/*
```

## Deploying to Fly.io

```bash
cd pinescript-mcp
fly deploy
```

The server runs at https://pinescript-mcp.fly.dev/mcp

Health check: https://pinescript-mcp.fly.dev/health

## Testing MCP Connection

### With Claude Code

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "pinescript-docs": {
      "type": "stdio",
      "command": "uvx",
      "args": ["pinescript-mcp"]
    }
  }
}
```

### With HTTP (public server)

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "type": "http",
      "url": "https://pinescript-mcp.fly.dev/mcp/"
    }
  }
}
```

## Architecture Notes

- Uses `mcp.server.fastmcp.FastMCP` from the official MCP SDK
- HTTP transport uses streamable-http (SSE is deprecated)
- DNS rebinding protection disabled for public server access
- Documentation loaded once at startup via `importlib.resources`
