## barcolor()

Set color of bars.

### Code Example
```pine
//@version=6
indicator("barcolor example", overlay=true)
barcolor(close < open ? color.black : color.white)
```

---

## bgcolor()

Fill background of bars with specified color.

### Code Example
```pine
//@version=6
indicator("bgcolor example", overlay=true)
bgcolor(close < open ? color.new(color.red,70) : color.new(color.green, 70))
```

---

## box()

Casts na to box.

### Returns
The value of the argument after casting to box.

---

## box.copy()

Clones the box object.

### Code Example
```pine
//@version=6
indicator('Last 50 bars price ranges', overlay = true)
LOOKBACK = 50
highest = ta.highest(LOOKBACK)
lowest = ta.lowest(LOOKBACK)
if barstate.islastconfirmedhistory
    var BoxLast = box.new(bar_index[LOOKBACK], highest, bar_index, lowest, bgcolor = color.new(color.green, 80))
    var BoxPrev = box.copy(BoxLast)
    box.set_lefttop(BoxPrev, bar_index[LOOKBACK * 2], highest[50])
    box.set_rightbottom(BoxPrev, bar_index[LOOKBACK], lowest[50])
    box.set_bgcolor(BoxPrev, color.new(color.red, 80))
```

---

## box.delete()

Deletes the specified box object. If it has already been deleted, does nothing.

---

## box.get_bottom()

Returns the price value of the bottom border of the box.

### Returns
The price value.

---

## box.get_left()

Returns the bar index or the UNIX time (depending on the last value used for 'xloc') of the left border of the box.

### Returns
A bar index or a UNIX timestamp (in milliseconds).

---

## box.get_right()

Returns the bar index or the UNIX time (depending on the last value used for 'xloc') of the right border of the box.

### Returns
A bar index or a UNIX timestamp (in milliseconds).

---

## box.get_top()

Returns the price value of the top border of the box.

### Returns
The price value.

---

## box.new()

Creates a new box object.

### Returns
The ID of a box object which may be used in box.set_*() and box.get_*() functions.

### Code Example
```pine
//@version=6
indicator("box.new")
var b = box.new(time, open, time + 60 * 60 * 24, close, xloc=xloc.bar_time, border_style=line.style_dashed)
box.set_lefttop(b, time, 100)
box.set_rightbottom(b, time + 60 * 60 * 24, 500)
box.set_bgcolor(b, color.green)
```

---

## box.set_bgcolor()

Sets the background color of the box.

---

## box.set_border_color()

Sets the border color of the box.

---

## box.set_border_style()

Sets the border style of the box.

---

## box.set_border_width()

Sets the border width of the box.

---

## box.set_bottom()

Sets the bottom coordinate of the box.

---

## box.set_bottom_right_point()

Sets the bottom-right corner location of the id box to point.

---

## box.set_extend()

Sets extending type of the border of this box object. When extend.none is used, the horizontal borders start at the left border and end at the right border. With extend.left or extend.right, the horizontal borders are extended indefinitely to the left or right of the box, respectively. With extend.both, the horizontal borders are extended on both sides.

---

## box.set_left()

Sets the left coordinate of the box.

---

## box.set_lefttop()

Sets the left and top coordinates of the box.

---

## box.set_right()

Sets the right coordinate of the box.

---

## box.set_rightbottom()

Sets the right and bottom coordinates of the box.

---

## box.set_text()

The function sets the text in the box.

---

## box.set_text_color()

The function sets the color of the text inside the box.

---

## box.set_text_font_family()

The function sets the font family of the text inside the box.

### Code Example
```pine
//@version=6
indicator("Example of setting the box font")
if barstate.islastconfirmedhistory
    b = box.new(bar_index, open-ta.tr, bar_index-50, open-ta.tr*5, text="monospace")
    box.set_text_font_family(b, font.family_monospace)
```

---

## box.set_text_formatting()

Sets the formatting attributes the drawing applies to displayed text.

---

## box.set_text_halign()

The function sets the horizontal alignment of the box's text.

---

## box.set_text_size()

The function sets the size of the box's text.

---

## box.set_text_valign()

