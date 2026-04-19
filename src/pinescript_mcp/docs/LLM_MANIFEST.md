# Pine Script v6 Documentation Manifest

**Purpose:** This file is a directory map and tool guide for LLMs using the pinescript-mcp server. Read this first, then use the tools below to retrieve exactly the content you need.

---

## How to Use These Tools

**For exact Pine Script API terms** (`ta.rsi`, `strategy.entry`, `repainting`, `request.security`, etc.):
→ `resolve_topic(query)` — fast keyword lookup, returns doc path immediately

**For natural language questions** ("how do I...", "why is my...", "what's the difference..."):
→ Read the doc sections below to find the right file, then retrieve it directly

**Retrieval tools:**
- **Large files** (`ta.md`, `strategy.md`, `collections.md`, `drawing.md`, `general.md`) — 1000–2800 lines each:
  `list_sections(path)` → see all headers → `get_section(path, header)` for specific content
- **Small files** → `get_doc(path)` to read the whole thing
- **Exact string grep** → `search_docs(query)` across all docs

**Validation tools:**
- `validate_function(fn_name)` — checks if a function exists, suggests closest match
- `get_functions(namespace)` — lists all functions in a namespace (e.g. `"ta"`, `"strategy"`)

**Read docs first.** When writing Pine Script, consult the relevant docs
before coding. Use `validate_function` to sanity-check any non-obvious
function names. Paste the finished script into TradingView's Pine Editor —
the TradingView compiler will surface any syntax or type errors on "Add to
Chart", which is faster and more authoritative than a server-side linter.

---

## 1. Syntax and Core Concepts

*Use these for language mechanics, execution flow, type errors, and OOP patterns.*

- **`concepts/execution_model.md`**
  - Bar-by-bar execution, `var` / `varip`, historical vs. real-time context, `barstate.*`
  - Keywords: `barstate`, `history`, `realtime`, `calc_on_every_tick`, `var`, `varip`

- **`concepts/timeframes.md`**
  - Multi-timeframe data, repainting prevention, `lookahead` parameter
  - Keywords: `request.security`, `timeframe.period`, `repainting`, `HTF`, `lookahead`

- **`concepts/colors_and_display.md`**
  - Defining colors, gradients, transparency, `color.new`, `bgcolor`
  - Keywords: `color.new`, `color.from_gradient`, `bgcolor`, `transparency`

- **`concepts/common_errors.md`**
  - Explanations for runtime and compile-time errors
  - Keywords: `"series string"`, `"undeclared identifier"`, `max_bars_back`, `compile error`

- **`concepts/methods.md`**
  - User-defined methods, `.method()` syntax, extending built-in types
  - Keywords: `method`, `methods`, user-defined methods, extending types

- **`concepts/objects.md`**
  - User-defined types (UDT), `type` keyword, object-oriented patterns
  - Keywords: `udt`, `user-defined type`, `object`, `type keyword`

---

## 2. API Reference

*Use these for built-in variables, constants, keywords, operators, and annotations.*

- **`reference/variables.md`**
  - Built-in read-only variables: `open`, `high`, `low`, `close`, `volume`, `time`, `syminfo.*`, `bar_index`

- **`reference/constants.md`**
  - Fixed constants: `color.red`, `shape.triangle`, `plot.style_line`, `size.small`, `alert.freq_once_per_bar`

- **`reference/types.md`**
  - Type system: `int`, `float`, `bool`, `color`, `string`, `line`, `label`, `box`, `simple`, `series`, `const`

- **`reference/keywords.md`**
  - Language keywords: `if`, `else`, `switch`, `for`, `while`, `export`, `import`, `method`

- **`reference/operators.md`**
  - Arithmetic, comparison, logical, and ternary operators

- **`reference/annotations.md`**
  - Script type annotations: `indicator()`, `strategy()`, `library()`, `export`, `@description`, `@param`, `@returns`

- **`reference/pine_v6_cheatsheet.md`**
  - Compact v6 reference: valid functions, namespaces, built-in variables, common pitfalls

---

## 3. Function Reference

*Large files — always use `list_sections()` + `get_section()`, not `get_doc()`.*

- **`reference/functions/ta.md`** (~197 sections)
  - Technical analysis: `ta.rsi`, `ta.sma`, `ta.ema`, `ta.macd`, `ta.crossover`, `ta.atr`, `ta.vwap`, `ta.pivot_point_levels`

- **`reference/functions/strategy.md`** (~48 sections)
  - Backtesting engine: `strategy.entry`, `strategy.exit`, `strategy.close`, `strategy.position_size`, `strategy.equity`
  - Read with: `concepts/execution_model.md`

- **`reference/functions/request.md`**
  - External data: `request.security`, `request.financial`, `request.seed`, `request.currency_rate`
  - Read with: `concepts/timeframes.md`

