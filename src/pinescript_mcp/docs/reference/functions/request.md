## request.currency_rate()

Provides a daily rate that can be used to convert a value expressed in the from currency to another in the to currency.

### Syntax
```
request.currency_rate(from, to, ignore_invalid_currency) → series float
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| from | series string | yes | — |
| to | series string | yes | — |
| ignore_invalid_currency | series bool | no | false |

### Remarks
If from and to arguments are equal, function returns 1. Please note that using this variable/function can cause indicator repainting.

### Code Example
```pine
//@version=6
indicator("Close in British Pounds")
rate = request.currency_rate(syminfo.currency, "GBP")
plot(close * rate)
```

---

## request.dividends()

Requests dividends data for the specified symbol.

### Syntax
```
request.dividends(ticker, field, gaps, lookahead, ignore_invalid_symbol, currency) → series float
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| ticker | simple string | yes | — |
| field | simple string | no | dividends.gross |
| gaps | barmerge_gaps | no | barmerge.gaps_off |
| lookahead | barmerge_lookahead | no | barmerge.lookahead_off |
| ignore_invalid_symbol | simple bool | no | false |
| currency | simple string | no | syminfo.currency |

### Returns
Requested series, or n/a if there is no dividends data for the specified symbol.

### Code Example
```pine
//@version=6
indicator("request.dividends")
s1 = request.dividends("NASDAQ:BELFA")
plot(s1)
s2 = request.dividends("NASDAQ:BELFA", dividends.net, gaps=barmerge.gaps_on, lookahead=barmerge.lookahead_on)
plot(s2)
```

---

## request.earnings()

Requests earnings data for the specified symbol.

### Syntax
```
request.earnings(ticker, field, gaps, lookahead, ignore_invalid_symbol, currency) → series float
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| ticker | simple string | yes | — |
| field | simple string | no | earnings.actual |
| gaps | barmerge_gaps | no | barmerge.gaps_off |
| lookahead | barmerge_lookahead | no | barmerge.lookahead_off |
| ignore_invalid_symbol | simple bool | no | false |
| currency | simple string | no | syminfo.currency |

### Returns
Requested series, or n/a if there is no earnings data for the specified symbol.

### Code Example
```pine
//@version=6
indicator("request.earnings")
s1 = request.earnings("NASDAQ:BELFA")
plot(s1)
s2 = request.earnings("NASDAQ:BELFA", earnings.actual, gaps=barmerge.gaps_on, lookahead=barmerge.lookahead_on)
plot(s2)
```

---

## request.economic()

Requests economic data for a symbol. Economic data includes information such as the state of a country's economy (GDP, inflation rate, etc.) or of a particular industry (steel production, ICU beds, etc.).

### Syntax
```
request.economic(country_code, field, gaps, ignore_invalid_symbol) → series float
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| country_code | series string | yes | — |
| field | series string | yes | — |
| gaps | barmerge_gaps | no | barmerge.gaps_off |
| ignore_invalid_symbol | series bool | no | false |

### Returns
Requested series.

### Remarks
Economic data can also be accessed from charts, just like a regular symbol. Use "ECONOMIC" as the exchange name and {country_code}{field} as the ticker. The name of US GDP data is thus "ECONOMIC:USGDP".

### Code Example
```pine
//@version=6
indicator("US GDP")
e = request.economic("US", "GDP")
plot(e)
```

---

## request.financial()

Requests financial series for symbol.

### Syntax
```
request.financial(symbol, financial_id, period, gaps, ignore_invalid_symbol, currency) → series float
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| symbol | series string | yes | — |
| financial_id | series string | yes | — |
| period | series string | yes | — |
| gaps | barmerge_gaps | no | barmerge.gaps_off |
| ignore_invalid_symbol | series bool | no | false |
| currency | series string | no | syminfo.currency |

### Returns
Requested series.

### Code Example
```pine
//@version=6
indicator("request.financial")
f = request.financial("NASDAQ:MSFT", "ACCOUNTS_PAYABLE", "FY")
plot(f)
```

---

## request.quandl()

Note: This function has been deprecated due to the API change from NASDAQ Data Link. Requests for "QUANDL" symbols are no longer valid and requests for them return a runtime error.

### Syntax
```
request.quandl(ticker, gaps, index, ignore_invalid_symbol) → series float
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| ticker | simple string | yes | — |
| gaps | barmerge_gaps | no | barmerge.gaps_off |
| index | simple int | no | 0 |
| ignore_invalid_symbol | simple bool | no | false |