The function sets the vertical alignment of a box's text.

---

## box.set_text_wrap()

The function sets the mode of wrapping of the text inside the box.

---

## box.set_top()

Sets the top coordinate of the box.

---

## box.set_top_left_point()

Sets the top-left corner location of the id box to point.

---

## box.set_xloc()

Sets the left and right borders of a box and updates its xloc property.

---

## fill()

Fills background between two plots or hlines with a given color.

### Code Example
```pine
//@version=6
indicator("Fill between hlines", overlay = false)
h1 = hline(20)
h2 = hline(10)
fill(h1, h2, color = color.new(color.blue, 90))

//@version=6
indicator("Fill between plots", overlay = true)
p1 = plot(open)
p2 = plot(close)
fill(p1, p2, color = color.new(color.green, 90))

//@version=6
indicator("Gradient Fill between hlines", overlay = false)
topVal = input.int(100)
botVal = input.int(0)
topCol = input.color(color.red)
botCol = input.color(color.blue)
topLine = hline(100, color = topCol, linestyle = hline.style_solid)
botLine = hline(0,   color = botCol, linestyle = hline.style_solid)
fill(topLine, botLine, topVal, botVal, topCol, botCol)
```

---

## hline()

Renders a horizontal line at a given fixed price level.

### Returns
An hline object, that can be used in fill

### Code Example
```pine
//@version=6
indicator("input.hline", overlay=true)
hline(3.14, title='Pi', color=color.blue, linestyle=hline.style_dotted, linewidth=2)

// You may fill the background between any two hlines with a fill() function:
h1 = hline(20)
h2 = hline(10)
fill(h1, h2, color=color.new(color.green, 90))
```

---

## label()

Casts na to label

### Returns
The value of the argument after casting to label.

---

## label.copy()

Clones the label object.

### Returns
New label ID object which may be passed to label.setXXX and label.getXXX functions.

### Code Example
```pine
//@version=6
indicator('Last 100 bars highest/lowest', overlay = true)
LOOKBACK = 100
highest = ta.highest(LOOKBACK)
highestBars = ta.highestbars(LOOKBACK)
lowest = ta.lowest(LOOKBACK)
lowestBars = ta.lowestbars(LOOKBACK)
if barstate.islastconfirmedhistory
    var labelHigh = label.new(bar_index + highestBars, highest, str.tostring(highest), color = color.green)
    var labelLow = label.copy(labelHigh)
    label.set_xy(labelLow, bar_index + lowestBars, lowest)
    label.set_text(labelLow, str.tostring(lowest))
    label.set_color(labelLow, color.red)
    label.set_style(labelLow, label.style_label_up)
```

---

## label.delete()

Deletes the specified label object. If it has already been deleted, does nothing.

---

## label.get_text()

Returns the text of this label object.

### Returns
String object containing the text of this label.

### Code Example
```pine
//@version=6
indicator("label.get_text")
my_label = label.new(time, open, text="Open bar text", xloc=xloc.bar_time)
a = label.get_text(my_label)
label.new(time, close, text = a + " new", xloc=xloc.bar_time)
```

---

## label.get_x()

Returns UNIX time or bar index (depending on the last xloc value set) of this label's position.

### Returns
UNIX timestamp (in milliseconds) or bar index.

### Code Example
```pine
//@version=6
indicator("label.get_x")
my_label = label.new(time, open, text="Open bar text", xloc=xloc.bar_time)
a = label.get_x(my_label)
plot(time - label.get_x(my_label)) //draws zero plot
```

---

## label.get_y()

Returns price of this label's position.

### Returns
Floating point value representing price.

---

## label.new()

Creates new label object.

### Returns
Label ID object which may be passed to label.setXXX and label.getXXX functions.

### Code Example
```pine
//@version=6
indicator("label.new")
var label1 = label.new(bar_index, low, text="Hello, world!", style=label.style_circle)
label.set_x(label1, 0)
label.set_xloc(label1, time, xloc.bar_time)
label.set_color(label1, color.red)
label.set_size(label1, size.large)
```

---

## label.set_color()

Sets label border and arrow color.

---

## label.set_point()

