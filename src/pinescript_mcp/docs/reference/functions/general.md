
## alert()

Creates an alert trigger for an indicator or strategy, with a specified frequency, when called on the latest realtime bar. To activate alerts for a script containing calls to this function, open the "Create Alert" dialog box, then select the script name and "Any alert() function call" in the "Condition" section.

### Remarks
The alert() function does not display information on the chart. In contrast to alertcondition, calls to this function do not count toward a script's plot count. Additionally, alert() calls are allowed in local scopes, including the scopes of exported library functions. See this article in our Help Center to learn more about activating alerts from alert() calls.

### Code Example
```pine
//@version=6
indicator("`alert()` example", "", true)
ma = ta.sma(close, 14)
xUp = ta.crossover(close, ma)
if xUp
    // Trigger the alert the first time a cross occurs during the real-time bar.
    alert("Price (" + str.tostring(close) + ") crossed over MA (" + str.tostring(ma) + ").", alert.freq_once_per_bar)
plot(ma)
plotchar(xUp, "xUp", "▲", location.top, size = size.tiny)
```

---

## alertcondition()

Creates alert condition, that is available in Create Alert dialog. Please note, that alertcondition does NOT create an alert, it just gives you more options in Create Alert dialog. Also, alertcondition effect is invisible on chart.

### Remarks
Please note that an alertcondition call generates an additional plot. All such calls are taken into account when we calculate the number of the output series per script.

### Code Example
```pine
//@version=6
indicator("alertcondition", overlay=true)
alertcondition(close >= open, title='Alert on Green Bar', message='Green Bar!')
```

---

## bool()

Converts the x value to a bool value. Returns false if x is na, false, or an int/float value equal to 0. Returns true for all other possible values.

### Returns
The value of the argument after casting to bool.

---

## chart.point.copy()

Creates a copy of a chart.point object with the specified id.

---

## chart.point.from_index()

Returns a chart.point object with index as its x-coordinate and price as its y-coordinate.

### Remarks
The time field values of chart.point instances returned from this function will be na, meaning drawing objects with xloc values set to xloc.bar_time will not work with them.

---

## chart.point.from_time()

Returns a chart.point object with time as its x-coordinate and price as its y-coordinate.

### Remarks
The index field values of chart.point instances returned from this function will be na, meaning drawing objects with xloc values set to xloc.bar_index will not work with them.

---

## chart.point.new()

Creates a new chart.point object with the specified time, index, and price.

### Remarks
Whether a drawing object uses a point's time or index field as an x-coordinate depends on the xloc type used in the function call that returned the drawing. It's important to note that this function does not verify that the time and index values refer to the same bar.

---

## chart.point.now()

Returns a chart.point object with price as the y-coordinate

### Remarks
The chart.point instance returned from this function records values for its index and time fields on the bar it executed on, making it suitable for use with drawing objects of any xloc type.

---

## color()

Casts na to color

### Returns
The value of the argument after casting to color.

---

## color.b()

Retrieves the value of the color's blue component.

### Returns
The value (0 to 255) of the color's blue component.

### Code Example
```pine
//@version=6
indicator("color.b", overlay=true)
plot(color.b(color.blue))
```

---

## color.from_gradient()

Based on the relative position of value in the bottom_value to top_value range, the function returns a color from the gradient defined by bottom_color to top_color.

### Returns
A color calculated from the linear gradient between bottom_color to top_color.

### Remarks
Using this function will have an impact on the colors displayed in the script's "Settings/Style" tab. See the User Manual for more information.

### Code Example
```pine
//@version=6
indicator("color.from_gradient", overlay=true)
color1 = color.from_gradient(close, low, high, color.yellow, color.lime)
color2 = color.from_gradient(ta.rsi(close, 7), 0, 100, color.rgb(255, 0, 0), color.rgb(0, 255, 0, 50))
plot(close, color=color1)
plot(ta.rsi(close,7), color=color2)
```

---

## color.g()

Retrieves the value of the color's green component.

### Returns
The value (0 to 255) of the color's green component.

### Code Example
```pine
//@version=6
indicator("color.g", overlay=true)
plot(color.g(color.green))
```

---

## color.new()

Function color applies the specified transparency to the given color.

### Returns
Color with specified transparency.

### Remarks
Using arguments that are not constants (e.g., 'simple', 'input' or 'series') will have an impact on the colors displayed in the script's "Settings/Style" tab. See the User Manual for more information.

### Code Example
```pine
//@version=6
indicator("color.new", overlay=true)
plot(close, color=color.new(color.red, 50))
```

---

## color.r()

Retrieves the value of the color's red component.

### Returns
The value (0 to 255) of the color's red component.

### Code Example
```pine
//@version=6
indicator("color.r", overlay=true)
plot(color.r(color.red))
```

---

## color.rgb()

Creates a new color with transparency using the RGB color model.

### Returns
Color with specified transparency.

### Remarks
Using arguments that are not constants (e.g., 'simple', 'input' or 'series') will have an impact on the colors displayed in the script's "Settings/Style" tab. See the User Manual for more information.

### Code Example
```pine
//@version=6
indicator("color.rgb", overlay=true)
plot(close, color=color.rgb(255, 0, 0, 50))
```

---

## color.t()

Retrieves the color's transparency.

### Returns
The value (0-100) of the color's transparency.

### Code Example
```pine
//@version=6
indicator("color.t", overlay=true)
plot(color.t(color.new(color.red, 50)))
```

---

## dayofmonth()

### Returns
Day of month (in exchange timezone) for provided UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970. Note that this function returns the day based on the time of the bar's open. For overnight sessions (e.g. EURUSD, where Monday session starts on Sunday, 17:00 UTC-4) this value can be lower by 1 than the day of the trading day.

---

## dayofweek()

### Returns
Day of week (in exchange timezone) for provided UNIX time.

### Remarks
Note that this function returns the day based on the time of the bar's open. For overnight sessions (e.g. EURUSD, where Monday session starts on Sunday, 17:00) this value can be lower by 1 than the day of the trading day. UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970.

---

## fixnan()

For a given series replaces NaN values with previous nearest non-NaN value.

### Returns
Series without na gaps.

---

