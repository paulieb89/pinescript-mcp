# Pine Script v5 to v6 Migration Guide

## Version Declaration

```pine
// v5
//@version=5

// v6
//@version=6
```

## Renamed Functions

| v5 | v6 | Notes |
|---|---|---|
| `study()` | `indicator()` | Direct rename, same parameters |
| `security()` | `request.security()` | Moved to `request` namespace |
| `tickerid()` | `ticker.new()` | Moved to `ticker` namespace |
| `hline()` | Still `hline()` | Unchanged, but prefer `plot()` with `style=plot.style_line` |

## Type System Changes

### Explicit Type Qualifiers

v6 is stricter about `series` vs `simple` vs `const` qualifiers:

```pine
// v5: implicit type coercion was more lenient
length = input.int(14)

// v6: input values are `input int`, not `simple int`
// Functions requiring `simple` may reject `input` values
```

### New Type Keywords

- `type` keyword for User-Defined Types (UDTs)
- `method` keyword for declaring methods on types
- `export` for library functions

```pine
//@version=6
type PriceLevel
    float price
    string label
    color clr = color.gray

method toString(PriceLevel this) =>
    str.format("{0}: {1}", this.label, this.price)
```

## New v6 Features

### User-Defined Types (UDTs)

```pine
type Signal
    string direction
    float entry
    float stopLoss
    float takeProfit
```

### Methods

```pine
method isLong(Signal this) =>
    this.direction == "long"

method riskReward(Signal this) =>
    math.abs(this.takeProfit - this.entry) / math.abs(this.entry - this.stopLoss)
```

### Objects

```pine
var mySignal = Signal.new(
    direction = "long",
    entry = close,
    stopLoss = low,
    takeProfit = high
)
```

### Enum Inputs

```pine
// v6 adds input.enum() for typed enum selections
// Note: cannot use const string constants (shape.*, size.*, etc.)
// Use input.string(options=[...]) for string-based selections
```

## Deprecated Patterns

### `var` with Reassignment

```pine
// v5: var could be reassigned freely
var float myVar = na
myVar := close

// v6: same behavior, but prefer varip for per-bar persistent state
varip float tickCounter = 0
tickCounter += 1
```

### Direct `na` Comparison

```pine
// v5: sometimes worked
if myValue == na

// v6: must use na() function
if na(myValue)
```

### Legacy Color Syntax

```pine
// v5: some legacy color constants
color.lime, color.navy

// v6: use color.rgb() or color.new() for custom colors
myColor = color.new(color.green, 50)
```

## Common Migration Errors

| Error | Cause | Fix |
|---|---|---|
| `Undeclared identifier 'study'` | `study()` removed in v6 | Replace with `indicator()` |
| `Undeclared identifier 'security'` | `security()` removed in v6 | Replace with `request.security()` |
| `Cannot compare to na` | Direct `na` comparison | Use `na(value)` function |
| `Type mismatch: series/simple` | Stricter type qualifiers | Check function parameter requirements |
| `input.enum cannot use const string` | Using `shape.*`, `size.*` with `input.enum()` | Use `input.string(options=[...])` instead |

## Migration Checklist

1. Update `//@version=5` to `//@version=6`
2. Replace `study()` with `indicator()`
3. Replace `security()` with `request.security()`
4. Replace `== na` / `!= na` with `na()` / `not na()`
5. Check for deprecated function names (use `validate_function` tool)
6. Review type qualifier warnings
7. Consider adopting UDTs for complex data structures
8. Consider adopting methods for cleaner code organization