Sets the location of the id label to point.

---

## label.set_size()

Sets arrow and text size of the specified label object.

---

## label.set_style()

Sets label style.

---

## label.set_text()

Sets label text

---

## label.set_text_font_family()

The function sets the font family of the text inside the label.

### Code Example
```pine
//@version=6
indicator("Example of setting the label font")
if barstate.islastconfirmedhistory
    l = label.new(bar_index, 0, "monospace", yloc=yloc.abovebar)
    label.set_text_font_family(l, font.family_monospace)
```

---

## label.set_text_formatting()

Sets the formatting attributes the drawing applies to displayed text.

---

## label.set_textalign()

Sets the alignment for the label text.

---

## label.set_textcolor()

Sets color of the label text.

---

## label.set_tooltip()

Sets the tooltip text.

---

## label.set_x()

Sets bar index or bar time (depending on the xloc) of the label position.

---

## label.set_xloc()

Sets x-location and new bar index/time value.

---

## label.set_xy()

Sets bar index/time and price of the label position.

---

## label.set_y()

Sets price of the label position

---

## label.set_yloc()

Sets new y-location calculation algorithm.

---

## line()

Casts na to line

### Returns
The value of the argument after casting to line.

---

## line.copy()

Clones the line object.

### Returns
New line ID object which may be passed to line.setXXX and line.getXXX functions.

### Code Example
```pine
//@version=6
indicator('Last 100 bars price range', overlay = true)
LOOKBACK = 100
highest = ta.highest(LOOKBACK)
lowest = ta.lowest(LOOKBACK)
if barstate.islastconfirmedhistory
    var lineTop = line.new(bar_index[LOOKBACK], highest, bar_index, highest, color = color.green)
    var lineBottom = line.copy(lineTop)
    line.set_y1(lineBottom, lowest)
    line.set_y2(lineBottom, lowest)
    line.set_color(lineBottom, color.red)
```

---

## line.delete()

Deletes the specified line object. If it has already been deleted, does nothing.

---

## line.get_price()

Returns the price level of a line at a given bar index.

### Returns
Price value of line 'id' at bar index 'x'.

### Remarks
The line is considered to have been created using 'extend=extend.both'. This function can only be called for lines created using 'xloc.bar_index'. If you try to call it for a line created with 'xloc.bar_time', it will generate an error.

### Code Example
```pine
//@version=6
indicator("GetPrice", overlay=true)
var line l = na
if bar_index == 10
    l := line.new(0, high[5], bar_index, high)
plot(line.get_price(l, bar_index), color=color.green)
```

---

## line.get_x1()

Returns UNIX time or bar index (depending on the last xloc value set) of the first point of the line.

### Returns
UNIX timestamp (in milliseconds) or bar index.

### Code Example
```pine
//@version=6
indicator("line.get_x1")
my_line = line.new(time, open, time + 60 * 60 * 24, close, xloc=xloc.bar_time)
a = line.get_x1(my_line)
plot(time - line.get_x1(my_line)) //draws zero plot
```

---

## line.get_x2()

Returns UNIX time or bar index (depending on the last xloc value set) of the second point of the line.

### Returns
UNIX timestamp (in milliseconds) or bar index.

---

## line.get_y1()

Returns price of the first point of the line.

### Returns
Price value.

---

## line.get_y2()

Returns price of the second point of the line.

### Returns
Price value.

---

## line.new()

Creates new line object.

### Returns
Line ID object which may be passed to line.setXXX and line.getXXX functions.

### Code Example
```pine
//@version=6
indicator("line.new")
var line1 = line.new(0, low, bar_index, high, extend=extend.right)
var line2 = line.new(time, open, time + 60 * 60 * 24, close, xloc=xloc.bar_time, style=line.style_dashed)
line.set_x2(line1, 0)
line.set_xloc(line1, time, time + 60 * 60 * 24, xloc.bar_time)
line.set_color(line2, color.green)
line.set_width(line2, 5)
```

---

## line.set_color()

Sets the line color

---

## line.set_extend()