## float()

Casts na to float

### Returns
The value of the argument after casting to float.

---

## hour()

### Returns
Hour (in exchange timezone) for provided UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970.

---

## indicator()

This declaration statement designates the script as an indicator and sets a number of indicator-related properties.

### Remarks
Every indicator script must have one indicator call.

### Code Example
```pine
//@version=6
indicator("My script", shorttitle="Script")
plot(close)
```

---

## input()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function automatically detects the type of the argument used for 'defval' and uses the corresponding input widget.

### Returns
Value of input variable.

### Remarks
Result of input function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input", overlay=true)
i_switch = input(true, "On/Off")
plot(i_switch ? open : na)

i_len = input(7, "Length")
i_src = input(close, "Source")
plot(ta.sma(i_src, i_len))

i_border = input(142.50, "Price Border")
hline(i_border)
bgcolor(close > i_border ? color.green : color.red)

i_col = input(color.red, "Plot Color")
plot(close, color=i_col)

i_text = input("Hello!", "Message")
l = label.new(bar_index, high, text=i_text)
label.delete(l[1])
```

---

## input.bool()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a checkmark to the script's inputs.

### Returns
Value of input variable.

### Remarks
Result of input.bool function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.bool", overlay=true)
i_switch = input.bool(true, "On/Off")
plot(i_switch ? open : na)
```

---

## input.color()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a color picker that allows the user to select a color and transparency, either from a palette or a hex value.

### Returns
Value of input variable.

### Remarks
Result of input.color function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.color", overlay=true)
i_col = input.color(color.red, "Plot Color")
plot(close, color=i_col)
```

---

## input.enum()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a dropdown with options based on the enum fields passed to its defval and options parameters.

### Returns
Value of input variable.

### Remarks
All fields included in the defval and options arguments must belong to the same enum.

### Code Example
```pine
//@version=6
indicator("Session highlight", overlay = true)

//@enum        Contains fields with popular timezones as titles.
//@field exch  Has an empty string as the title to represent the chart timezone.
enum tz
    utc  = "UTC"
    exch = ""
    ny   = "America/New_York"
    chi  = "America/Chicago"
    lon  = "Europe/London"
    tok  = "Asia/Tokyo"

//@variable The session string.
selectedSession = input.session("1200-1500", "Session")
//@variable The selected timezone. The input's dropdown contains the fields in the `tz` enum.
selectedTimezone = input.enum(tz.utc, "Session Timezone")

//@variable Is `true` if the current bar's time is in the specified session.
bool inSession = false
if not na(time("", selectedSession, str.tostring(selectedTimezone)))
    inSession := true

// Highlight the background when `inSession` is `true`.
bgcolor(inSession ? color.new(color.green, 90) : na, title = "Active session highlight")
```

---

## input.float()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a field for a float input to the script's inputs.

### Returns
Value of input variable.

### Remarks
Result of input.float function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.float", overlay=true)
i_angle1 = input.float(0.5, "Sin Angle", minval=-3.14, maxval=3.14, step=0.02)
plot(math.sin(i_angle1) > 0 ? close : open, "sin", color=color.green)

i_angle2 = input.float(0, "Cos Angle", options=[-3.14, -1.57, 0, 1.57, 3.14])
plot(math.cos(i_angle2) > 0 ? close : open, "cos", color=color.red)
```

---

## input.int()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a field for an integer input to the script's inputs.

### Returns
Value of input variable.

### Remarks
Result of input.int function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.int", overlay=true)
i_len1 = input.int(10, "Length 1", minval=5, maxval=21, step=1)
plot(ta.sma(close, i_len1))

i_len2 = input.int(10, "Length 2", options=[5, 10, 21])
plot(ta.sma(close, i_len2))
```

---

## input.price()

Adds a price input to the script's "Settings/Inputs" tab. Using confirm = true activates the interactive input mode where a price is selected by clicking on the chart.

### Returns
Value of input variable.

### Remarks
When using interactive mode, a time input can be combined with a price input if both function calls use the same argument for their inline parameter.

### Code Example
```pine
//@version=6
indicator("input.price", overlay=true)
price1 = input.price(title="Date", defval=42)
plot(price1)

price2 = input.price(54, title="Date")
plot(price2)
```

---

## input.session()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds two dropdowns that allow the user to specify the beginning and the end of a session using the session selector and returns the result as a string.

### Returns
Value of input variable.

### Remarks
Result of input.session function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.session", overlay=true)
i_sess = input.session("1300-1700", "Session", options=["0930-1600", "1300-1700", "1700-2100"])
t = time(timeframe.period, i_sess)
bgcolor(time == t ? color.green : na)
```

---

## input.source()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a dropdown that allows the user to select a source for the calculation, e.g. close, hl2, etc. The user can also select an output from another indicator on their chart as the source.

### Returns
Value of input variable.

### Remarks
Result of input.source function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.source", overlay=true)
i_src = input.source(close, "Source")
plot(i_src)
```

---

## input.string()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a field for a string input to the script's inputs.

### Returns
Value of input variable.

### Remarks
Result of input.string function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.string", overlay=true)
i_text = input.string("Hello!", "Message")
l = label.new(bar_index, high, i_text)
label.delete(l[1])
```

---

## input.symbol()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a field that allows the user to select a specific symbol using the symbol search and returns that symbol, paired with its exchange prefix, as a string.

### Returns
Value of input variable.

### Remarks
Result of input.symbol function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.symbol", overlay=true)
i_sym = input.symbol("DELL", "Symbol")
s = request.security(i_sym, 'D', close)
plot(s)
```

---

## input.text_area()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a field for a multiline text input.

### Returns
Value of input variable.

### Remarks
Result of input.text_area function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.text_area")
i_text = input.text_area(defval = "Hello \nWorld!", title = "Message")
plot(close)
```

---

## input.time()

Adds a time input to the script's "Settings/Inputs" tab. This function adds two input widgets on the same line: one for the date and one for the time. The function returns a date/time value in UNIX format. Using confirm = true activates the interactive input mode where a point in time is selected by clicking on the chart.

### Returns
Value of input variable.

### Remarks
When using interactive mode, a price input can be combined with a time input if both function calls use the same argument for their inline parameter.

