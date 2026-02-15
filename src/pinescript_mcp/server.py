#!/usr/bin/env python3
"""
Pine Script v6 Documentation MCP Server

Provides tools to list, search, and read Pine Script v6 documentation.
"""

import json
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("pinescript-docs")

# Path resolution - support both installed package and development
# For Python 3.10+, use importlib.resources
try:
    if sys.version_info >= (3, 11):
        from importlib.resources import files
        _pkg_files = files("pinescript_mcp")
        DOCS_ROOT = Path(str(_pkg_files.joinpath("docs")))
    else:
        # Python 3.10 fallback
        from importlib.resources import files
        import importlib.resources as pkg_resources
        _pkg_files = files("pinescript_mcp")
        DOCS_ROOT = Path(str(_pkg_files.joinpath("docs")))
except (ImportError, TypeError, ModuleNotFoundError):
    # Fallback for development mode
    DOCS_ROOT = Path(__file__).parent / "docs"

# Allowed directories for reading docs
ALLOWED_DIRS = ["concepts", "reference", "writing_scripts", "visuals"]

# Path to functions JSON
FUNCTIONS_JSON = DOCS_ROOT / "pine_v6_functions.json"


def _load_functions() -> tuple[set, set, set]:
    """Load function data from JSON file."""
    if not FUNCTIONS_JSON.exists():
        return set(), set(), set()
    try:
        data = json.loads(FUNCTIONS_JSON.read_text(encoding="utf-8"))
        return (
            set(data.get("functions", [])),
            set(data.get("namespaces", [])),
            set(data.get("toplevel", [])),
        )
    except (json.JSONDecodeError, KeyError):
        return set(), set(), set()


PINE_V6_FUNCTIONS, PINE_V6_NAMESPACES, PINE_V6_TOPLEVEL = _load_functions()

# Documentation index with descriptions
DOCS = {
    # Concepts
    "concepts/execution_model.md": "Bar-by-bar execution, var, varip, history vs realtime",
    "concepts/timeframes.md": "Multi-timeframe data, request.security, repainting prevention",
    "concepts/colors_and_display.md": "Colors, gradients, transparency, color.new, bgcolor",
    "concepts/common_errors.md": "Runtime and compile-time error explanations",
    "concepts/methods.md": "User-defined methods, method declarations, extending types",
    "concepts/objects.md": "User-defined types (UDT), type keyword, object-oriented patterns",
    # Reference
    "reference/variables.md": "Built-in variables: open, high, low, close, volume, syminfo",
    "reference/constants.md": "Fixed constants: color.red, shape.*, plot.style_*, size.*",
    "reference/types.md": "Type system: int, float, bool, series, simple, const",
    "reference/keywords.md": "Language keywords: if, else, for, while, var, varip, switch",
    "reference/operators.md": "Arithmetic, comparison, logical, ternary operators",
    "reference/annotations.md": "Library annotations: @description, @function, @param, @returns, export",
    "reference/pine_v6_cheatsheet.md": "Compact v6 reference with common pitfalls",
    # Functions
    "reference/functions/ta.md": "Technical analysis: ta.rsi, ta.sma, ta.ema, ta.macd, ta.crossover",
    "reference/functions/strategy.md": "Backtesting: strategy.entry, strategy.exit, strategy.close",
    "reference/functions/request.md": "External data: request.security, request.financial",
    "reference/functions/drawing.md": "Visuals: plot, plotshape, line.new, box.new, label.new, table",
    "reference/functions/collections.md": "Arrays, maps, matrices: array.new, map.new, matrix.new",
    "reference/functions/general.md": "Math, strings, inputs: math.abs, str.format, input.int",
    # Visuals
    "visuals/overview.md": "Visual outputs overview, chart graphics concepts",
    "visuals/plots.md": "plot(), plotcandle(), plotbar() functions",
    "visuals/backgrounds.md": "bgcolor(), background coloring techniques",
    "visuals/bar_coloring.md": "barcolor(), coloring price bars",
    "visuals/bar_plotting.md": "plotcandle(), plotbar() for custom OHLC",
    "visuals/colors.md": "Color functions, color.new(), color.rgb()",
    "visuals/fills.md": "fill() between plots and hlines",
    "visuals/levels.md": "hline(), horizontal levels",
    "visuals/lines_and_boxes.md": "line.new(), box.new() drawing objects",
    "visuals/tables.md": "table.new(), table.cell() for data display",
    "visuals/texts_and_shapes.md": "label.new(), plotshape(), plotchar()",
    # Writing Scripts
    "writing_scripts/style_guide.md": "Naming conventions, code organization, best practices",
    "writing_scripts/debugging.md": "Debugging techniques, log.*, runtime.error()",
    "writing_scripts/limitations.md": "Pine Script limitations, max bars, memory limits",
    "writing_scripts/profiling_and_optimization.md": "Performance optimization, profiling tools",
    "writing_scripts/publishing_scripts.md": "Publishing to TradingView, script visibility",
}