Sets extending type of this line object. If extend=extend.none, draws segment starting at point (x1, y1) and ending at point (x2, y2). If extend is equal to extend.right or extend.left, draws a ray starting at point (x1, y1) or (x2, y2), respectively. If extend=extend.both, draws a straight line that goes through these points.

---

## line.set_first_point()

Sets the first point of the id line to point.

---

## line.set_second_point()

Sets the second point of the id line to point.

---

## line.set_style()

Sets the line style

---

## line.set_width()

Sets the line width.

---

## line.set_x1()

Sets bar index or bar time (depending on the xloc) of the first point.

---

## line.set_x2()

Sets bar index or bar time (depending on the xloc) of the second point.

---

## line.set_xloc()

Sets x-location and new bar index/time values.

---

## line.set_xy1()

Sets bar index/time and price of the first point.

---

## line.set_xy2()

Sets bar index/time and price of the second point

---

## line.set_y1()

Sets price of the first point

---

## line.set_y2()

Sets price of the second point.

---

## linefill()

Casts na to linefill.

### Returns
The value of the argument after casting to linefill.

---

## linefill.delete()

Deletes the specified linefill object. If it has already been deleted, does nothing.

---

## linefill.get_line1()

Returns the ID of the first line used in the id linefill.

---

## linefill.get_line2()

Returns the ID of the second line used in the id linefill.

---

## linefill.new()

Creates a new linefill object and displays it on the chart, filling the space between line1 and line2 with the color specified in color.

### Returns
The ID of a linefill object that can be passed to other linefill.*() functions.

### Remarks
If any line of the two is deleted, the linefill object is also deleted. If the lines are moved (e.g. via line.set_xy functions), the linefill object is also moved. If both lines are extended in the same direction relative to the lines themselves (e.g. both have extend.right as the value of their extend= parameter), the space between line extensions will also be filled.

---

## linefill.set_color()

The function sets the color of the linefill object passed to it.

---

## plot()

Plots a series of data on the chart.

### Returns
A plot object, that can be used in fill

### Code Example
```pine
//@version=6
indicator("plot")
plot(high+low, title='Title', color=color.new(#00ffaa, 70), linewidth=2, style=plot.style_area, offset=15, trackprice=true)

// You may fill the background between any two plots with a fill() function:
p1 = plot(open)
p2 = plot(close)
fill(p1, p2, color=color.new(color.green, 90))
```

---

## polyline.delete()

Deletes the specified polyline object. It has no effect if the id doesn't exist.

---

## polyline.new()

Creates a new polyline instance and displays it on the chart, sequentially connecting all of the points in the points array with line segments. The segments in the drawing can be straight or curved depending on the curved parameter.

### Returns
The ID of a new polyline object that a script can use in other polyline.*() functions.

### Code Example
```pine
//@version=6
indicator("Polylines example", overlay = true)

//@variable If `true`, connects all points in the polyline with curved line segments. 
bool curvedInput = input.bool(false, "Curve Polyline")
//@variable If `true`, connects the first point in the polyline to the last point.
bool closedInput = input.bool(true, "Close Polyline")
//@variable The color of the space filled by the polyline.
color fillcolor = input.color(color.new(color.blue, 90), "Fill Color")

// Time and price inputs for the polyline's points. 
p1x = input.time(0,  "p1", confirm = true, inline = "p1")
p1y = input.price(0, "  ", confirm = true, inline = "p1")
p2x = input.time(0,  "p2", confirm = true, inline = "p2")
p2y = input.price(0, "  ", confirm = true, inline = "p2")
p3x = input.time(0,  "p3", confirm = true, inline = "p3")
p3y = input.price(0, "  ", confirm = true, inline = "p3")
p4x = input.time(0,  "p4", confirm = true, inline = "p4")
p4y = input.price(0, "  ", confirm = true, inline = "p4")
p5x = input.time(0,  "p5", confirm = true, inline = "p5")
p5y = input.price(0, "  ", confirm = true, inline = "p5")

if barstate.islastconfirmedhistory
    //@variable An array of `chart.point` objects for the new polyline.
    var points = array.new<chart.point>()
    // Push new `chart.point` instances into the `points` array.
    points.push(chart.point.from_time(p1x, p1y))
    points.push(chart.point.from_time(p2x, p2y))
    points.push(chart.point.from_time(p3x, p3y))
    points.push(chart.point.from_time(p4x, p4y))
    points.push(chart.point.from_time(p5x, p5y))
    // Add labels for each `chart.point` in `points`.
    l1p1 = label.new(points.get(0), text = "p1", xloc = xloc.bar_time, color = na)
    l1p2 = label.new(points.get(1), text = "p2", xloc = xloc.bar_time, color = na)
    l2p1 = label.new(points.get(2), text = "p3", xloc = xloc.bar_time, color = na)
    l2p2 = label.new(points.get(3), text = "p4", xloc = xloc.bar_time, color = na)
    // Create a new polyline that connects each `chart.point` in the `points` array, starting from the first.
    polyline.new(points, curved = curvedInput, closed = closedInput, fill_color = fillcolor, xloc = xloc.bar_time)
```