### Code Example
```pine
//@version=6
indicator("input.time", overlay=true)
i_date = input.time(timestamp("20 Jul 2021 00:00 +0300"), "Date")
l = label.new(i_date, high, "Date", xloc=xloc.bar_time)
label.delete(l[1])
```

---

## input.timeframe()

Adds an input to the Inputs tab of your script's Settings, which allows you to provide configuration options to script users. This function adds a dropdown that allows the user to select a specific timeframe via the timeframe selector and returns it as a string. The selector includes the custom timeframes a user may have added using the chart's Timeframe dropdown.

### Returns
Value of input variable.

### Remarks
Result of input.timeframe function always should be assigned to a variable, see examples above.

### Code Example
```pine
//@version=6
indicator("input.timeframe", overlay=true)
i_res = input.timeframe('D', "Resolution", options=['D', 'W', 'M'])
s = request.security("AAPL", i_res, close)
plot(s)
```

---

## int()

Casts na or truncates float value to int

### Returns
The value of the argument after casting to int.

---

## library()

Declaration statement identifying a script as a library.

### Code Example
```pine
//@version=6
// @description Math library
library("num_methods", overlay = true)
// Calculate "sinh()" from the float parameter `x`
export sinh(float x) =>
    (math.exp(x) - math.exp(-x)) / 2.0
plot(sinh(0))
```

---

## log.error()

Converts the formatting string and value(s) into a formatted string, and sends the result to the "Pine logs" menu tagged with the "error" debug level.

### Returns
The formatted string.