### Returns
Requested series.

### Code Example
```pine
//@version=6
indicator("request.quandl")
f = request.quandl("CFTC/SB_FO_ALL", barmerge.gaps_off, 0)
plot(f)
```

---

## request.security()

Requests the result of an expression from a specified context (symbol and timeframe).

### Syntax
```
request.security(symbol, timeframe, expression, gaps, lookahead, ignore_invalid_symbol, currency, calc_bars_count) → series <type>
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| symbol | series string | yes | — |
| timeframe | series string | yes | — |
| expression | <any type> | yes | — |
| gaps | barmerge_gaps | no | barmerge.gaps_off |
| lookahead | barmerge_lookahead | no | barmerge.lookahead_off |
| ignore_invalid_symbol | series bool | no | false |
| currency | series string | no | syminfo.currency |
| calc_bars_count | series int | no | — |

### Returns
A result determined by expression.

### Remarks
Scripts using this function might calculate differently on historical and realtime bars, leading to repainting. A single script can contain no more than 40 unique request.*() function calls. A call is unique only if it does not call the same function with the same arguments. When using two calls to a request.*() function to evaluate the same expression from the same context with different calc_bars_count values, the second call requests the same number of historical bars as the first. For example, if a script calls request.security("AAPL", "", close, calc_bars_count = 3) after it calls request.security("AAPL", "", close, calc_bars_count = 5), the second call also uses five bars of historical data, not three. The symbol of a request.() call can be inherited if it is not specified precisely, i.e., if the symbol argument is an empty string or syminfo.tickerid. Similarly, the timeframe of a request.() call can be inherited if the timeframe argument is an empty string or timeframe.period. These values are normally taken from the chart on which the script is running. However, if request.*() function A is called from within the expression of request.*() function B, then function A can inherit the values from function B. See here for more information.

### Code Example
```pine
//@version=6
indicator("Simple `request.security()` calls")
// Returns 1D close of the current symbol.
dailyClose = request.security(syminfo.tickerid, "1D", close)
plot(dailyClose)

// Returns the close of "AAPL" from the same timeframe as currently open on the chart.
aaplClose = request.security("AAPL", timeframe.period, close)
plot(aaplClose)

//@version=6
indicator("Advanced `request.security()` calls")
// This calculates a 10-period moving average on the active chart.
sma = ta.sma(close, 10)
// This sends the `sma` calculation for execution in the context of the "AAPL" symbol at a "240" (4 hours) timeframe.
aaplSma = request.security("AAPL", "240", sma)
plot(aaplSma)

// To avoid differences on historical and realtime bars, you can use this technique, which only returns a value from the higher timeframe on the bar after it completes:
indexHighTF = barstate.isrealtime ? 1 : 0
indexCurrTF = barstate.isrealtime ? 0 : 1
nonRepaintingClose = request.security(syminfo.tickerid, "1D", close[indexHighTF])[indexCurrTF]
plot(nonRepaintingClose, "Non-repainting close")

// Returns the 1H close of "AAPL", extended session included. The value is dividend-adjusted.
extendedTicker = ticker.modify("NASDAQ:AAPL", session = session.extended, adjustment = adjustment.dividends)
aaplExtAdj = request.security(extendedTicker, "60", close)
plot(aaplExtAdj)

// Returns the result of a user-defined function.
// The `max` variable is mutable, but we can pass it to `request.security()` because it is wrapped in a function.
allTimeHigh(source) =>
    var max = source
    max := math.max(max, source)
allTimeHigh1D = request.security(syminfo.tickerid, "1D", allTimeHigh(high))

// By using a tuple `expression`, we obtain several values with only one `request.security()` call.
[open1D, high1D, low1D, close1D, ema1D] = request.security(syminfo.tickerid, "1D", [open, high, low, close, ta.ema(close, 10)])
plotcandle(open1D, high1D, low1D, close1D)
plot(ema1D)