# Topic mapping for resolve_topic() - keyword -> doc path
TOPIC_MAP = {
    # Execution & State
    "barstate": "concepts/execution_model.md",
    "var": "concepts/execution_model.md",
    "varip": "concepts/execution_model.md",
    "history": "concepts/execution_model.md",
    "realtime": "concepts/execution_model.md",
    "calc_on_every_tick": "concepts/execution_model.md",
    "execution model": "concepts/execution_model.md",
    "bar-by-bar": "concepts/execution_model.md",
    # Repainting & MTF
    "repainting": "concepts/timeframes.md",
    "repaint": "concepts/timeframes.md",
    "lookahead": "concepts/timeframes.md",
    "request.security": "reference/functions/request.md",
    "htf": "concepts/timeframes.md",
    "multi-timeframe": "concepts/timeframes.md",
    "mtf": "concepts/timeframes.md",
    "timeframe": "concepts/timeframes.md",
    "higher timeframe": "concepts/timeframes.md",
    # Strategy
    "backtest": "reference/functions/strategy.md",
    "backtesting": "reference/functions/strategy.md",
    "strategy": "reference/functions/strategy.md",
    "entry": "reference/functions/strategy.md",
    "exit": "reference/functions/strategy.md",
    "trailing stop": "reference/functions/strategy.md",
    "stop loss": "reference/functions/strategy.md",
    "take profit": "reference/functions/strategy.md",
    "position size": "reference/functions/strategy.md",
    "order": "reference/functions/strategy.md",
    "trade": "reference/functions/strategy.md",
    "equity": "reference/functions/strategy.md",
    "drawdown": "reference/functions/strategy.md",
    "commission": "reference/functions/strategy.md",
    "slippage": "reference/functions/strategy.md",
    # Technical Analysis
    "rsi": "reference/functions/ta.md",
    "sma": "reference/functions/ta.md",
    "ema": "reference/functions/ta.md",
    "macd": "reference/functions/ta.md",
    "crossover": "reference/functions/ta.md",
    "crossunder": "reference/functions/ta.md",
    "indicator": "reference/functions/ta.md",
    "moving average": "reference/functions/ta.md",
    "pivot": "reference/functions/ta.md",
    "atr": "reference/functions/ta.md",
    "bollinger": "reference/functions/ta.md",
    "supertrend": "reference/functions/ta.md",
    "stochastic": "reference/functions/ta.md",
    "highest": "reference/functions/ta.md",
    "lowest": "reference/functions/ta.md",
    "vwap": "reference/functions/ta.md",
    # Drawing & Visuals
    "plot": "reference/functions/drawing.md",
    "plotshape": "reference/functions/drawing.md",
    "line": "reference/functions/drawing.md",
    "box": "reference/functions/drawing.md",
    "label": "reference/functions/drawing.md",
    "table": "reference/functions/drawing.md",
    "polyline": "reference/functions/drawing.md",
    "fill": "reference/functions/drawing.md",
    "hline": "reference/functions/drawing.md",
    "color": "concepts/colors_and_display.md",
    "bgcolor": "concepts/colors_and_display.md",
    "gradient": "concepts/colors_and_display.md",
    "transparency": "concepts/colors_and_display.md",
    # Collections
    "array": "reference/functions/collections.md",
    "matrix": "reference/functions/collections.md",
    "map": "reference/functions/collections.md",
    # Errors
    "error": "concepts/common_errors.md",
    "max_bars_back": "concepts/common_errors.md",
    "undeclared": "concepts/common_errors.md",
    "compile error": "concepts/common_errors.md",
    "runtime error": "concepts/common_errors.md",
    # Types & Keywords
    "type": "reference/types.md",
    "series": "reference/types.md",
    "simple": "reference/types.md",
    "const": "reference/types.md",
    "float": "reference/types.md",
    "int": "reference/types.md",
    "bool": "reference/types.md",
    "string": "reference/types.md",
    "input": "reference/functions/general.md",
    "alert": "reference/functions/general.md",
    "math": "reference/functions/general.md",
    "str.": "reference/functions/general.md",
    # Built-ins
    "open": "reference/variables.md",
    "close": "reference/variables.md",
    "high": "reference/variables.md",
    "low": "reference/variables.md",
    "volume": "reference/variables.md",
    "syminfo": "reference/variables.md",
    "bar_index": "reference/variables.md",
    "time": "reference/variables.md",
    "ohlc": "reference/variables.md",
    # Keywords
    "if": "reference/keywords.md",
    "for": "reference/keywords.md",
    "while": "reference/keywords.md",
    "switch": "reference/keywords.md",
    "import": "reference/keywords.md",
    "export": "reference/keywords.md",
    "method": "reference/keywords.md",
    # Libraries & Annotations
    "library": "reference/annotations.md",
    "libraries": "reference/annotations.md",
    "@description": "reference/annotations.md",
    "@function": "reference/annotations.md",
    "@param": "reference/annotations.md",
    "@returns": "reference/annotations.md",
    "annotation": "reference/annotations.md",
    # Methods & Objects
    "method": "concepts/methods.md",
    "methods": "concepts/methods.md",
    "udt": "concepts/objects.md",
    "user-defined type": "concepts/objects.md",
    "object": "concepts/objects.md",
    "objects": "concepts/objects.md",
    "type keyword": "concepts/objects.md",
    # Operators
    "operator": "reference/operators.md",
    "operators": "reference/operators.md",
    "ternary": "reference/operators.md",
    "arithmetic": "reference/operators.md",
    "comparison": "reference/operators.md",
    "logical": "reference/operators.md",
    # Visuals (detailed)
    "plotcandle": "visuals/bar_plotting.md",
    "plotbar": "visuals/bar_plotting.md",
    "barcolor": "visuals/bar_coloring.md",
    "linefill": "visuals/fills.md",
    # Writing Scripts
    "debug": "writing_scripts/debugging.md",
    "debugging": "writing_scripts/debugging.md",
    "log.info": "writing_scripts/debugging.md",
    "log.warning": "writing_scripts/debugging.md",
    "log.error": "writing_scripts/debugging.md",
    "limitation": "writing_scripts/limitations.md",
    "limitations": "writing_scripts/limitations.md",
    "max bars": "writing_scripts/limitations.md",
    "memory": "writing_scripts/limitations.md",
    "optimization": "writing_scripts/profiling_and_optimization.md",
    "profiling": "writing_scripts/profiling_and_optimization.md",
    "performance": "writing_scripts/profiling_and_optimization.md",
    "publish": "writing_scripts/publishing_scripts.md",
    "publishing": "writing_scripts/publishing_scripts.md",
    "style guide": "writing_scripts/style_guide.md",
    "naming convention": "writing_scripts/style_guide.md",
    "best practice": "writing_scripts/style_guide.md",
}


