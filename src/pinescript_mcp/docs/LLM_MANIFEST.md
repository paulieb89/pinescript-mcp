# Pine Script v6 Documentation Manifest

**Purpose:** This file is a directory map and tool guide for LLMs using the pinescript-mcp server. Read this first, then use the tools below to retrieve exactly the content you need.

---

## How to Use These Tools

Follow this decision tree for every Pine Script query:

1. **Start with `resolve_topic(query)`** — natural language routing to the right doc(s). Returns ranked matches with `read_with` companion hints and a `suggestion` field telling you the next step.

2. **For large files** (`ta.md`, `strategy.md`, `collections.md`, `drawing.md`, `general.md`):
   - `list_sections(path)` → see all headers
   - `get_section(path, header)` → read just the section you need
   - Never load these files whole with `get_doc` — they are 1000–2800 lines.

3. **For small files** → `get_doc(path)` to read the whole thing directly.

4. **For exact function/syntax lookup** → `search_docs(query)` greps across all docs. Use this when you know the function name (e.g. `"str.format"`, `"strategy.exit"`).

5. **To validate a function name** → `validate_function(fn_name)` checks if a function exists and suggests the closest match if not.

6. **To list functions by namespace** → `get_functions(namespace)` (e.g. `"ta"`, `"strategy"`, `"array"`).

7. **To check Pine Script syntax** → `lint_script(script)` — fast static analysis, no API cost.

**Efficient pattern for most queries:**
```
resolve_topic(query)
  → if LARGE_DOCS: list_sections(path) → get_section(path, header)
  → if small file: get_doc(path)
  → if function lookup: search_docs(fn_name)
```

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

**"What's the RSI function signature?"**
```
resolve_topic("RSI")
  → ta.md (LARGE_DOCS)
list_sections("reference/functions/ta.md")
  → find "## ta.rsi()"
get_section("reference/functions/ta.md", "ta.rsi()")
```

**"Color bars based on volume"**
```
resolve_topic("color bars volume")
  → visuals/bar_coloring.md + reference/variables.md
get_doc("visuals/bar_coloring.md")   ← small file, read whole
get_doc("reference/variables.md")    ← for volume variable
```

**"Write a trailing stop strategy"**
```
resolve_topic("trailing stop strategy")
  → strategy.md (LARGE_DOCS, read_with: execution_model.md)
list_sections("reference/functions/strategy.md")
  → find "## strategy.exit()"
get_section("reference/functions/strategy.md", "strategy.exit()")
get_doc("concepts/execution_model.md")
```

**"Convert my v5 script to v6"**
```
resolve_topic("convert v5")
  → reference/migration_v5_to_v6.md
get_doc("reference/migration_v5_to_v6.md")
```

**"How do I format numbers in a table?"**
```
resolve_topic("format numbers table")
  → general.md (LARGE_DOCS) + tables
search_docs("str.format")              ← find exact usage lines
get_section("reference/functions/general.md", "str.format()")
get_doc("visuals/tables.md")
```

**"How do I prevent repainting in a higher timeframe strategy?"**
```
resolve_topic("repainting higher timeframe strategy")
  → concepts/timeframes.md + strategy.md (read_with: execution_model.md)
get_doc("concepts/timeframes.md")
get_section("reference/functions/strategy.md", "strategy.entry()")
```

**"What's the difference between var and varip?"**
```
resolve_topic("var varip")
  → concepts/execution_model.md
get_doc("concepts/execution_model.md")   ← small enough to read whole
```