### Remarks
Any curly braces within an unquoted pattern must be balanced. For example, "ab {0} de" and "ab '}' de" are valid patterns, but "ab {0'}' de", "ab } de" and "''{''" are not.  The function can apply additional formatting to some values inside of the {}. The list of additional formatting options can be found in the EXAMPLE section of the str.format article.  The string used as the formatString argument can contain single quote characters ('). However, one must pair all single quotes in that string to avoid unexpected formatting results.  The "Pine logs..." button is accessible from the "More" dropdown in the Pine Editor and from the "More" dropdown in the status line of any script that uses log.*() functions.

### Code Example
```pine
//@version=6
strategy("My strategy", overlay = true, process_orders_on_close = true)
bracketTickSizeInput = input.int(1000, "Stoploss/Take-Profit distance (in ticks)")

longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
if (longCondition)
    limitLevel = close * 1.01
    log.info("Long limit order has been placed at {0}", limitLevel)
    strategy.order("My Long Entry Id", strategy.long, limit = limitLevel)

    log.info("Exit orders have been placed: Take-profit at {0}, Stop-loss at {1}", close, limitLevel)
    strategy.exit("Exit", "My Long Entry Id", profit = bracketTickSizeInput, loss = bracketTickSizeInput)

if strategy.opentrades > 10
    log.warning("{0} positions opened in the same direction in a row. Try adjusting `bracketTickSizeInput`", strategy.opentrades)

last10Perc = strategy.initial_capital / 10 > strategy.equity
if (last10Perc and not last10Perc[1])
    log.error("The strategy has lost 90% of the initial capital!")
```

---

## log.info()

Converts the formatting string and value(s) into a formatted string, and sends the result to the "Pine logs" menu tagged with the "info" debug level.

### Returns
The formatted string.

### Remarks
Any curly braces within an unquoted pattern must be balanced. For example, "ab {0} de" and "ab '}' de" are valid patterns, but "ab {0'}' de", "ab } de" and "''{''" are not.  The function can apply additional formatting to some values inside of the {}. The list of additional formatting options can be found in the EXAMPLE section of the str.format article.  The string used as the formatString argument can contain single quote characters ('). However, one must pair all single quotes in that string to avoid unexpected formatting results.  The "Pine logs..." button is accessible from the "More" dropdown in the Pine Editor and from the "More" dropdown in the status line of any script that uses log.*() functions.

### Code Example
```pine
//@version=6
strategy("My strategy", overlay = true, process_orders_on_close = true)
bracketTickSizeInput = input.int(1000, "Stoploss/Take-Profit distance (in ticks)")

longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
if (longCondition)
    limitLevel = close * 1.01
    log.info("Long limit order has been placed at {0}", limitLevel)
    strategy.order("My Long Entry Id", strategy.long, limit = limitLevel)

    log.info("Exit orders have been placed: Take-profit at {0}, Stop-loss at {1}", close, limitLevel)
    strategy.exit("Exit", "My Long Entry Id", profit = bracketTickSizeInput, loss = bracketTickSizeInput)

if strategy.opentrades > 10
    log.warning("{0} positions opened in the same direction in a row. Try adjusting `bracketTickSizeInput`", strategy.opentrades)

last10Perc = strategy.initial_capital / 10 > strategy.equity
if (last10Perc and not last10Perc[1])
    log.error("The strategy has lost 90% of the initial capital!")
```

---

## log.warning()

Converts the formatting string and value(s) into a formatted string, and sends the result to the "Pine logs" menu tagged with the "warning" debug level.

### Returns
The formatted string.

### Remarks
Any curly braces within an unquoted pattern must be balanced. For example, "ab {0} de" and "ab '}' de" are valid patterns, but "ab {0'}' de", "ab } de" and "''{''" are not.  The function can apply additional formatting to some values inside of the {}. The list of additional formatting options can be found in the EXAMPLE section of the str.format article.  The string used as the formatString argument can contain single quote characters ('). However, one must pair all single quotes in that string to avoid unexpected formatting results.  The "Pine logs..." button is accessible from the "More" dropdown in the Pine Editor and from the "More" dropdown in the status line of any script that uses log.*() functions.

### Code Example
```pine
//@version=6
strategy("My strategy", overlay = true, process_orders_on_close = true)
bracketTickSizeInput = input.int(1000, "Stoploss/Take-Profit distance (in ticks)")

longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
if (longCondition)
    limitLevel = close * 1.01
    log.info("Long limit order has been placed at {0}", limitLevel)
    strategy.order("My Long Entry Id", strategy.long, limit = limitLevel)

    log.info("Exit orders have been placed: Take-profit at {0}, Stop-loss at {1}", close, limitLevel)
    strategy.exit("Exit", "My Long Entry Id", profit = bracketTickSizeInput, loss = bracketTickSizeInput)

if strategy.opentrades > 10
    log.warning("{0} positions opened in the same direction in a row. Try adjusting `bracketTickSizeInput`", strategy.opentrades)

last10Perc = strategy.initial_capital / 10 > strategy.equity
if (last10Perc and not last10Perc[1])
    log.error("The strategy has lost 90% of the initial capital!")
```

---

## math.abs()

Absolute value of number is number if number >= 0, or -number otherwise.

### Returns
The absolute value of number.

---

## math.acos()

The acos function returns the arccosine (in radians) of number such that cos(acos(y)) = y for y in range [-1, 1].

### Returns
The arc cosine of a value; the returned angle is in the range [0, Pi], or na if y is outside of range [-1, 1].

---

## math.asin()

The asin function returns the arcsine (in radians) of number such that sin(asin(y)) = y for y in range [-1, 1].

### Returns
The arcsine of a value; the returned angle is in the range [-Pi/2, Pi/2], or na if y is outside of range [-1, 1].

---

## math.atan()

The atan function returns the arctangent (in radians) of number such that tan(atan(y)) = y for any y.

### Returns
The arc tangent of a value; the returned angle is in the range [-Pi/2, Pi/2].

---

## math.avg()

Calculates average of all given series (elementwise).

### Returns
Average.

---

## math.ceil()

Rounds the specified number up to the smallest whole number ("int" value) that is greater than or equal to it.

### Returns
The smallest "int" value that is greater than or equal to the number.

---

## math.cos()

The cos function returns the trigonometric cosine of an angle.

### Returns
The trigonometric cosine of an angle.

---

## math.exp()

The exp function of number is e raised to the power of number, where e is Euler's number.

### Returns
A value representing e raised to the power of number.

---

## math.floor()

Rounds the specified number down to the largest whole number ("int" value) that is less than or equal to it.

### Returns
The largest "int" value that is less than or equal to the number.

---

## math.log()

Natural logarithm of any number > 0 is the unique y such that e^y = number.

### Returns
The natural logarithm of number.

---

## math.log10()

The common (or base 10) logarithm of number is the power to which 10 must be raised to obtain the number. 10^y = number.

### Returns
The base 10 logarithm of number.

---

## math.max()

Returns the greatest of multiple values.

### Returns
The greatest of multiple given values.

### Code Example
```pine
//@version=6
indicator("math.max", overlay=true)
plot(math.max(close, open))
plot(math.max(close, math.max(open, 42)))
```

---

## math.min()

Returns the smallest of multiple values.

### Returns
The smallest of multiple given values.

### Code Example
```pine
//@version=6
indicator("math.min", overlay=true)
plot(math.min(close, open))
plot(math.min(close, math.min(open, 42)))
```

---

## math.pow()

Mathematical power function.

### Returns
base raised to the power of exponent. If base is a series, it is calculated elementwise.

### Code Example
```pine
//@version=6
indicator("math.pow", overlay=true)
plot(math.pow(close, 2))
```

---

## math.random()

Returns a pseudo-random value. The function will generate a different sequence of values for each script execution. Using the same value for the optional seed argument will produce a repeatable sequence.

### Returns
A random value.

---

## math.round()

Returns the value of number rounded to the nearest integer, with ties rounding up. If the precision parameter is used, returns a float value rounded to that amount of decimal places.

### Returns
The value of number rounded to the nearest integer, or according to precision.

### Remarks
Note that for 'na' values function returns 'na'.

---

## math.round_to_mintick()

Returns the value rounded to the symbol's mintick, i.e. the nearest value that can be divided by syminfo.mintick, without the remainder, with ties rounding up.

### Returns
The number rounded to tick precision.

### Remarks
Note that for 'na' values function returns 'na'.

---

## math.sign()

Sign (signum) of number is zero if number is zero, 1.0 if number is greater than zero, -1.0 if number is less than zero.

### Returns
The sign of the argument.

---

## math.sin()

The sin function returns the trigonometric sine of an angle.

### Returns
The trigonometric sine of an angle.

---

## math.sqrt()

Square root of any number >= 0 is the unique y >= 0 such that y^2 = number.

### Returns
The square root of number.

---

## math.sum()

The sum function returns the sliding sum of last y values of x.

### Returns
Sum of source for length bars back.

### Remarks
na values in the source series are ignored; the function calculates on the length quantity of non-na values.

---

## math.tan()

The tan function returns the trigonometric tangent of an angle.

### Returns
The trigonometric tangent of an angle.

---

## math.todegrees()

Returns an approximately equivalent angle in degrees from an angle measured in radians.

### Returns
The angle value in degrees.

---

## math.toradians()

Returns an approximately equivalent angle in radians from an angle measured in degrees.

### Returns
The angle value in radians.

---

## max_bars_back()

Function sets the maximum number of bars that is available for historical reference of a given built-in or user variable. When operator '[]' is applied to a variable - it is a reference to a historical value of that variable.

### Returns
void

### Remarks
At the moment 'max_bars_back' cannot be applied to built-ins like 'hl2', 'hlc3', 'ohlc4'. Please use multiple 'max_bars_back' calls as workaround here (e.g. instead of a single ‘max_bars_back(hl2, 100)’ call you should call the function twice: ‘max_bars_back(high, 100), max_bars_back(low, 100)’).  If the indicator or strategy 'max_bars_back' parameter is used, all variables in the indicator are affected. This may result in excessive memory usage and cause runtime problems. When possible (i.e. when the cause is a variable rather than a function), please use the max_bars_back function instead.

### Code Example
```pine
//@version=6
indicator("max_bars_back")
close_() => close
depth() => 400
d = depth()
v = close_()
max_bars_back(v, 500)
out = if bar_index > 0
    v[d]
else
    v
plot(out)
```

---

## minute()

### Returns
Minute (in exchange timezone) for provided UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970.

---

## month()

### Returns
Month (in exchange timezone) for provided UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970. Note that this function returns the month based on the time of the bar's open. For overnight sessions (e.g. EURUSD, where Monday session starts on Sunday, 17:00 UTC-4) this value can be lower by 1 than the month of the trading day.

---

## na()

Tests if x is na.

### Returns
Returns true if x is na, false otherwise.

### Code Example
```pine
//@version=6
indicator("na")
// Use the `na()` function to test for `na`.
plot(na(close[1]) ? close : close[1])
// ALTERNATIVE
// `nz()` also tests `close[1]` for `na`. It returns `close[1]` if it is not `na`, and `close` if it is.
plot(nz(close[1], close))
```

---

## nz()

Replaces NaN values with zeros (or given value) in a series.

### Returns
The value of source if it is not na. If the value of source is na, returns zero, or the replacement argument when one is used.

### Code Example
```pine
//@version=6
indicator("nz", overlay=true)
plot(nz(ta.sma(close, 100)))
```

---

## plotarrow()

Plots up and down arrows on the chart. Up arrow is drawn at every indicator positive value, down arrow is drawn at every negative value. If indicator returns na then no arrow is drawn. Arrows has different height, the more absolute indicator value the longer arrow is drawn.

### Remarks
Use plotarrow function in conjunction with 'overlay=true' indicator parameter!

### Code Example
```pine
//@version=6
indicator("plotarrow example", overlay=true)
codiff = close - open
plotarrow(codiff, colorup=color.new(color.teal,40), colordown=color.new(color.orange, 40))
```

---

## plotbar()

Plots ohlc bars on the chart.

### Remarks
Even if one value of open, high, low or close equal NaN then bar no draw. The maximal value of open, high, low or close will be set as 'high', and the minimal value will be set as 'low'.

### Code Example
```pine
//@version=6
indicator("plotbar example", overlay=true)
plotbar(open, high, low, close, title='Title', color = open < close ? color.green : color.red)
```

---

## plotcandle()

Plots candles on the chart.

### Remarks
Even if one value of open, high, low or close equal NaN then bar no draw. The maximal value of open, high, low or close will be set as 'high', and the minimal value will be set as 'low'.

### Code Example
```pine
//@version=6
indicator("plotcandle example", overlay=true)
plotcandle(open, high, low, close, title='Title', color = open < close ? color.green : color.red, wickcolor=color.black)
```

---

## plotchar()

Plots visual shapes using any given one Unicode character on the chart.

### Remarks
Use plotchar function in conjunction with 'overlay=true' indicator parameter!

### Code Example
```pine
//@version=6
indicator("plotchar example", overlay=true)
data = close >= open
plotchar(data, char='❄')
```

---

## plotshape()

Plots visual shapes on the chart.

### Remarks
Use plotshape function in conjunction with 'overlay=true' indicator parameter!

### Code Example
```pine
//@version=6
indicator("plotshape example 1", overlay=true)
data = close >= open
plotshape(data, style=shape.xcross)
```

---

## runtime.error()

When called, causes a runtime error with the error message specified in the message argument.

---

## second()

### Returns
Second (in exchange timezone) for provided UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970.

---

## str.contains()

Returns true if the source string contains the str substring, false otherwise.

### Returns
True if the str was found in the source string, false otherwise.

### Code Example
```pine
//@version=6
indicator("str.contains")
// If the current chart is a continuous futures chart, e.g “BTC1!”, then the function will return true, false otherwise.
var isFutures = str.contains(syminfo.tickerid, "!")
plot(isFutures ? 1 : 0)
```

---

## str.endswith()

Returns true if the source string ends with the substring specified in str, false otherwise.

### Returns
True if the source string ends with the substring specified in str, false otherwise.

---

## str.format()

Converts the formatting string and value(s) into a formatted string. The formatting string can contain literal text and one placeholder in curly braces {} for each value to be formatted. Each placeholder consists of the index of the required argument (beginning at 0) that will replace it, and an optional format specifier. The index represents the position of that argument in the str.format argument list.

### Returns
The formatted string.

### Remarks
By default, formatted numbers will display up to three decimals with no trailing zeros. The string used as the formatString argument can contain single quote characters ('). However, one must pair all single quotes in that string to avoid unexpected formatting results. Any curly braces within an unquoted pattern must be balanced. For example, "ab {0} de" and "ab '}' de" are valid patterns, but "ab {0'}' de", "ab } de" and "''{''" are not.

### Code Example
```pine
//@version=6
indicator("str.format", overlay=true)
// The format specifier inside the curly braces accepts certain modifiers:
// - Specify the number of decimals to display:
s1 = str.format("{0,number,#.#}", 1.34) // returns: 1.3
label.new(bar_index, close, text=s1)
// - Round a float value to an integer:
s2 = str.format("{0,number,integer}", 1.34) // returns: 1
label.new(bar_index - 1, close, text=s2)
// - Display a number in currency:
s3 = str.format("{0,number,currency}", 1.34) // returns: $1.34
label.new(bar_index - 2, close, text=s3)
// - Display a number as a percentage:
s4 = str.format("{0,number,percent}", 0.5) // returns: 50%
label.new(bar_index - 3, close, text=s4)
// EXAMPLES WITH SEVERAL ARGUMENTS
// returns: Number 1 is not equal to 4
s5 = str.format("Number {0} is not {1} to {2}", 1, "equal", 4)
label.new(bar_index - 4, close, text=s5)
// returns: 1.34 != 1.3
s6 = str.format("{0} != {0, number, #.#}", 1.34)
label.new(bar_index - 5, close, text=s6)
// returns: 1 is equal to 1, but 2 is equal to 2
s7 = str.format("{0, number, integer} is equal to 1, but {1, number, integer} is equal to 2", 1.34, 1.52)
label.new(bar_index - 6, close, text=s7)
// returns: The cash turnover amounted to $1,340,000.00
s8 = str.format("The cash turnover amounted to {0, number, currency}", 1340000)
label.new(bar_index - 7, close, text=s8)
// returns: Expected return is 10% - 20%
s9 = str.format("Expected return is {0, number, percent} - {1, number, percent}", 0.1, 0.2)
label.new(bar_index - 8, close, text=s9)
```

---

## str.format_time()

Converts the time timestamp into a string formatted according to format and timezone.

### Returns
The formatted string.

### Remarks
The M, d, h, H, m and s tokens can all be doubled to generate leading zeros. For example, the month of January will display as 1 with M, or 01 with MM.  The most frequently used formatting tokens are:  y - Year. Use yy to output the last two digits of the year or yyyy to output all four. Year 2000 will be 00 with yy or 2000 with yyyy. M - Month. Not to be confused with lowercase m, which stands for minute. d - Day of the month. a - AM/PM postfix. h - Hour in the 12-hour format. The last hour of the day will be 11 in this format. H - Hour in the 24-hour format. The last hour of the day will be 23 in this format. m - Minute. s - Second. S - Fractions of a second. Z - Timezone, the HHmm offset from UTC, preceded by either + or -.

### Code Example
```pine
//@version=6
indicator("str.format_time")
if timeframe.change("1D")
    formattedTime = str.format_time(time, "yyyy-MM-dd HH:mm", syminfo.timezone)
    label.new(bar_index, high, formattedTime)
```

---

## str.length()

Returns an integer corresponding to the amount of chars in that string.

### Returns
The number of chars in source string.

---

## str.lower()

Returns a new string with all letters converted to lowercase.

### Returns
A new string with all letters converted to lowercase.

---

## str.match()

Returns the new substring of the source string if it matches a regex regular expression, an empty string otherwise.

### Returns
The new substring of the source string if it matches a regex regular expression, an empty string otherwise.

### Remarks
Function returns first occurrence of the regular expression in the source string. The backslash "\" symbol in theregex string needs to be escaped with additional backslash, e.g. "\\d" stands for regular expression "\d".

### Code Example
```pine
//@version=6
indicator("str.match")

s = input.string("It's time to sell some NASDAQ:AAPL!")

// finding first substring that matches regular expression "[\w]+:[\w]+"
var string tickerid = str.match(s, "[\\w]+:[\\w]+")

if barstate.islastconfirmedhistory
    label.new(bar_index, high, text = tickerid) // "NASDAQ:AAPL"
```

---

## str.pos()

Returns the position of the first occurrence of the str string in the source string, 'na' otherwise.

### Returns
Position of the str string in the source string.

### Remarks
Strings indexing starts at 0.

---

## str.repeat()

Constructs a new string containing the source string repeated repeat times with the separator injected between each repeated instance.

### Remarks
Returns na if the source is na.

### Code Example
```pine
//@version=6
indicator("str.repeat")
repeat = str.repeat("?", 3, ",") // Returns "?,?,?"
label.new(bar_index,close,repeat)
```

---

## str.replace()

Returns a new string with the Nth occurrence of the target string replaced by the replacement string, where N is specified in occurrence.

### Returns
Processed string.

### Code Example
```pine
//@version=6
indicator("str.replace")
var source = "FTX:BTCUSD / FTX:BTCEUR"

// Replace first occurrence of "FTX" with "BINANCE" replacement string
var newSource = str.replace(source, "FTX", "BINANCE", 0)

if barstate.islastconfirmedhistory
    // Display "BINANCE:BTCUSD / FTX:BTCEUR"
    label.new(bar_index, high, text = newSource)
```

---

## str.replace_all()

Replaces each occurrence of the target string in the source string with the replacement string.

### Returns
Processed string.

---

## str.split()

Divides a string into an array of substrings and returns its array id.

### Returns
The id of an array of strings.

---

## str.startswith()

Returns true if the source string starts with the substring specified in str, false otherwise.

### Returns
True if the source string starts with the substring specified in str, false otherwise.

---

## str.substring()

Returns a new string that is a substring of the source string. The substring begins with the character at the index specified by begin_pos and extends to 'end_pos - 1' of the source string.

### Returns
The substring extracted from the source string.

### Remarks
Strings indexing starts from 0. If begin_pos is equal to end_pos, the function returns an empty string.

### Code Example
```pine
//@version=6
indicator("str.substring", overlay = true)
sym= input.symbol("NASDAQ:AAPL")
pos = str.pos(sym, ":") // Get position of ":" character
tkr= str.substring(sym, pos+1) // "AAPL"
if barstate.islastconfirmedhistory
    label.new(bar_index, high, text = tkr)
```

---

## str.tonumber()

Converts a value represented in string to its "float" equivalent.

### Returns
A "float" equivalent of the value in string. If the value is not a properly formed integer or floating point value, the function returns na.

---

## str.tostring()

### Returns
The string representation of the value argument.

### Remarks
The formatting of float values will also round those values when necessary, e.g. str.tostring(3.99, '#') will return "4". To display trailing zeros, use '0' instead of '#'. For example, '#.000'. When using format.mintick, the value will be rounded to the nearest number that can be divided by syminfo.mintick without the remainder. The string is returned with trailing zeros. If the x argument is a string, the same string value will be returned. Bool type arguments return "true" or "false". When x is na, the function returns "NaN".

---

## str.trim()

Constructs a new string with all consecutive whitespaces and other control characters (e.g., “\n”, “\t”, etc.) removed from the left and right of the source.

### Remarks
Returns an empty string ("") if the result is empty after the trim or if the source is na.

### Code Example
```pine
//@version=6
indicator("str.trim")
trim = str.trim("    abc    ") // Returns "abc"
label.new(bar_index,close,trim)
```

---

## str.upper()

Returns a new string with all letters converted to uppercase.

### Returns
A new string with all letters converted to uppercase.

---

## string()

Casts na to string

### Returns
The value of the argument after casting to string.

---

## syminfo.prefix()

Returns exchange prefix of the symbol, e.g. "NASDAQ".

### Returns
Returns exchange prefix of the symbol, e.g. "NASDAQ".

### Remarks
The result of the function is used in the ticker.new/ticker.modify and request.security.

### Code Example
```pine
//@version=6
indicator("syminfo.prefix fun", overlay=true)
i_sym = input.symbol("NASDAQ:AAPL")
pref = syminfo.prefix(i_sym)
tick = syminfo.ticker(i_sym)
t = ticker.new(pref, tick, session.extended)
s = request.security(t, "1D", close)
plot(s)
```

---

## syminfo.ticker()

Returns symbol name without exchange prefix, e.g. "AAPL".

### Returns
Returns symbol name without exchange prefix, e.g. "AAPL".

### Remarks
The result of the function is used in the ticker.new/ticker.modify and request.security.

### Code Example
```pine
//@version=6
indicator("syminfo.ticker fun", overlay=true) 
i_sym = input.symbol("NASDAQ:AAPL")
pref = syminfo.prefix(i_sym)
tick = syminfo.ticker(i_sym)
t = ticker.new(pref, tick, session.extended)
s = request.security(t, "1D", close)
plot(s)
```

---

## ticker.heikinashi()

Creates a ticker identifier for requesting Heikin Ashi bar values.

### Returns
String value of ticker id, that can be supplied to request.security function.

### Code Example
```pine
//@version=6
indicator("ticker.heikinashi", overlay=true) 
heikinashi_close = request.security(ticker.heikinashi(syminfo.tickerid), timeframe.period, close)

heikinashi_aapl_60_close = request.security(ticker.heikinashi("AAPL"), "60", close)
plot(heikinashi_close)
plot(heikinashi_aapl_60_close)
```

---

## ticker.inherit()

Constructs a ticker ID for the specified symbol with additional parameters inherited from the ticker ID passed into the function call, allowing the script to request a symbol's data using the same modifiers that the from_tickerid has, including extended session, dividend adjustment, currency conversion, non-standard chart types, back-adjustment, settlement-as-close, etc.

### Remarks
If the constructed ticker ID inherits a modifier that doesn't apply to the symbol (e.g., if the from_tickerid has Extended Hours enabled, but no such option is available for the symbol), the script will ignore the modifier when requesting data using the ID.

### Code Example
```pine
//@version=6
indicator("ticker.inherit")

//@variable A "NASDAQ:AAPL" ticker ID with Extender Hours enabled.
tickerExtHours = ticker.new("NASDAQ", "AAPL", session.extended)
//@variable A Heikin Ashi ticker ID for "NASDAQ:AAPL" with Extended Hours enabled.
HAtickerExtHours = ticker.heikinashi(tickerExtHours)
//@variable The "NASDAQ:MSFT" symbol with no modifiers.
testSymbol = "NASDAQ:MSFT"
//@variable A ticker ID for "NASDAQ:MSFT" with inherited Heikin Ashi and Extended Hours modifiers.
testSymbolHAtickerExtHours = ticker.inherit(HAtickerExtHours, testSymbol)

//@variable The `close` price requested using "NASDAQ:MSFT" with inherited modifiers. 
secData = request.security(testSymbolHAtickerExtHours, "60", close, ignore_invalid_symbol = true)
//@variable The `close` price requested using "NASDAQ:MSFT" without modifiers. 
compareData = request.security(testSymbol, "60", close, ignore_invalid_symbol = true)

plot(secData, color = color.green)
plot(compareData)
```

---

## ticker.kagi()

Creates a ticker identifier for requesting Kagi values.

### Returns
String value of ticker id, that can be supplied to request.security function.

### Code Example
```pine
//@version=6
indicator("ticker.kagi", overlay=true) 
kagi_tickerid = ticker.kagi(syminfo.tickerid, 3)
kagi_close = request.security(kagi_tickerid, timeframe.period, close)
plot(kagi_close)
```

---

## ticker.linebreak()

Creates a ticker identifier for requesting Line Break values.

### Returns
String value of ticker id, that can be supplied to request.security function.

### Code Example
```pine
//@version=6
indicator("ticker.linebreak", overlay=true) 
linebreak_tickerid = ticker.linebreak(syminfo.tickerid, 3)
linebreak_close = request.security(linebreak_tickerid, timeframe.period, close)
plot(linebreak_close)
```

---

## ticker.modify()

Creates a ticker identifier for requesting additional data for the script.

### Returns
String value of ticker id, that can be supplied to request.security function.

### Code Example
```pine
//@version=6
indicator("ticker_modify", overlay=true)
t1 = ticker.new(syminfo.prefix, syminfo.ticker, session.regular, adjustment.splits)
c1 = request.security(t1, "D", close)
t2 = ticker.modify(t1, session.extended)
c2 = request.security(t2, "2D", close)
plot(c1)
plot(c2)
```

---

## ticker.new()

Creates a ticker identifier for requesting additional data for the script.

### Returns
String value of ticker id, that can be supplied to request.security function.

### Remarks
You may use return value of ticker.new function as input argument for ticker.heikinashi, ticker.renko, ticker.linebreak, ticker.kagi, ticker.pointfigure functions.

### Code Example
```pine
//@version=6
indicator("ticker.new", overlay=true) 
t = ticker.new(syminfo.prefix, syminfo.ticker, session.regular, adjustment.splits)
t2 = ticker.heikinashi(t)
c = request.security(t2, timeframe.period, low, barmerge.gaps_on)
plot(c, style=plot.style_linebr)
```

---

## ticker.pointfigure()

Creates a ticker identifier for requesting Point & Figure values.

### Returns
String value of ticker id, that can be supplied to request.security function.

### Code Example
```pine
//@version=6
indicator("ticker.pointfigure", overlay=true) 
pnf_tickerid = ticker.pointfigure(syminfo.tickerid, "hl", "Traditional", 1, 3)
pnf_close = request.security(pnf_tickerid, timeframe.period, close)
plot(pnf_close)
```

---

## ticker.renko()

Creates a ticker identifier for requesting Renko values.

### Returns
String value of ticker id, that can be supplied to request.security function.

### Code Example
```pine
//@version=6
indicator("ticker.renko", overlay=true) 
renko_tickerid = ticker.renko(syminfo.tickerid, "ATR", 10)
renko_close = request.security(renko_tickerid, timeframe.period, close)
plot(renko_close)

//@version=6
indicator("Renko candles", overlay=false)
renko_tickerid = ticker.renko(syminfo.tickerid, "ATR", 10)
[renko_open, renko_high, renko_low, renko_close] = request.security(renko_tickerid, timeframe.period, [open, high, low, close])
plotcandle(renko_open, renko_high, renko_low, renko_close, color = renko_close > renko_open ? color.green : color.red)
```

---

## ticker.standard()

Creates a ticker to request data from a standard chart that is unaffected by modifiers like extended session, dividend adjustment, currency conversion, and the calculations of non-standard chart types: Heikin Ashi, Renko, etc. Among other things, this makes it possible to retrieve standard chart values when the script is running on a non-standard chart.

### Returns
A string representing the ticker of a standard chart in the "prefix:ticker" format. If the symbol argument does not contain the prefix and ticker information, the function returns the supplied argument as is.

### Code Example
```pine
//@version=6
indicator("ticker.standard", overlay = true)
// This script should be run on a non-standard chart such as HA, Renko...

// Requests data from the chart type the script is running on.
chartTypeValue = request.security(syminfo.tickerid, "1D", close)

// Request data from the standard chart type, regardless of the chart type the script is running on.
standardChartValue = request.security(ticker.standard(syminfo.tickerid), "1D", close)

// This will not use a standard ticker ID because the `symbol` argument contains only the ticker — not the prefix (exchange).
standardChartValue2 = request.security(ticker.standard(syminfo.ticker), "1D", close)

plot(chartTypeValue)
plot(standardChartValue, color = color.green)
```

---

## time()

The time function returns the UNIX time of the current bar for the specified timeframe and session or NaN if the time point is out of session.

### Returns
UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970.

### Code Example
```pine
//@version=6
indicator("Time", overlay=true)
// Try this on chart AAPL,1
timeinrange(res, sess) => not na(time(res, sess, "America/New_York")) ? 1 : 0
plot(timeinrange("1", "1300-1400"), color=color.red)

// This plots 1.0 at every start of 10 minute bar on a 1 minute chart:
newbar(res) => ta.change(time(res)) == 0 ? 0 : 1
plot(newbar("10"))

//@version=6
indicator("Time", overlay=true)
t1 = time(timeframe.period, "0000-0000:23456")
bgcolor(not na(t1) ? color.new(color.blue, 90) : na)

//@version=6
indicator("Time", overlay=true)
t1 = time(timeframe.period, "1000-1100,1400-1500:23456")
bgcolor(not na(t1) ? color.new(color.blue, 90) : na)
```

---

## time_close()

Returns the UNIX time of the current bar's close for the specified timeframe and session, or na if the time point is outside the session. On tick charts and price-based charts such as Renko, line break, Kagi, point & figure, and range, this function returns an na timestamp for the latest realtime bar (because the future closing time is unpredictable), but a valid timestamp for any previous bar.

### Returns
UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970.

### Code Example
```pine
//@version=6
indicator("Time", overlay=true)
t1 = time_close(timeframe.period, "1200-1300", "America/New_York")
bgcolor(not na(t1) ? color.new(color.blue, 90) : na)
```

---

## timeframe.change()

Detects changes in the specified timeframe.

### Returns
Returns true on the first bar of a new timeframe, false otherwise.

### Code Example
```pine
//@version=6
// Run this script on an intraday chart.
indicator("New day started", overlay = true)
// Highlights the first bar of the new day.
isNewDay = timeframe.change("1D")
bgcolor(isNewDay ? color.new(color.green, 80) : na)
```

---

## timeframe.from_seconds()

Converts a number of seconds into a valid timeframe string.

### Returns
A timeframe string compliant with timeframe string specifications.

### Remarks
If no valid timeframe exists for the quantity of seconds supplied, the next higher valid timeframe will be returned. Accordingly, one second or less will return "1S", 2-5 seconds will return "5S", and 604,799 seconds (one second less than 7 days) will return "7D". If the seconds exactly represent two or more valid timeframes, the one with the larger base unit will be used. Thus 604,800 seconds (7 days) returns "1W", not "7D". All values above 31,622,400 (366 days) return "12M".

### Code Example
```pine
//@version=6
indicator("HTF Close", "", true)
int chartTf = timeframe.in_seconds()
string tfTimes5 = timeframe.from_seconds(chartTf * 5)
float htfClose = request.security(syminfo.tickerid, tfTimes5, close)
plot(htfClose)
```

---

## timeframe.in_seconds()

Converts a timeframe string into seconds.

### Returns
The "int" representation of the number of seconds in the timeframe string.

### Remarks
When the timeframe is "1M" or more, calculations use 2628003 as the number of seconds in one month, which represents 30.4167 (365/12) days.

### Code Example
```pine
//@version=6
indicator("`timeframe_in_seconds()`")

// Get a user-selected timeframe.
tfInput = input.timeframe("1D")

// Convert it into an "int" number of seconds.
secondsInTf = timeframe.in_seconds(tfInput)

plot(secondsInTf)
```

---

## timestamp()

Function timestamp returns UNIX time of specified date and time.

### Returns
UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970.

### Code Example
```pine
//@version=6
indicator("timestamp")
plot(timestamp(2016, 01, 19, 09, 30), linewidth=3, color=color.green)
plot(timestamp(syminfo.timezone, 2016, 01, 19, 09, 30), color=color.blue)
plot(timestamp(2016, 01, 19, 09, 30), color=color.yellow)
plot(timestamp("GMT+6", 2016, 01, 19, 09, 30))
plot(timestamp(2019, 06, 19, 09, 30, 15), color=color.lime)
plot(timestamp("GMT+3", 2019, 06, 19, 09, 30, 15), color=color.fuchsia)
plot(timestamp("Feb 01 2020 22:10:05"))
plot(timestamp("2011-10-10T14:48:00"))
plot(timestamp("04 Dec 1995 00:12:00 GMT+5"))
```

---

## weekofyear()

### Returns
Week of year (in exchange timezone) for provided UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970. Note that this function returns the week based on the time of the bar's open. For overnight sessions (e.g. EURUSD, where Monday session starts on Sunday, 17:00) this value can be lower by 1 than the week of the trading day.

---

## year()

### Returns
Year (in exchange timezone) for provided UNIX time.

### Remarks
UNIX time is the number of milliseconds that have elapsed since 00:00:00 UTC, 1 January 1970. Note that this function returns the year based on the time of the bar's open. For overnight sessions (e.g. EURUSD, where Monday session starts on Sunday, 17:00 UTC-4) this value can be lower by 1 than the year of the trading day.

---