---

## table()

Casts na to table

### Returns
The value of the argument after casting to table.

---

## table.cell()

The function defines a cell in the table and sets its attributes.

### Remarks
This function does not create the table itself, but defines the table’s cells. To use it, you first need to create a table object with table.new. Each table.cell call overwrites all previously defined properties of a cell. If you call table.cell twice in a row, e.g., the first time with text='Test Text', and the second time with text_color=color.red but without a new text argument, the default value of the 'text' being an empty string, it will overwrite 'Test Text', and your cell will display an empty string. If you want, instead, to modify any of the cell's properties, use the table.cell_set_*() functions. A single script can only display one table in each of the possible locations. If table.cell is used on several bars to change the same attribute of a cell (e.g. change the background color of the cell to red on the first bar, then to yellow on the second bar), only the last change will be reflected in the table, i.e., the cell’s background will be yellow. Avoid unnecessary setting of cell properties by enclosing function calls in an if barstate.islast block whenever possible, to restrict their execution to the last bar of the series.

---

## table.cell_set_bgcolor()

The function sets the background color of the cell.

---

## table.cell_set_height()

The function sets the height of cell.

---

## table.cell_set_text()

The function sets the text in the specified cell.

### Code Example
```pine
//@version=6
indicator("TABLE example")
var tLog = table.new(position = position.top_left, rows = 1, columns = 2, bgcolor = color.yellow, border_width=1)
table.cell(tLog, row = 0, column = 0, text = "sometext", text_color = color.blue)
table.cell_set_text(tLog, row = 0, column = 0, text = "sometext")
```

---

## table.cell_set_text_color()

The function sets the color of the text inside the cell.

---

## table.cell_set_text_font_family()

The function sets the font family of the text inside the cell.

### Code Example
```pine
//@version=6
indicator("Example of setting the table cell font")
var t = table.new(position.top_left, rows = 1, columns = 1)
table.cell(t, 0, 0, "monospace", text_color = color.blue)
table.cell_set_text_font_family(t, 0, 0, font.family_monospace)
```

---

## table.cell_set_text_formatting()

Sets the formatting attributes the drawing applies to displayed text.

---

## table.cell_set_text_halign()

The function sets the horizontal alignment of the cell's text.

---

## table.cell_set_text_size()

The function sets the size of the cell's text.

---

## table.cell_set_text_valign()

The function sets the vertical alignment of a cell's text.

---

## table.cell_set_tooltip()

The function sets the tooltip in the specified cell.

### Code Example
```pine
//@version=6
indicator("TABLE example")
var tLog = table.new(position = position.top_left, rows = 1, columns = 2, bgcolor = color.yellow, border_width=1)
table.cell(tLog, row = 0, column = 0, text = "sometext", text_color = color.blue)
table.cell_set_tooltip(tLog, row = 0, column = 0, tooltip = "sometext")
```

---

## table.cell_set_width()

The function sets the width of the cell.

---

## table.clear()

The function removes a cell or a sequence of cells from the table. The cells are removed in a rectangle shape where the start_column and start_row specify the top-left corner, and end_column and end_row specify the bottom-right corner.