def _find_section(content: str, header: str, include_children: bool = True) -> tuple[str, int, int]:
    """Find a section in markdown content by header text.

    Returns (section_content, start_line, end_line) or raises ValueError.
    """
    lines = content.splitlines()

    # Normalize header query (strip leading #'s if present)
    header_text = re.sub(r'^#+\s*', '', header).strip().lower()

    start_idx = None
    start_level = None

    for i, line in enumerate(lines):
        if line.startswith('#'):
            # Parse header level and text
            match = re.match(r'^(#+)\s*(.+)', line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip().lower()

                if start_idx is None:
                    # Looking for start
                    if header_text in text or text in header_text:
                        start_idx = i
                        start_level = level
                else:
                    # Looking for end
                    if include_children:
                        # Stop at same level or higher (smaller number)
                        if level <= start_level:
                            return '\n'.join(lines[start_idx:i]), start_idx + 1, i
                    else:
                        # Stop at any header
                        return '\n'.join(lines[start_idx:i]), start_idx + 1, i

    if start_idx is not None:
        # Section goes to end of file
        return '\n'.join(lines[start_idx:]), start_idx + 1, len(lines)

    raise ValueError(f"Header not found: {header}")


def _validate_path(path: str) -> Path:
    """Validate and resolve a documentation path. Raises ValueError if invalid."""
    # Normalize path
    clean_path = path.lstrip("/").lstrip("./")

    # Check for path traversal
    if ".." in clean_path:
        raise ValueError(f"Invalid path: {path}")

    # Check if in allowed directory
    allowed = any(clean_path.startswith(d) for d in ALLOWED_DIRS)
    if not allowed:
        raise ValueError(f"Path not in allowed directories: {path}")

    full_path = DOCS_ROOT / clean_path

    # Verify path is within docs root
    try:
        full_path.resolve().relative_to(DOCS_ROOT.resolve())
    except ValueError:
        raise ValueError(f"Path escapes documentation root: {path}")

    if not full_path.exists():
        raise ValueError(f"File not found: {path}")

    return full_path


@mcp.tool()
def list_docs() -> str:
    """List all available Pine Script v6 documentation files with descriptions.

    Returns a formatted list of documentation files organized by category.
    Use get_doc(path) to read a specific file.
    """
    output = ["# Pine Script v6 Documentation", ""]

    # Group by category (ordered dict to preserve display order)
    categories = {
        "Concepts": [],
        "Reference": [],
        "Functions": [],
        "Visuals": [],
        "Writing Scripts": [],
    }

    for path, desc in DOCS.items():
        if path.startswith("concepts/"):
            categories["Concepts"].append((path, desc))
        elif path.startswith("reference/functions/"):
            categories["Functions"].append((path, desc))
        elif path.startswith("reference/"):
            categories["Reference"].append((path, desc))
        elif path.startswith("visuals/"):
            categories["Visuals"].append((path, desc))
        elif path.startswith("writing_scripts/"):
            categories["Writing Scripts"].append((path, desc))

    for category, docs in categories.items():
        if docs:
            output.append(f"## {category}")
            for path, desc in docs:
                output.append(f"- `{path}`: {desc}")
            output.append("")

    return "\n".join(output)


@mcp.tool()
def get_doc(path: str, limit: int = 0, offset: int = 0) -> str:
    """Read a specific Pine Script v6 documentation file.

    Args:
        path: Relative path to the documentation file (e.g., "reference/functions/ta.md")
        limit: Maximum characters to return. Use 30000 for large files to avoid token limits.
        offset: Character offset to start reading from (default: 0)

    Returns the contents with metadata header showing total size and current slice.
    """
    try:
        full_path = _validate_path(path)
        content = full_path.read_text(encoding="utf-8")
        total = len(content)

        # Apply offset and limit if specified
        if limit > 0:
            end = min(offset + limit, total)
            content = content[offset:end]
            has_more = end < total
            header = f"# {path} (chars {offset}-{end} of {total})\n"
            if has_more:
                header += f"# Use offset={end} to continue reading\n"
            return header + "\n" + content
        else:
            return content
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
def get_section(path: str, header: str, include_children: bool = True) -> str:
    """Get a specific section from a documentation file by its header.

    Use this after search_docs() finds a header match. Eliminates offset guessing.

    Args:
        path: Documentation file path (e.g., "reference/functions/strategy.md")
        header: Header text to find (e.g., "strategy.exit()" or "## strategy.exit()")
        include_children: Include nested subsections under the header (default: True)

    Returns the section content from the header to the next same-level header.
    """
    try:
        full_path = _validate_path(path)
        content = full_path.read_text(encoding="utf-8")

        section, start_line, end_line = _find_section(content, header, include_children)

        header_info = f"# {path} (lines {start_line}-{end_line})\n\n"
        return header_info + section

    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
def search_docs(query: str, max_results: int = 10) -> str:
    """Grep for an exact string across all Pine Script v6 documentation.

    Use this for specific function names, syntax, or code patterns (e.g., "ta.sma", "strategy.exit").
    For natural language questions, use resolve_topic() instead.

    Args:
        query: Exact string to search for (case-insensitive). Use single terms, not phrases.
        max_results: Maximum number of results to return (default: 10)

    Returns matching lines with file paths and line numbers.
    """
    results = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for rel_path in DOCS.keys():
        full_path = DOCS_ROOT / rel_path
        if not full_path.exists():
            continue

        try:
            lines = full_path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    results.append({
                        "file": rel_path,
                        "line": i,
                        "content": line.strip()[:200]  # Truncate long lines
                    })
                    if len(results) >= max_results:
                        break
        except Exception:
            continue

        if len(results) >= max_results:
            break

    if not results:
        return f"No results found for: {query}"

    output = [f"# Search results for: {query}", f"Found {len(results)} matches", ""]
    for r in results:
        output.append(f"**{r['file']}:{r['line']}**")
        output.append(f"  {r['content']}")
        output.append("")

    return "\n".join(output)


@mcp.tool()
def get_manifest() -> str:
    """Get the LLM_MANIFEST.md file which provides routing guidance for Pine Script topics.

    This manifest maps topics to specific documentation files and includes
    routing logic examples for common queries.
    """
    manifest_path = DOCS_ROOT / "LLM_MANIFEST.md"
    if manifest_path.exists():
        return manifest_path.read_text(encoding="utf-8")
    return "Error: LLM_MANIFEST.md not found"


@mcp.tool()
def get_functions(namespace: str = "") -> str:
    """Get valid Pine Script v6 functions, optionally filtered by namespace.

    Args:
        namespace: Filter by namespace (e.g., "ta", "strategy", "request").
                   Empty string returns all functions grouped by namespace.

    Returns formatted list of functions. External agents can use this
    to ground their Pine Script generation and avoid hallucinated functions.
    """
    if not PINE_V6_FUNCTIONS:
        return (
            "Error: Function data not loaded. "
            "The pine_v6_functions.json file may be missing from the package."
        )

    if not namespace:
        # Build compact grouped format
        by_ns: dict[str, list[str]] = {}
        for fn in sorted(PINE_V6_FUNCTIONS):
            ns, _, name = fn.rpartition(".")
            by_ns.setdefault(ns, []).append(name)

        lines = [f"{ns}.*: {', '.join(sorted(fns))}" for ns, fns in sorted(by_ns.items())]
        lines.append(f"Top-level: {', '.join(sorted(PINE_V6_TOPLEVEL))}")
        return "\n".join(lines)

    # Filter by namespace
    prefix = f"{namespace}."
    matches = sorted(fn for fn in PINE_V6_FUNCTIONS if fn.startswith(prefix))

    if not matches:
        available = ", ".join(sorted(PINE_V6_NAMESPACES))
        return f"No functions found for namespace '{namespace}'. Available namespaces: {available}"

    return f"# {namespace}.* functions ({len(matches)} total)\n\n" + "\n".join(f"- {fn}" for fn in matches)


@mcp.tool()
def validate_function(fn_name: str) -> str:
    """Check if a Pine Script v6 function name is valid.

    Args:
        fn_name: Function name to validate (e.g., "ta.sma", "strategy.entry", "plot")

    Returns JSON with:
        - valid: boolean indicating if function exists
        - type: "namespaced", "toplevel", or null if invalid
        - suggestion: closest match if invalid (for typos)
    """
    fn_name = fn_name.strip()

    # Check namespaced functions
    if fn_name in PINE_V6_FUNCTIONS:
        return json.dumps({"valid": True, "type": "namespaced", "function": fn_name})

    # Check top-level functions
    if fn_name in PINE_V6_TOPLEVEL:
        return json.dumps({"valid": True, "type": "toplevel", "function": fn_name})

    # Not found - try to find a suggestion
    suggestion = None

    # Check if it's a namespace prefix typo (e.g., "ta.smaa" -> "ta.sma")
    if "." in fn_name:
        ns, _, _name = fn_name.rpartition(".")
        prefix = f"{ns}."
        candidates = [fn for fn in PINE_V6_FUNCTIONS if fn.startswith(prefix)]
        # Simple prefix match for suggestion
        for candidate in candidates:
            if candidate.startswith(fn_name[:len(fn_name)-1]):
                suggestion = candidate
                break
        # If no prefix match, just show the namespace exists
        if not suggestion and candidates:
            suggestion = f"namespace '{ns}' exists with {len(candidates)} functions"
    else:
        # Check top-level for partial match
        for fn in PINE_V6_TOPLEVEL:
            if fn.startswith(fn_name[:max(1, len(fn_name)-1)]):
                suggestion = fn
                break

    result = {"valid": False, "type": None, "function": fn_name}
    if suggestion:
        result["suggestion"] = suggestion
    return json.dumps(result)


@mcp.tool()
def resolve_topic(query: str) -> str:
    """Find the right documentation for a Pine Script question or concept.

    START HERE for most queries. Handles natural language and multi-word searches.
    Examples: "trailing stop loss", "how to prevent repainting", "OHLC variables"

    Args:
        query: Natural language query or keywords (e.g., "trailing stop", "repainting", "RSI")

    Returns JSON with matched documentation paths ranked by relevance.
    Use get_doc(path) to read the recommended files.
    """
    query_lower = query.lower()

    # Count matches per path
    path_scores: dict[str, list[str]] = {}

    for keyword, path in TOPIC_MAP.items():
        if keyword in query_lower:
            if path not in path_scores:
                path_scores[path] = []
            path_scores[path].append(keyword)

    if not path_scores:
        # No exact matches - try partial matching
        for keyword, path in TOPIC_MAP.items():
            # Check if any word in query starts with keyword or vice versa
            for word in query_lower.split():
                if word.startswith(keyword[:3]) or keyword.startswith(word[:3]):
                    if path not in path_scores:
                        path_scores[path] = []
                    path_scores[path].append(f"~{keyword}")
                    break

    if not path_scores:
        return json.dumps({
            "matches": [],
            "query": query,
            "suggestion": "Try search_docs(query) for full-text search"
        })

    # Sort by number of keyword matches (most relevant first)
    ranked = sorted(path_scores.items(), key=lambda x: len(x[1]), reverse=True)

    matches = [
        {"path": path, "matched_keywords": keywords, "score": len(keywords)}
        for path, keywords in ranked
    ]

    return json.dumps({
        "matches": matches,
        "query": query,
        "suggestion": f"Use get_doc('{matches[0]['path']}') to read the top match"
    })


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for container orchestration."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "server": "pinescript-docs"})


def main():
    """Entry point for the CLI."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Pine Script v6 MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server (SSE transport)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)),
                        help="HTTP port (default: 8000 or $PORT)")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host (default: 0.0.0.0)")
    args = parser.parse_args()

    if args.http:
        # Configure host/port for HTTP transport
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        # Disable DNS rebinding protection for public server
        mcp.settings.transport_security.enable_dns_rebinding_protection = False
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
