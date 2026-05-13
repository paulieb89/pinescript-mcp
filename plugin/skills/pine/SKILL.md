---
name: pine
description: Writes Pine Script v6 indicators and strategies for TradingView from natural-language descriptions. Use when the user invokes /pine, asks Claude to write or build a Pine Script indicator, strategy, oscillator, or TradingView script, asks for a Pine v6 script, asks to convert v4/v5 Pine code to v6, or describes a trading indicator/strategy to implement (e.g. "RSI divergence", "EMA crossover strategy", "supertrend", "VWAP bands"). Routes through the pinescript MCP server (docs://manifest, get_section, validate_function) to fetch authoritative Pine v6 docs and validate every function call against the v6 allowlist before emitting code. Always produces scripts with //@version=6, the correct script-type declaration (indicator vs strategy), and named-argument calling convention. Does not invent function names. Does not emit v3/v4/v5 syntax. Keywords - Pine Script, Pine v6, TradingView, indicator, strategy, oscillator, screener, ta.rsi, ta.sma, request.security, plot, alertcondition.
license: MIT
compatibility: Designed for Claude Code and other agentskills.io-compliant hosts. Requires the pinescript MCP server, hosted at https://pinescript-mcp.fly.dev/mcp or local via `uvx pinescript-mcp` (stdio). Without the MCP server the validation step cannot run and the skill must not emit code.
metadata:
  version: "0.1.0"
  repository: https://github.com/paulieb89/pinescript-mcp
---

# pine — Pine Script v6 authoring

You are writing Pine Script v6 for TradingView. Your single most important job is to **never emit a function call you have not validated against the v6 allowlist**. Pine Script's compiler is unforgiving and TradingView users iterate by copy-paste, so a hallucinated `ta.adx()` or a stray `study()` wastes their time. This skill exists to prevent that.

Follow the seven-step authoring loop below on every invocation. Do not skip steps. Do not reorder them.

## Authoring loop

### 1. Clarify intent — at most one question, only if essential

If the user's request is missing a load-bearing detail, ask exactly one focused question. Otherwise proceed.

Load-bearing details (ask only if absent and not inferable):

- Overlay on price chart, or separate pane? (indicator only)
- Indicator or strategy? (i.e. plotting signals vs placing simulated orders)
- Specific inputs/parameters the user wants exposed (lengths, sources, thresholds)

Do **not** ask about colour schemes, label text, code style, or anything cosmetic. Make a reasonable default and proceed.

### 2. Route via the manifest

Read the `docs://manifest` MCP resource first. It is the routing index for the Pine v6 doc corpus. Identify the doc paths most relevant to the functions and concepts the script will need (e.g. `reference/functions/ta.md`, `concepts/strategies.md`, `concepts/timeframes.md`).

For exact API terms (`ta.rsi`, `request.security`, `repainting`), call `resolve_topic` to jump directly to the right doc.

### 3. Read the relevant doc sections

Prefer `get_section` over `get_doc`. Large doc files (`ta.md`, `strategy.md`, `drawing.md`) blow context if read whole. Use `list_sections` to enumerate `##` headers, then `get_section` for just the section you need.

For each function the script will call, you must have seen its actual signature, parameter order, and return type — not your memory of it. Pine v6 renamed and re-tupled enough functions that memory is unreliable.

### 4. Draft the code

The draft must include, in order:

1. `//@version=6` — first non-blank line. Never `//@version=5`.
2. Script-type declaration on the next line:
   - `indicator(title="...", shorttitle="...", overlay=<true|false>)` for indicators.
   - `strategy(title="...", shorttitle="...", overlay=<true|false>, initial_capital=..., default_qty_type=..., default_qty_value=...)` for strategies.
   - Never `study(...)` — that is v3/v4 syntax.
3. Inputs grouped at the top via `input.int`, `input.float`, `input.bool`, `input.string`, `input.source`, `input.timeframe`, `input.color`, etc. Use typed variants, not bare `input()`.
4. Calculations, using named arguments wherever the function accepts them (Pine v6 increasingly requires named args for non-positional parameters).
5. Plots and visual outputs at the bottom (`plot`, `plotshape`, `bgcolor`, `label.new`, `line.new`).
6. `alertcondition` blocks if alerts are part of the request.

See `references/v6-checklist.md` for the full set of v6 gotchas (version annotation, type qualifiers `series`/`simple`/`input`/`const`, `var`/`varip` semantics, repainting traps with `request.security` + `lookahead`, `barstate.isconfirmed` for alert hygiene).

### 5. Validate every function call — non-negotiable

This is the step that justifies the skill's existence. Before emitting code:

1. Enumerate every distinct function reference in the draft. A reference is any token that looks like `<namespace>.<func>(` (e.g. `ta.rsi(`, `request.security(`, `strategy.entry(`) or a bare `<func>(` at a function-call position (e.g. `plot(`, `indicator(`, `nz(`).
2. For each unique reference, call the `validate_function` MCP tool with the bare function name (no parentheses, no args).
3. If `valid: true`, the call is allowed.
4. If `valid: false`, the response includes a `suggestion`. Common cases: `ta.adx` → use `ta.dmi`; `security` → use `request.security`; `study` → use `indicator`; `ta.sum` → use `math.sum`. Replace the call with the suggested function, re-read the relevant doc section for the replacement, and re-validate.
5. Repeat until every function in the draft is valid.

Full validation pattern, input/output shapes, and a worked example live in `references/validation-workflow.md`. Read it on the first invocation of any session.

Do not skip validation for "obvious" functions like `plot` or `indicator`. The cost is one MCP call each and the corpus is small enough that responses are cached.

### 6. Emit the code

Render the script in a single fenced code block tagged `pinescript`. Above the block, give the user a one- or two-sentence summary of what the script does. Below the block, give a short bulleted explanation — one bullet per logical section of the code (inputs, core calculation, signal logic, plots, alerts). Aim for clarity over verbosity. Do not annotate line by line.

Use the worked example at `assets/rsi-divergence.pine` as a quality anchor for what good v6 output looks like — version annotation, named arguments, typed inputs, comments at section boundaries, no v5 holdovers.

### 7. Offer next steps

End the reply with two or three concrete follow-ups the user can pick from:

- Refine a specific parameter or input range.
- Explain a particular section in deeper detail.
- Convert from indicator to strategy (or vice versa).
- Save the script to a file in their workspace.

Keep this short — three bullets max.

## MCP surface — what to call

The pinescript MCP server exposes these tools and resources. Use the names verbatim.

**Tools:**

- `resolve_topic(query)` — fast lookup for exact API terms.
- `search_docs(query)` — multi-word search across the doc corpus (AND logic).
- `list_docs()` — list available doc files.
- `list_sections(path)` — list `##` headers in a doc.
- `get_doc(path, limit, offset)` — read a doc file with pagination.
- `get_section(path, header)` — read one section by header.
- `get_functions(namespace?)` — list valid Pine v6 functions, optionally scoped to a namespace.
- `validate_function(fn_name)` — **the mandatory pre-emit check.** Returns `ValidationResult` with `valid`, `type`, `function`, `suggestion`.
- `list_prompts()` / `get_prompt(name, args)` — synthetic prompt-template access.

**Resources:**

- `docs://manifest` — start here. Routing guide for the corpus.
- `docs://functions` — the raw v6 function allowlist.
- `docs://{path*}` — direct doc file access.

If the MCP server is unreachable (tool calls error out), stop. Tell the user the validation step cannot run and that they should check the MCP connection. Do not fall back to emitting unvalidated code.

## Output discipline

- Always tag the code block `pinescript`, not `pine` or untagged.
- Always include `//@version=6` as the first line.
- Always include a script-type declaration (`indicator(...)` or `strategy(...)`) on the second non-blank line.
- Always use named arguments for parameters beyond the first one or two, especially in `indicator()`, `strategy()`, `plot()`, `request.security()`, `ta.*` calls with optional args.
- Never emit `study(...)`, `security(...)` bare, or any other v4/v5-only function.
- Never invent a function. If you cannot validate it, do not write it.

## Supporting files

- `references/v6-checklist.md` — Pine v6 syntax gotchas, type qualifiers, v5→v6 renames, repainting traps.
- `references/validation-workflow.md` — the exact `validate_function` call pattern and how to interpret the response, with a worked example.
- `assets/rsi-divergence.pine` — fully validated RSI divergence indicator. Reference quality bar for emitted code.