- **`reference/functions/drawing.md`** (~110 sections)
  - Chart objects: `plot`, `plotshape`, `plotchar`, `line.new`, `box.new`, `label.new`, `polyline.new`, `fill`

- **`reference/functions/collections.md`** (~115 sections)
  - Data structures: `array.new`, `array.push`, `matrix.new`, `matrix.mult`, `map.new`, `map.put`

- **`reference/functions/general.md`** (~115 sections)
  - Math, strings, inputs: `math.abs`, `math.round`, `str.tostring`, `str.format`, `input.int`, `input.bool`, `alert()`

---

## 4. Visuals

*Use these when the user asks about chart appearance, colors, plots, or drawing.*

- **`visuals/overview.md`** — Start here for visual concepts; explains all output types
- **`visuals/plots.md`** — `plot()`, basic line/area/histogram/step output
- **`visuals/backgrounds.md`** — `bgcolor()`, background highlighting by condition
- **`visuals/bar_coloring.md`** — `barcolor()`, conditional bar/candle colors
- **`visuals/bar_plotting.md`** — `plotcandle()`, `plotbar()`, custom OHLC rendering
- **`visuals/colors.md`** — `color.new()`, `color.rgb()`, gradients, transparency
- **`visuals/fills.md`** — `fill()` between plots and hlines
- **`visuals/levels.md`** — `hline()`, horizontal reference levels
- **`visuals/lines_and_boxes.md`** — `line.new()`, `box.new()` drawing objects
- **`visuals/tables.md`** — `table.new()`, `table.cell()` for on-chart data display
- **`visuals/texts_and_shapes.md`** — `label.new()`, `plotshape()`, `plotchar()`

---

## 5. Writing Scripts

*Use these for code quality, debugging, and understanding Pine Script limits.*

- **`writing_scripts/style_guide.md`** — Naming conventions, code organisation, best practices
- **`writing_scripts/debugging.md`** — `log.*`, `runtime.error()`, debugging techniques
- **`writing_scripts/limitations.md`** — Max bars back, memory limits, Pine Script constraints
- **`writing_scripts/profiling_and_optimization.md`** — Performance optimisation, profiling tools

---

## 6. Migration

*Use when the user asks about v5 → v6 changes, deprecated functions, or conversion.*

- **`reference/migration_v5_to_v6.md`** — Breaking changes, renamed functions, v5 → v6 migration guide
  - Keywords: `migrate`, `v5 to v6`, `deprecated`, `study()`, `security()`, `upgrade`

---

## Routing Examples

These examples show the full tool call sequence, not just the doc to retrieve.

> All tools below are available directly — call them by name.

**"What's the ta.rsi() signature?"** — exact API term → resolve_topic
```
resolve_topic("ta.rsi")
  → reference/functions/ta.md (LARGE_DOCS)
list_sections("reference/functions/ta.md")
  → find "## ta.rsi()"
get_section("reference/functions/ta.md", "ta.rsi()")
```

**"Color bars based on volume"** — natural language → use manifest sections above
```
get_doc("visuals/bar_coloring.md")   ← Visuals section: barcolor()
get_doc("reference/variables.md")    ← API Reference section: volume
```

**"Write a trailing stop strategy"** — natural language → manifest + search
```
list_sections("reference/functions/strategy.md")   ← Function Reference section
  → find "## strategy.exit()"
get_section("reference/functions/strategy.md", "strategy.exit()")
get_doc("concepts/execution_model.md")             ← Concepts section
```

**"How does request.security work?"** — exact API term → resolve_topic
```
resolve_topic("request.security")
  → reference/functions/request.md (read_with: concepts/timeframes.md)
get_doc("reference/functions/request.md")
get_doc("concepts/timeframes.md")
```

**"How do I format numbers in a table?"** — natural language → search + manifest
```
search_docs("str.format")              ← find exact usage lines
get_section("reference/functions/general.md", "str.format()")
get_doc("visuals/tables.md")           ← Visuals section: tables
```

**"What does repainting mean?"** — exact Pine Script term → resolve_topic
```
resolve_topic("repainting")
  → concepts/timeframes.md
get_doc("concepts/timeframes.md")
```

**"How do I prevent repainting in a higher timeframe strategy?"** — needs both concept + function docs
```
resolve_topic("repainting")
  → concepts/timeframes.md
resolve_topic("request.security")
  → reference/functions/request.md (read_with: concepts/timeframes.md)
get_doc("concepts/timeframes.md")               ← lookahead warnings, calc_on_every_tick
get_section("reference/functions/request.md", "request.security()")  ← non-repainting pattern
```

**"What's the difference between var and varip?"** — varip is exact → resolve_topic
```
resolve_topic("varip")
  → concepts/execution_model.md
get_doc("concepts/execution_model.md")
```