// Returns an array containing the OHLC values of the chart's symbol from the 1D timeframe.
ohlcArray = request.security(syminfo.tickerid, "1D", array.from(open, high, low, close))
plotcandle(array.get(ohlcArray, 0), array.get(ohlcArray, 1), array.get(ohlcArray, 2), array.get(ohlcArray, 3))
```

---

## request.security_lower_tf()

Requests the results of an expression from a specified symbol on a timeframe lower than or equal to the chart's timeframe. It returns an array containing one element for each lower-timeframe bar within the chart bar. On a 5-minute chart, requesting data using a timeframe argument of "1" typically returns an array with five elements representing the value of the expression on each 1-minute bar, ordered by time with the earliest value first.

### Syntax
```
request.security_lower_tf(symbol, timeframe, expression, ignore_invalid_symbol, currency, ignore_invalid_timeframe, calc_bars_count) → array<type>
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| symbol | series string | yes | — |
| timeframe | series string | yes | — |
| expression | <any type> | yes | — |
| ignore_invalid_symbol | series bool | no | false |
| currency | series string | no | syminfo.currency |
| ignore_invalid_timeframe | series bool | no | false |
| calc_bars_count | series int | no | — |

### Returns
An array of a type determined by expression, or a tuple of these.

### Remarks
Scripts using this function might calculate differently on historical and realtime bars, leading to repainting. Please note that spreads (e.g., "AAPL+MSFT*TSLA") do not always return reliable data with this function. A single script can contain no more than 40 unique request.*() function calls. A call is unique only if it does not call the same function with the same arguments. When using two calls to a request.*() function to evaluate the same expression from the same context with different calc_bars_count values, the second call requests the same number of historical bars as the first. For example, if a script calls request.security("AAPL", "", close, calc_bars_count = 3) after it calls request.security("AAPL", "", close, calc_bars_count = 5), the second call also uses five bars of historical data, not three. The symbol of a request.() call can be inherited if it is not specified precisely, i.e., if the symbol argument is an empty string or syminfo.tickerid. Similarly, the timeframe of a request.() call can be inherited if the timeframe argument is an empty string or timeframe.period. These values are normally taken from the chart that the script is running on. However, if request.*() function A is called from within the expression of request.*() function B, then function A can inherit the values from function B. See here for more information.

### Code Example
```pine
//@version=6
indicator("`request.security_lower_tf()` Example", overlay = true)

// If the current chart timeframe is set to 120 minutes, then the `arrayClose` array will contain two 'close' values from the 60 minute timeframe for each bar.
arrClose = request.security_lower_tf(syminfo.tickerid, "60", close)

if bar_index == last_bar_index - 1
    label.new(bar_index, high, str.tostring(arrClose))
```

---

## request.seed()

Requests data from a user-maintained GitHub repository and returns it as a series. An in-depth tutorial on how to add new data can be found here.

### Syntax
```
request.seed(source, symbol, expression, ignore_invalid_symbol, calc_bars_count) → series <type>
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| source | series string | yes | — |
| symbol | series string | yes | — |
| expression | <any type> | yes | — |
| ignore_invalid_symbol | series bool | no | false |
| calc_bars_count | series int | no | — |

### Returns
Requested series or tuple of series, which may include array/matrix IDs.

### Code Example
```pine
//@version=6
indicator("BTC Development Activity")

[devAct, devActSMA] = request.seed("seed_crypto_santiment", "BTC_DEV_ACTIVITY", [close, ta.sma(close, 10)])

plot(devAct, "BTC Development Activity")
plot(devActSMA, "BTC Development Activity SMA10", color = color.yellow)
```

---

## request.splits()

Requests splits data for the specified symbol.

### Syntax
```
request.splits(ticker, field, gaps, lookahead, ignore_invalid_symbol) → series float
```

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| ticker | simple string | yes | — |
| field | simple string | no | splits.denominator |
| gaps | barmerge_gaps | no | barmerge.gaps_off |
| lookahead | barmerge_lookahead | no | barmerge.lookahead_off |
| ignore_invalid_symbol | simple bool | no | false |

### Returns
Requested series, or n/a if there is no splits data for the specified symbol.

### Code Example
```pine
//@version=6
indicator("request.splits")
s1 = request.splits("NASDAQ:BELFA", splits.denominator)
plot(s1)
s2 = request.splits("NASDAQ:BELFA", splits.denominator, gaps=barmerge.gaps_on, lookahead=barmerge.lookahead_on)
plot(s2)
```

---

