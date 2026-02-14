# Pine Script v6 Compact Reference (for LLM validation)

## Version & Declarations
- ALWAYS `//@version=6` — v6 IS the current public version on TradingView
- Every script needs exactly ONE of: `indicator()`, `strategy()`, `library()`
- `study()` was removed in v4+. Use `indicator()`.

## Types
bool, int, float, string, color, array, matrix, map, box, label, line, linefill, polyline, table, chart.point, enum

## Type Qualifiers
- `const` — compile-time constant
- `input` — set via Settings/Inputs, constant at runtime
- `simple` — known at bar 0, constant across bars
- `series` — can change bar-to-bar (most variables)

## Keywords
var, varip, if, else, for, for...in, while, switch, import, export, method, type, enum, true, false, na, and, or, not

## Declaration Modes
- `var` — initialize once (bar 0), persist across bars
- `varip` — persist across bars AND intrabar ticks (realtime only)
- No keyword — re-declare every bar

## Valid Namespaces & Function Count
- `ta.*` (50): sma, ema, rsi, macd, atr, stoch, crossover, crossunder, change, highest, lowest, bb, cci, vwap, supertrend, etc.
- `strategy.*` (30+): entry, exit, close, close_all, cancel, order, risk.*, closedtrades.*, opentrades.*, convert_to_account, default_entry_qty
- `request.*` (9): security, security_lower_tf, currency_rate, dividends, earnings, economic, financial, seed, splits
- `input.*` (13): int, float, string, bool, color, source, session, symbol, timeframe, time, price, text_area, enum
- `math.*` (25): abs, max, min, round, floor, ceil, sqrt, pow, log, avg, sum, random, round_to_mintick, sign, etc.
- `str.*` (18): tostring, tonumber, contains, format, format_time, length, substring, replace, replace_all, split, match, etc.
- `array.*` (40+): new, from, get, set, push, pop, size, sort, includes, avg, min, max, sum, etc.
- `matrix.*` (40+): new, get, set, rows, columns, add_row, add_col, mult, inv, det, etc.
- `map.*` (9): new, get, put, contains, keys, values, remove, size, clear
- `color.*` (7): new, rgb, r, g, b, t, from_gradient
- `table.*` (18): new, cell, delete, clear, merge_cells, set_bgcolor, cell_set_text, cell_set_bgcolor, etc.
- `label.*` (15): new, delete, copy, set_text, set_xy, set_color, set_style, set_point, etc.
- `line.*` (15): new, delete, copy, set_xy1, set_xy2, get_price, set_color, set_style, etc.
- `box.*` (20): new, delete, copy, set_top, set_bottom, set_bgcolor, set_text, etc.
- `ticker.*` (8): new, modify, heikinashi, inherit, standard, kagi, linebreak, renko, pointfigure
- `log.*` (3): info, warning, error
- `runtime.*` (1): error
- `chart.point.*` (5): new, from_index, from_time, now, copy
- `polyline.*` (2): new, delete
- `linefill.*` (4): new, delete, get_line1, get_line2
- `timeframe.*` (3): change, in_seconds, from_seconds
- `syminfo.*` (2 functions): prefix, ticker

## Top-level Functions
alert, alertcondition, barcolor, bgcolor, fill, fixnan, hline, na, nz, plot, plotarrow, plotbar, plotcandle, plotchar, plotshape, time, time_close, timestamp, year, month, dayofmonth, dayofweek, hour, minute, second, weekofyear, max_bars_back

## Built-in Variables (commonly used)
- Price: open, high, low, close, hl2, hlc3, ohlc4, volume
- Bar: bar_index, last_bar_index, barstate.isconfirmed, barstate.isfirst, barstate.islast, barstate.isnew, barstate.isrealtime, barstate.ishistory, barstate.islastconfirmedhistory
- Symbol: syminfo.tickerid, syminfo.ticker, syminfo.prefix, syminfo.timezone, syminfo.currency, syminfo.basecurrency, syminfo.type, syminfo.mintick, syminfo.pointvalue, syminfo.isin
- Time: time, time_close, timenow, timeframe.period, timeframe.multiplier
- Chart: chart.fg_color, chart.bg_color, chart.is_standard, chart.is_heikinashi
- Strategy: strategy.position_size, strategy.position_avg_price, strategy.equity, strategy.openprofit, strategy.netprofit, strategy.closedtrades, strategy.opentrades, strategy.long, strategy.short

