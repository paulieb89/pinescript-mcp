---
name: pine-validate
description: >-
  Validates Pine Script v6 function calls against the official v6 allowlist via
  the pinescript MCP server. Use when the user invokes /pine-validate, pastes a
  Pine Script snippet and asks whether it compiles, asks whether a specific
  function like ta.adx, ta.sum, security(), study() or request.security() is a
  valid Pine v6 function, asks Claude to check a Pine script for hallucinated
  or renamed function references before running it on TradingView, or asks to
  audit a snippet for v5-to-v6 migration issues. Extracts every function call,
  validates each via the validate_function MCP tool, and returns a compact
  table of results with known-replacement suggestions for invalid or renamed
  calls. Keywords: validate, Pine Script, Pine v6, TradingView, function,
  allowlist, compile check, v5 to v6 migration.
license: MIT
compatibility: >-
  Designed for Claude Code and other agentskills.io-compliant clients.
  Requires the pinescript MCP server providing the validate_function tool,
  hosted at https://pinescript-mcp.fly.dev/mcp or available locally via
  uvx pinescript-mcp.
metadata:
  version: "0.1.0"
  repository: https://github.com/paulieb89/pinescript-mcp
---

# pine-validate

Validate Pine Script v6 function references against the v6 allowlist. The
authoritative source of truth is the `validate_function` MCP tool on the
`pinescript` server. Never assert a function is valid from memory — always
check via the tool.

## When to activate

- The user invokes `/pine-validate` explicitly.
- The user pastes a Pine Script snippet and asks "does this compile?",
  "is this valid Pine v6?", "check this for errors", or similar.
- The user asks about a single function: "is `ta.adx` valid?",
  "does `security()` exist in v6?", "what replaced `study()`?".
- The user asks to audit a script for hallucinated, renamed, or v5-era
  function references before running on TradingView.

Do not activate for general Pine Script authoring requests — that is the
`pine` skill's job. This skill is read-only validation.

## Workflow (mandatory, in order)

### Step 1: Parse the input and extract function references

From the user's input, extract every distinct function reference. A function
reference is anything that looks like a call site:

- `<namespace>.<func>(` — namespaced calls like `ta.rsi(`, `strategy.entry(`,
  `request.security(`, `math.sum(`.
- `<func>(` — top-level calls like `plot(`, `indicator(`, `input(`.

Apply these filters when extracting:

- **Ignore comments.** Pine comments start with `//`. Skip anything after
  `//` on a line.
- **Ignore string literals.** Anything inside `"..."` or `'...'` is not a
  call.
- **Ignore definitions.** Skip user-defined function definitions of the form
  `myFunc(...) =>` — those are declarations, not calls against the allowlist.
- **Deduplicate.** Validate each unique name once, even if it appears many
  times in the snippet.

If the user provided only a bare function name (e.g. "is `ta.adx` valid?"),
treat that as a single reference to validate.

### Step 2: Validate each reference via `validate_function`

For each unique function name extracted, call the MCP tool:

```
validate_function(fn_name="<name>")
```

The tool returns a `ValidationResult` object with:

- `valid` — boolean.
- `type` — `"namespaced"`, `"toplevel"`, or `null`.
- `function` — the name that was checked.
- `suggestion` — replacement hint or guidance, present when `valid` is false.

Call the tool once per unique name. Do not batch, do not skip, do not infer
results without calling.

### Step 3: Report results as a compact table

Render the findings as a markdown table in this exact shape:

| Function | Valid | Suggested replacement |
|---|---|---|
| `ta.rsi` | yes | — |
| `ta.adx` | no | ta.adx() does NOT exist. Use ta.dmi(diLen, adxSmoothing) → returns [diPlus, diMinus, adx] as a tuple. |

Rules for the table:

- One row per unique function reference.
- Sort: invalid rows first, then valid rows, alphabetically within each
  group. Invalid rows are the actionable ones.
- Wrap function names in backticks.
- Use `—` (em dash) in the replacement column when the function is valid.
- Quote the `suggestion` field verbatim from the tool response for invalid
  rows. Do not paraphrase.

### Step 4: Summarise and recommend next action

After the table:

- **If every function is valid:** state explicitly that all function calls
  validate against the Pine v6 allowlist and the snippet should compile on
  TradingView (subject to non-function errors — type mismatches, missing
  arguments, etc., which this skill does not check).
- **If any function is invalid:** suggest the user re-run their script with
  the listed replacements applied, then revalidate. Where the suggestion
  names a concrete replacement (e.g. `security` → `request.security`), offer
  to rewrite the snippet inline if the user wants — but only on request,
  do not rewrite unprompted.

## Edge cases

- **Empty input.** If the user invokes the skill without a snippet or a
  function name, ask for what to validate. Do not call the tool with an
  empty string.
- **No function calls detected.** If parsing finds no call sites (e.g. the
  user pasted variable declarations only), say so and ask whether they meant
  a different snippet.
- **Method-call syntax.** Pine v6 supports method-call syntax on user types
  and arrays (e.g. `myArray.push(x)`). Treat `<identifier>.<method>(` as a
  call only when `<identifier>` is a known namespace (`ta`, `math`, `array`,
  `strategy`, `request`, `input`, `str`, `chart`, `color`, `line`, `label`,
  `box`, `table`, `polyline`, `map`, `matrix`, `runtime`, `session`,
  `syminfo`, `ticker`, `time`, `timeframe`). For ambiguous prefixes, validate
  and let the tool's response settle it.
- **`input()` calls.** Bare `input(` is flagged by the allowlist as
  preferred-typed-variant. Pass that suggestion through verbatim in the
  table.
- **Large snippets.** If the snippet has more than ~50 unique function
  references, validate the first 50 alphabetically and tell the user the
  remainder were truncated; offer to continue on request.

## Quick reference

For a static reference table of commonly invalid or renamed Pine functions
and their canonical replacements, see
[references/known-replacements.md](references/known-replacements.md). That
file mirrors the `KNOWN_REPLACEMENTS` map maintained inside the MCP server
and is useful when the user wants the answer without round-tripping the
tool. The MCP `validate_function` tool remains the source of truth — the
reference file is a cache for human reading.

## Example session

User: *"Is this snippet valid Pine v6? `plot(ta.rsi(close, 14))
security(syminfo.tickerid, 'D', close)`"*

1. Extract calls: `plot`, `ta.rsi`, `security`, `syminfo.tickerid`.
   (`syminfo.tickerid` is a variable, not a call — drop it.)
2. Call `validate_function` for each of: `plot`, `ta.rsi`, `security`.
3. Render:

| Function | Valid | Suggested replacement |
|---|---|---|
| `security` | no | security() was renamed in v5. Use request.security() instead. |
| `plot` | yes | — |
| `ta.rsi` | yes | — |

4. Summarise: one invalid call. Recommend replacing `security(` with
   `request.security(` and revalidating.
