# pinescript-mcp

<!-- mcp-name: io.gitlab.articat1066/pinescript-v6-mcp -->

MCP server providing Pine Script v6 documentation for AI assistants (Claude, etc.).

Enables AI to:
- Look up Pine Script functions and validate syntax
- Access official documentation for indicators, strategies, and visuals
- Understand Pine Script concepts (execution model, repainting, etc.)
- Generate correct v6 code with proper function references

## Usage with Claude Code

Add to `.mcp.json` in your project (recommended):

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

## Usage with Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "command": "uvx",
      "args": ["pinescript-mcp"]
    }
  }
}
```

## Usage with Google Antigravity

Add to `~/.gemini/antigravity/mcp_config.json`:

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "command": "uvx",
      "args": ["pinescript-mcp"]
    }
  }
}
```

Or use the public HTTP server (no install):

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "serverUrl": "https://pinescript-mcp.fly.dev/mcp"
    }
  }
}
```

## Version Pinning

Documentation is bundled in the package - each version contains a frozen snapshot. For reproducible agent behavior, pin to a specific version:

```json
{
  "mcpServers": {
    "pinescript-docs": {
      "command": "uvx",
      "args": ["pinescript-mcp==0.5.1"]
    }
  }
}
```

Without pinning, `uvx pinescript-mcp` gets the latest version.

## Alternative: pip install

If you prefer pip over uvx:

```bash
pip install pinescript-mcp==0.5.1
```

Note: `"command": "pinescript-mcp"` only works if the install location is in your PATH. The `uvx` method above is more reliable as it handles environments automatically.

## Public Server (No Install Required)

Connect directly to the hosted server - no Python or uvx needed:

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

## Available Tools

| Tool | Description |
|------|-------------|
| `resolve_topic(query)` | **Start here** - Map a question to relevant docs |
| `get_doc(path)` | Read a specific documentation file |
| `get_section(path, header)` | Read a specific section from a documentation file |
| `search_docs(query)` | Full-text search across all docs |
| `list_docs()` | List all documentation files with descriptions |
| `get_functions(namespace)` | List valid functions (ta, strategy, etc.) |
| `validate_function(name)` | Check if a function exists in Pine v6 |
| `lint_script(script)` | Lint Pine Script (15 rules, free, no API cost) |
| `get_manifest()` | Get routing guidance for topics |

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `debug_error(error, code)` | Analyze a Pine Script compilation error |
| `convert_v5_to_v6(code)` | Convert Pine Script v5 code to v6 syntax |
| `explain_function(name)` | Explain a Pine Script function in detail |

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

## Lint Rules (15 total)

The `lint_script` tool checks for common Pine Script issues without using AI:

| Rule | Type | Description |
|------|------|-------------|
| E001 | Error | `input.enum()` with const string constants |
| E003 | Error | Return type keyword on function declaration |
| E005 | Error | `study()` → use `indicator()` |
| E006 | Error | `security()` → use `request.security()` |
| E007 | Error | `alertcondition()` in strategy scripts |
| E009 | Error | `format.currency` doesn't exist |
| E010 | Error | Direct `na` comparison (use `na()` function) |
| E012 | Error | Unknown/hallucinated function |
| E013 | Error | `input.enum()` with options array |
| E014 | Error | `strategy()` missing title parameter |
| E015 | Error | Mismatched string quotes |
| W001 | Warning | Missing `//@version=6` |
| W003 | Warning | `lookahead_on` without justification |
| W004 | Warning | High `max_bars_back` value |
| W005 | Warning | Potentially unused variable |

## Performance

The HTTP server (Fly.io) uses response caching with 1-hour TTL for documentation lookups, making repeated queries very fast.

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