## Constants (commonly used)
- barmerge: gaps_off, gaps_on, lookahead_off, lookahead_on
- strategy.commission: percent, cash_per_contract, cash_per_order
- strategy.direction: long, short, all
- format: mintick, price, percent, volume
- position: top_left, top_center, top_right, middle_left, middle_center, middle_right, bottom_left, bottom_center, bottom_right
- size: auto, tiny, small, normal, large, huge
- color: aqua, black, blue, fuchsia, gray, green, lime, maroon, navy, olive, orange, purple, red, silver, teal, white, yellow
- plot.style: line, stepline, histogram, cross, area, columns, circles, linebr, areabr, stepline_diamond
- label.style: label_left, label_right, label_up, label_down, none, etc.
- line.style: solid, dotted, dashed, arrow_left, arrow_right, arrow_both
- xloc: bar_index, bar_time
- yloc: price, abovebar, belowbar
- location: abovebar, belowbar, top, bottom, absolute
- shape: xcross, cross, triangleup, triangledown, flag, circle, arrowup, arrowdown, square, diamond, labelup, labeldown

## strategy() Declaration — Full Parameter Reference
```
strategy(title, shorttitle, overlay, format, precision, scale, pyramiding,
         calc_on_order_fills, calc_on_every_tick, max_bars_back,
         backtest_fill_limits_assumption, default_qty_type, default_qty_value,
         initial_capital, currency, slippage, commission_type, commission_value,
         process_orders_on_close, close_entries_rule, margin_long, margin_short,
         explicit_plot_zorder, max_lines_count, max_labels_count, max_boxes_count,
         risk_free_rate, use_bar_magnifier, fill_orders_on_standard_ohlc,
         max_polylines_count)
```

### Key Parameters & Valid Values
| Parameter | Type | Valid Values / Notes |
|-----------|------|---------------------|
| `title` | `const string` | Required. Script name shown in UI |
| `overlay` | `const bool` | `true` = on price chart, `false` = separate pane |
| `initial_capital` | `const int/float` | Starting equity for backtesting (e.g., `100000`) |
| `default_qty_type` | `const string` | `strategy.fixed`, `strategy.cash`, `strategy.percent_of_equity` |
| `default_qty_value` | `const int/float` | Qty per trade (units depend on `default_qty_type`) |
| `pyramiding` | `const int` | Max simultaneous entries in same direction (0 = no pyramiding) |
| `commission_type` | `const string` | `strategy.commission.percent`, `strategy.commission.cash_per_contract`, `strategy.commission.cash_per_order` |
| `commission_value` | `const int/float` | Commission amount |
| `slippage` | `const int` | Ticks of slippage per fill |
| `margin_long` | `const int/float` | Margin % for longs (e.g., `5` = 5% margin = 20:1 leverage) |
| `margin_short` | `const int/float` | Margin % for shorts |
| `process_orders_on_close` | `const bool` | `true` = fill at bar close, `false` = fill at next bar open |
| `calc_on_every_tick` | `const bool` | `true` = recalc on every tick (realtime only) |
| `calc_on_order_fills` | `const bool` | `true` = recalc after each fill |
| `use_bar_magnifier` | `const bool` | `true` = use intrabar data for more accurate fills |
| `close_entries_rule` | `const string` | `"FIFO"` or `"ANY"` |
| `currency` | `const string` | `currency.USD`, `currency.EUR`, etc. |

### Strategy Sizing Gotchas
- `strategy.percent_of_equity` with 100% on **futures** will fail silently if notional > capital (e.g., 1 NQ contract ≈ $500K notional vs $25K capital → 0 trades)
- `strategy.fixed` with `default_qty_value=1` is safest for futures backtesting
- `strategy.cash` sizes by dollar amount — works across instruments but qty rounds down
- Always set `margin_long`/`margin_short` for futures (typical: 5–15%)
- TradingView Properties tab can **override** script defaults — click "Defaults" button to reset