### Code Example
```pine
//@version=6
indicator("A donut", overlay=true)
if barstate.islast
    colNum = 8, rowNum = 8
    padding = "◯"
    donutTable = table.new(position.middle_right, colNum, rowNum)
    for c = 0 to colNum - 1
        for r = 0 to rowNum - 1
            table.cell(donutTable, c, r, text=padding, bgcolor=#face6e, text_color=color.new(color.black, 100))
    table.clear(donutTable, 2, 2, 5, 5)
```

---

## table.delete()

The function deletes a table.

### Code Example
```pine
//@version=6
indicator("table.delete example")
var testTable = table.new(position = position.top_right, columns = 2, rows = 1, bgcolor = color.yellow, border_width = 1)
if barstate.islast
    table.cell(table_id = testTable, column = 0, row = 0, text = "Open is " + str.tostring(open))
    table.cell(table_id = testTable, column = 1, row = 0, text = "Close is " + str.tostring(close), bgcolor=color.teal)
if barstate.isrealtime
    table.delete(testTable)
```

---

## table.merge_cells()

The function merges a sequence of cells in the table into one cell. The cells are merged in a rectangle shape where the start_column and start_row specify the top-left corner, and end_column and end_row specify the bottom-right corner.

### Remarks
This function will merge cells, even if their properties are not yet defined with table.cell. The resulting merged cell inherits all of its values from the cell located at start_column:start_row, except width and height. The width and height of the resulting merged cell are based on the width/height of other cells in the neighboring columns/rows and cannot be set manually. To modify the merged cell with any of the table.cell_set_* functions, target the cell at the start_column:start_row coordinates. An attempt to merge a cell that has already been merged will result in an error.

### Code Example
```pine
//@version=6
indicator("table.merge_cells example")
SMA50  = ta.sma(close, 50)
SMA100 = ta.sma(close, 100)
SMA200 = ta.sma(close, 200)
if barstate.islast
    maTable = table.new(position.bottom_right, 3, 3, bgcolor = color.gray, border_width = 1, border_color = color.black)
    // Header
    table.cell(maTable, 0, 0, text = "SMA Table")
    table.merge_cells(maTable, 0, 0, 2, 0)
    // Cell Titles
    table.cell(maTable, 0, 1, text = "SMA 50")
    table.cell(maTable, 1, 1, text = "SMA 100")
    table.cell(maTable, 2, 1, text = "SMA 200")
    // Values
    table.cell(maTable, 0, 2, bgcolor = color.white, text = str.tostring(SMA50))
    table.cell(maTable, 1, 2, bgcolor = color.white, text = str.tostring(SMA100))
    table.cell(maTable, 2, 2, bgcolor = color.white, text = str.tostring(SMA200))
```

---

## table.new()

The function creates a new table.

### Returns
The ID of a table object that can be passed to other table.*() functions.

### Remarks
This function creates the table object itself, but the table will not be displayed until its cells are populated. To define a cell and change its contents or attributes, use table.cell and other table.cell_*() functions. One table.new call can only display one table (the last one drawn), but the function itself will be recalculated on each bar it is used on. For performance reasons, it is wise to use table.new in conjunction with either the var keyword (so the table object is only created on the first bar) or in an if barstate.islast block (so the table object is only created on the last bar).

### Code Example
```pine
//@version=6
indicator("table.new example")
var testTable = table.new(position = position.top_right, columns = 2, rows = 1, bgcolor = color.yellow, border_width = 1)
if barstate.islast
    table.cell(table_id = testTable, column = 0, row = 0, text = "Open is " + str.tostring(open))
    table.cell(table_id = testTable, column = 1, row = 0, text = "Close is " + str.tostring(close), bgcolor=color.teal)
```

---

## table.set_bgcolor()

The function sets the background color of a table.

---

## table.set_border_color()

The function sets the color of the borders (excluding the outer frame) of the table's cells.

---

## table.set_border_width()

The function sets the width of the borders (excluding the outer frame) of the table's cells.

---

## table.set_frame_color()

The function sets the color of the outer frame of a table.

---

## table.set_frame_width()

The function set the width of the outer frame of a table.

---

## table.set_position()

The function sets the position of a table.

---

