# pinescript — Claude Code plugin

Pine Script v6 authoring assistant. Turns Claude into a useful pairing partner for TradingView script work, backed by the [pinescript-mcp](https://github.com/paulieb89/pinescript-mcp) server.

## What it does

Two [agentskills.io](https://agentskills.io)-compliant skills:

- **`pine`** — writes Pine Script v6 indicators and strategies from natural-language descriptions. Validates every function call against the v6 allowlist before emitting code. Auto-triggers on Pine Script asks; also responds to `/pine <description>`.
- **`pine-validate`** — validates a Pine snippet or function name against the v6 allowlist. Auto-triggers on validation asks; also responds to `/pine-validate <snippet>`.

The plugin's primary value is **first-try, validated Pine v6 code** — no hallucinated function names, no v5/v6 confusion.

## Install

From the repo root:

```bash
claude --plugin-dir /path/to/pinescript-mcp/plugin
```

Or copy the contents of this `plugin/` directory into your project's `.claude-plugin/`.

## Prerequisites

The plugin connects to the hosted `pinescript-mcp` server at `https://pinescript-mcp.fly.dev/mcp` — no local setup required.

**For offline or private use**, replace `.mcp.json` with the stdio configuration:

```json
{
  "mcpServers": {
    "pinescript": {
      "command": "uvx",
      "args": ["pinescript-mcp"]
    }
  }
}
```

This requires [`uv`](https://docs.astral.sh/uv/) on PATH.

## Example prompts

Pine authoring (triggers `pine` skill):

- *Write me a Pine Script indicator that plots a 200 EMA with breakout signals.*
- *`/pine` RSI divergence detector on a 5-minute chart*
- *Build a Pine v6 strategy that buys on supertrend flips with a 2% trailing stop.*

Validation (triggers `pine-validate` skill):

- *Is `ta.adx` a valid Pine v6 function?*
- *`/pine-validate` `security(syminfo.tickerid, "D", close)`*
- *Check this Pine snippet for hallucinated function calls before I paste it into TradingView.*

## Plugin layout

```
plugin/
├── .claude-plugin/plugin.json   # Plugin manifest
├── .mcp.json                    # MCP server registration
├── skills/
│   ├── pine/                    # Authoring skill + supporting refs/assets
│   └── pine-validate/           # Validation skill + replacements reference
└── README.md
```

Both skills conform strictly to the [agentskills.io specification](https://agentskills.io/specification.md). Validate with:

```bash
uvx --from skills-ref agentskills validate plugin/skills/pine
uvx --from skills-ref agentskills validate plugin/skills/pine-validate
```

## License

MIT. See repository root `LICENSE`.