## Type Qualifier Requirements (Common Functions)
| Function | Parameter | Required Qualifier | Common Mistake |
|----------|-----------|-------------------|----------------|
| `input.int()` | `defval` | `const int` | Using `bar_index` (series) |
| `input.int()` | `minval`, `maxval`, `step` | `const int` | — |
| `input.float()` | `defval` | `const float` | — |
| `input.float()` | `minval`, `maxval`, `step` | `const float` | Using `syminfo.mintick` (simple) |
| `input.string()` | `defval` | `const string` | — |
| `input.string()` | `options` | `tuple of const string` | Dynamic array of strings |
| `input.session()` | `defval` | `const string` | — |
| `input.timeframe()` | `defval` | `const string` | — |
| `plot()` | `title` | `const string` | `"RSI " + input.timeframe()` (input string) |
| `hline()` | `title` | `const string` | Same as plot |
| `alertcondition()` | `title`, `message` | `const string` | String concatenation with inputs |
| `indicator()` | `title` | `const string` | — |
| `strategy()` | `title` | `const string` | — |
| `strategy()` | ALL params | `const` | See table above |
| `strategy.entry()` | `id` | `const string` | — |
| `strategy.entry()` | `direction` | `const` | `strategy.long` or `strategy.short` |
| `strategy.entry()` | `qty` | `simple int/float` | OK to use `input.int()` result |
| `strategy.entry()` | `limit`, `stop` | `series float` | OK — can change per bar |
| `strategy.exit()` | `id`, `from_entry` | `const string` | — |
| `strategy.exit()` | `stop`, `limit`, `trail_*` | `series float` | OK — can change per bar |
| `request.security()` | `symbol` | `simple string` | — |
| `request.security()` | `timeframe` | `simple string` | — |
| `request.security()` | `expression` | `series` | Any expression is fine |
| `ta.sma()` | `length` | `simple int` | Using `bar_index` (series) |
| `ta.ema()` | `length` | `simple int` | Same |
| `ta.rsi()` | `length` | `simple int` | Same |
| `ta.atr()` | `length` | `simple int` | Same |
| `color.new()` | `color` | `series color` | OK |
| `color.new()` | `transp` | `series int` | OK (0–100) |

### Qualifier Hierarchy (auto-cast upward only)
```
const → input → simple → series
```
A `const` can be used where `input` is required, `input` where `simple` is required, etc. But NOT the reverse — `series` cannot be used where `simple` is required.

## request.security() Signature
```
request.security(symbol, timeframe, expression, gaps, lookahead, ignore_invalid_symbol, currency, calc_bars_count)
```
- Use `barmerge.lookahead_off` to prevent repainting (default)
- `barmerge.lookahead_on` WITHOUT historical offset `[1]` = lookahead bias (BUG)
- Named args also valid: `gaps=barmerge.gaps_off, lookahead=barmerge.lookahead_off`

## Common Pitfalls
- `plot()`, `hline()`, `alertcondition()` require `const string` for `title` — cannot use `input string` concatenation (e.g., `"RSI " + tf` where `tf` is from `input.timeframe()` is INVALID)
- `input.*()` requires `const` values for `minval`, `maxval`, `step` — `syminfo.mintick` is `simple float` and CANNOT be used (use a literal like `0.01` instead)
- `ta.crossover()`, `ta.crossunder()`, `ta.change()` etc. must be called in global scope (not inside `if` blocks or conditional expressions) — they depend on per-bar history and will produce inconsistent results if skipped on some bars
- `ta.crossover(close, level)` requires `close[1] <= level` — wrong for level-break strategies (ORB, support/resistance) where price may already be at the level. Use `close > level` with a one-shot flag instead
- `alertcondition()` only works in `indicator()` scripts — strategies must use `alert()` with `alert.freq_once_per_bar_close`
- `study()` does not exist in v6 — use `indicator()`
- `security()` does not exist — use `request.security()`
- `input()` without namespace works but prefer `input.int()`, `input.float()`, etc.
- `barstate.isconfirmed` inside `request.security()` expression is unreliable
- `var` resets on `strategy.close_all()` — use `varip` if needed across trades
- String concatenation: use `+` operator or `str.format()`
- No `format.currency` constant — use `format.mintick` or manual "$" + str.tostring()
- `chart.fg_color` IS valid in v6 (added 2025)
- `na()` and `nz()` do NOT accept `series bool` — they only work with numeric types. To safely check a previous bool value: use `myBool[1] == true ? true : false` instead of `nz(myBool[1], false)` or `na(myBool[1])`
- `input.enum()` does NOT work with `position.*`, `size.*`, or other `const string` built-in constants — use `input.string()` with `options=[...]` instead
- User-defined functions cannot have return type keywords like `string f() =>` or `int f() =>` — just use `f() =>` and let Pine infer the type
- Cannot compare a value to `na` directly (`x != na` is INVALID). Use `na()` function instead: `not na(x)` or `na(x)`
- `strategy.exit()` `stop=` and `limit=` values **recalculate every bar**. If you compute `stop=entry - atrMult * ta.atr(14)`, the stop drifts as ATR changes. Freeze stop/target at entry using `var float frozenStop = na` and set it on the entry bar only
- `ta.adx()` does NOT exist. Use `ta.dmi(diLen, adxSmoothing)` which returns `[diPlus, diMinus, adx]` as a tuple
- `ta.sum()` does NOT exist. Use `math.sum(source, length)` instead
