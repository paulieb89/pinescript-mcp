# Pine Script v6 — Authoring Checklist

A condensed reference for the gotchas that cause Pine v6 scripts to fail compilation or repaint silently. Read this once per session, consult on demand.

## 1. Version annotation

| Rule | Detail |
|------|--------|
| Required first line | `//@version=6` |
| Allowed values | Only `6`. Not `5`, not `4`. |
| Position | First non-blank, non-comment line of the file. |
| Common mistake | Copying a v5 example that begins `//@version=5` — must be updated. |

## 2. Script-type declaration

Exactly one of these must appear on the second non-blank line.

| Declaration | When to use | Required args |
|-------------|-------------|---------------|
| `indicator(...)` | Visualisations, oscillators, screeners, signal plotters | `title` |
| `strategy(...)` | Anything that simulates orders, P&L, position management | `title` |
| `library(...)` | Reusable function libraries | `title` |

**Do not** use `study(...)`. That is v3/v4 syntax. The MCP server's `KNOWN_REPLACEMENTS` map flags it.

### Common args (named where optional)

- `title` — string. Required.
- `shorttitle` — string. Optional but recommended.
- `overlay` — `true` to draw on the price chart, `false` for a separate pane. Default `false`.
- `format` — `format.price`, `format.percent`, `format.volume`, etc.
- `precision` — int. Decimal places for plotted values.
- `max_lines_count`, `max_labels_count`, `max_boxes_count` — increase if drawing many objects (default 50, max 500).

Strategies additionally take:

- `initial_capital` — float, e.g. `10000`.
- `default_qty_type` — `strategy.fixed`, `strategy.cash`, `strategy.percent_of_equity`.
- `default_qty_value` — numeric.
- `commission_type`, `commission_value`, `slippage`, `process_orders_on_close`, `calc_on_every_tick`.

## 3. Named-argument calling convention

Pine v6 requires named arguments for most non-positional parameters. Positional-only calls beyond the first argument or two produce compile errors.

```pine
// CORRECT
plot(rsi, title="RSI", color=color.purple, linewidth=2)
request.security(syminfo.tickerid, "D", close, lookahead=barmerge.lookahead_off)

// WRONG
plot(rsi, "RSI", color.purple, 2)
```

## 4. v5 → v6 renames and removals

From the server's `KNOWN_REPLACEMENTS` map and the migration doc:

| v4/v5 | v6 replacement | Notes |
|-------|----------------|-------|
| `study(...)` | `indicator(...)` | Renamed in v5. Common copy-paste trap. |
| `security(...)` | `request.security(...)` | Moved into the `request.*` namespace. |
| `ta.adx(...)` | `ta.dmi(diLen, adxSmoothing)` | `ta.adx` does not exist. `ta.dmi` returns a tuple `[diPlus, diMinus, adx]`. |
| `ta.sum(...)` | `math.sum(source, length)` | `ta.sum` does not exist. |
| bare `input(...)` | `input.int`, `input.float`, `input.bool`, `input.string`, `input.source`, `input.timeframe`, `input.color`, `input.symbol`, `input.session`, `input.price` | Bare `input()` still compiles but typed variants are the v6 style. |

If you suspect a function may be renamed, call `validate_function` — that is the canonical source.

## 5. Type system — qualifiers and types

Pine has two orthogonal axes: **qualifier** and **type**.

| Qualifier | Meaning |
|-----------|---------|
| `const` | Compile-time constant. |
| `input` | Set once at chart load from an `input.*` call. |
| `simple` | Set once at script start, never changes per bar. |
| `series` | May change every bar. Default for most variables. |

Qualifier ordering, weakest to strongest: `series` > `input` > `simple` > `const`. Functions that require `simple` arguments (e.g. `request.security`'s `timeframe`) will reject a `series` value.

| Type | Examples |
|------|----------|
| `int` | `length = 14` |
| `float` | `rsi = ta.rsi(close, 14)` |
| `bool` | `isLong = close > ta.sma(close, 50)` |
| `string` | `tf = "5"` |
| `color` | `color.red`, `#00FF00`, `color.new(color.blue, 50)` |
| `label`, `line`, `box`, `table`, `linefill`, `chart.point` | Drawing object handles. |
| `array<T>`, `matrix<T>`, `map<K,V>` | Collections. |

Declare types explicitly when the inferred type might be wrong:

```pine
float upperBand = na
var array<float> closes = array.new<float>()
```

## 6. `var` and `varip` semantics

| Keyword | Behaviour |
|---------|-----------|
| (no qualifier) | Re-evaluates every bar. Resets on each bar. |
| `var` | Initialised once on the first bar; value persists across bars. |
| `varip` | Like `var`, but updates intra-bar (every tick) in real time. Use sparingly — script becomes non-deterministic during the realtime bar. |

```pine
var int barCount = 0
barCount += 1  // increments once per bar, persists
```

## 7. Repainting and `request.security`

The single biggest source of bug reports.

| Pattern | Repaints? | Recommendation |
|---------|-----------|----------------|
| `request.security(sym, tf, close)` on a higher TF | Yes, until bar closes | Use `barstate.isconfirmed` checks or read the closed value. |
| `request.security(sym, tf, close[1], lookahead=barmerge.lookahead_on)` | No, but introduces future leak risk | Only use with `[1]` to read the previous closed bar's value safely. |
| `request.security(sym, tf, close, lookahead=barmerge.lookahead_off)` | Yes in real time, no on historical | Default and safest pattern. |

Rule of thumb: `lookahead=barmerge.lookahead_on` is only safe when paired with `[1]`-shifted source values. Otherwise it leaks future data into history.

## 8. Alert hygiene

```pine
alertcondition(crossOver and barstate.isconfirmed,
     title="Crossover",
     message="Price crossed above SMA")
```

- Gate `alertcondition` on `barstate.isconfirmed` to avoid intra-bar flicker.
- `alert()` (function call) fires once per evaluation — gate similarly.

## 9. NA handling

- `na` is Pine's null. Most arithmetic with `na` propagates `na`.
- Use `nz(x, fallback)` to coerce `na` to a numeric default.
- Use `na(x)` to test for nullness.

## 10. Drawing objects — buffer limits

- Default max per script: 50 of each (lines, labels, boxes, polylines).
- Raise via `indicator(max_labels_count=500, max_lines_count=500, max_boxes_count=500)`.
- Max is 500. Beyond that you must delete older objects (`label.delete`, `line.delete`).

## 11. Plotting tips

- `plot(series, title, color, linewidth, style)` — primary plotting function.
- `plot(na)` to leave a gap.
- `plotshape(condition, location=location.abovebar, style=shape.triangledown, color=color.red)` for discrete signals.
- `bgcolor(color.new(color.green, 90))` for translucent zones — second arg of `color.new` is transparency 0–100.

## 12. Pre-emit checklist

Run through this list mentally before validating function calls:

- [ ] `//@version=6` on line 1.
- [ ] `indicator(...)` or `strategy(...)` on line 2 (or 3 if line 2 is blank).
- [ ] No `study(...)`, no bare `security(...)`, no `ta.adx(...)`, no `ta.sum(...)`.
- [ ] All `input.*` calls use typed variants.
- [ ] Named arguments used for all optional parameters.
- [ ] `request.security` calls have explicit `lookahead=` if accuracy matters.
- [ ] Alert conditions gated on `barstate.isconfirmed`.
- [ ] Drawing object counts bumped if the script will create many.
