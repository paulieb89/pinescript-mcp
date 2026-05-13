# Known Pine Script v6 replacements

A human-readable digest of the `KNOWN_REPLACEMENTS` map maintained in the
`pinescript-mcp` server (`src/pinescript_mcp/server.py`). When the
`validate_function` MCP tool flags a function as invalid and the name
appears in this map, the tool returns the corresponding suggestion verbatim.

This file is a cache for quick human lookup. The MCP server is the source
of truth — if a mismatch appears, the server wins and this file should be
updated.

## Mappings

| Invalid call | Suggested replacement | Notes |
|---|---|---|
| `ta.adx` | `ta.dmi(diLen, adxSmoothing)` — returns `[diPlus, diMinus, adx]` as a tuple. | `ta.adx()` does not exist in Pine v6. Use `ta.dmi()` and destructure the third element when only the ADX line is needed. |
| `ta.sum` | `math.sum(source, length)` | `ta.sum()` does not exist in Pine v6. The rolling-sum helper lives in the `math` namespace. |
| `security` | `request.security(...)` | Renamed in Pine v5. The bare `security()` form no longer resolves. |
| `study` | `indicator(...)` | Renamed in Pine v5. Script-type declarations now use `indicator(` for non-strategy scripts. |
| `input` | Prefer typed variants: `input.int()`, `input.float()`, `input.string()`, `input.bool()`, etc. | Bare `input()` still works in Pine v6, but the typed variants are the recommended form and produce clearer, type-checked code. |

## When these replacements apply

- **v5-to-v6 migration.** `security` → `request.security` and `study` →
  `indicator` were introduced in the v4-to-v5 transition and remain the
  correct calls in v6. Snippets copy-pasted from older TradingView scripts
  or older AI outputs commonly trip these.
- **Common LLM hallucinations.** `ta.adx` and `ta.sum` are the canonical
  hallucinated names — they sound plausible (the `ta` namespace exists, ADX
  is a real indicator) but neither call exists in the v6 allowlist. Models
  invent them by analogy.
- **Style upgrades.** The `input` entry is not a hard error; bare `input()`
  compiles. It is included as a style nudge for code being written fresh
  rather than migrated.

## Using this reference

For ad-hoc lookups during a Pine authoring session, skim the table here. For
authoritative validation — including functions not listed above — call the
`validate_function` MCP tool. The tool also handles generic cases (unknown
namespaces, typos in valid namespaces) with targeted guidance derived from
the live allowlist.
