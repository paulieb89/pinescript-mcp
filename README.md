# pinescript-mcp

<!-- mcp-name: io.github.paulieb89/pinescript-mcp -->

[![PyPI](https://img.shields.io/pypi/v/pinescript-mcp)](https://pypi.org/project/pinescript-mcp/)
[![Glama](https://img.shields.io/badge/Glama-listed-orange?style=flat-square)](https://glama.ai/mcp/servers/paulieb89/pinescript-mcp)
[![smithery badge](https://smithery.ai/badge/bouch/pinescript)](https://smithery.ai/servers/bouch/pinescript)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=pinescript-docs&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fpinescript-mcp.fly.dev%2Fmcp%22%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=pinescript-docs&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fpinescript-mcp.fly.dev%2Fmcp%22%7D&quality=insiders)
[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_Server-000000?style=flat-square&logoColor=white)](https://cursor.com/en/install-mcp?name=pinescript-docs&config=eyJ0eXBlIjoiaHR0cCIsInVybCI6Imh0dHBzOi8vcGluZXNjcmlwdC1tY3AuZmx5LmRldi9tY3AifQ==)
[![Install in VS Code (local)](https://img.shields.io/badge/VS_Code-Install_Local-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=pinescript-docs&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22pinescript-mcp%22%5D%7D)

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

## Version Pinning

Documentation is bundled in the package — each version contains a frozen snapshot. For reproducible agent behaviour, pin to a specific version:

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "command": "uvx",
      "args": ["pinescript-mcp==0.7.4"]
    }
  }
}
```

Without pinning, `uvx pinescript-mcp` gets the latest version.

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
git clone https://github.com/paulieb89/pinescript-mcp
cd pinescript-mcp
pip install -e .

# Run the server
pinescript-mcp
```

## License

MIT
