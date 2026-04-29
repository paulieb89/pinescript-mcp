# pinescript-mcp

<!-- mcp-name: io.github.paulieb89/pinescript-mcp -->

[![pinescript-mcp MCP server](https://glama.ai/mcp/servers/paulieb89/pinescript-mcp/badges/card.svg)](https://glama.ai/mcp/servers/paulieb89/pinescript-mcp)
[![smithery badge](https://smithery.ai/badge/bouch/pinescript)](https://smithery.ai/servers/bouch/pinescript)

MCP server providing Pine Script v6 documentation for AI assistants (Claude, etc.).

Enables AI to:
- Look up Pine Script functions and validate syntax
- Access official documentation for indicators, strategies, and visuals
- Understand Pine Script concepts (execution model, repainting, etc.)
- Generate correct v6 code with proper function references

## Quick Start (stdio)

Works with Claude Code, Claude Desktop, Gemini CLI, and any MCP client that supports stdio:

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

## Public Server (No Install Required)

No Python or uvx needed — connect directly to the hosted server.

**Streamable HTTP** — Claude Code, Claude Desktop, Cursor, Cline (standard `mcpServers` with `type` field):

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "type": "http",
      "url": "https://pinescript-mcp.fly.dev/mcp"
    }
  }
}
```

**Windsurf** — uses its own `serverUrl` shape (see [Windsurf docs](https://docs.windsurf.com/windsurf/cascade/mcp#remote-http-mcps)). Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "serverUrl": "https://pinescript-mcp.fly.dev/mcp"
    }
  }
}
```

**ChatGPT** — no config file. In ChatGPT, go to **Settings → Connectors → Create** and paste `https://pinescript-mcp.fly.dev/mcp` into the Server URL field. Developer Mode must be enabled (see [OpenAI Developer Mode guide](https://platform.openai.com/docs/mcp)).

**Claude.ai** — add via the web UI's MCP connector settings, not a JSON file.

**SSE** (legacy transport, kept for older clients):

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "type": "sse",
      "url": "https://pinescript-mcp.fly.dev/sse"
    }
  }
}
```

Streamable HTTP is preferred — SSE is being phased out across the MCP ecosystem.

## Version Pinning

Documentation is bundled in the package — each version contains a frozen snapshot. For reproducible agent behaviour, pin to a specific version:

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "command": "uvx",
      "args": ["pinescript-mcp==0.7.0"]
    }
  }
}
```

Without pinning, `uvx pinescript-mcp` gets the latest version.

> Note: versions before `0.7.0` included `lint_script` and `edit_and_lint` tools that were removed in 0.7.0 (docs-only server). Pinning to 0.6.x will give you those tools back, but the auth gate on `lint_script` was never completed on the hosted Fly instance, so they'll return auth errors on HTTP. Pin 0.7.0+ for the current, working tool surface.

## Available Tools

| Tool | Description |
|------|-------------|
| `resolve_topic(query)` | Fast lookup for exact API terms (`ta.rsi`, `repainting`) |
| `search_docs(query)` | Grep for exact strings across all docs |
| `list_docs()` | List all documentation files with descriptions |
| `list_sections(path)` | List `##` headers in a doc file (for navigating large files) |
| `get_doc(path)` | Read a specific documentation file |
| `get_section(path, header)` | Read a specific section by header |
| `get_functions(namespace)` | List valid functions (ta, strategy, etc.) |
| `validate_function(name)` | Check if a function exists in Pine v6 |
| `list_resources()` | Browse available documentation resources |
| `read_resource(uri)` | Read a doc resource by URI (e.g. `docs://manifest`) |
| `list_prompts()` | List available prompt templates |
| `get_prompt(name, arguments)` | Render a prompt template with arguments |

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `debug_error(error, code)` | Analyze a Pine Script compilation error |
| `convert_v5_to_v6(code)` | Convert Pine Script v5 code to v6 syntax |
| `explain_function(name)` | Explain a Pine Script function in detail |

## Available Resources

| URI | Description |
|-----|-------------|
| `docs://manifest` | **Start here** — routing guide for Pine Script questions |
| `docs://functions` | Complete Pine Script v6 function list (JSON) |
| `docs://{path}` | Any doc file by path (e.g. `concepts/timeframes.md`) |

## Example Queries

- "How do I create a trailing stop in Pine Script?"
- "What's the difference between var and varip?"
- "Is ta.supertrend a valid function?"
- "How do I avoid repainting with request.security?"

## Documentation Coverage

The server bundles comprehensive Pine Script v6 documentation:

- **Concepts**: Execution model, timeframes, colors, methods, objects, common errors
- **Reference**: Types, variables, constants, keywords, operators, annotations
- **Functions**: Technical analysis (ta.*), strategies, requests, drawings, collections
- **Visuals**: Plots, fills, shapes, tables, lines, boxes, backgrounds
- **Writing Scripts**: Style guide, debugging, optimization, limitations

## Why Use This?

AI models often hallucinate Pine Script functions or use deprecated v5 syntax. This MCP server grounds the AI in actual v6 documentation, preventing:

- Made-up function names (e.g., `ta.hull` doesn't exist, use `ta.hma`)
- Deprecated syntax from v4/v5
- Incorrect parameter orders
- Missing required arguments

## Skills

Combine with skills for even more control available at [bouch.dev/products/pine-strategy-builder](https://bouch.dev/products/pine-strategy-builder).

## Development

```bash
# Clone and install locally
git clone https://gitlab.com/articat1066/pinescript-v6-mcp
cd pinescript-mcp
pip install -e .

# Run the server
pinescript-mcp
```

## License

MIT
