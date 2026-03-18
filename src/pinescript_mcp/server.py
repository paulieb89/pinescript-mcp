#!/usr/bin/env python3
"""
Pine Script v6 Documentation MCP Server

Provides tools to list, search, and read Pine Script v6 documentation.
"""

import json
import re
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP, Context
from fastmcp.server.middleware.caching import ResponseCachingMiddleware, CallToolSettings
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware
from fastmcp.utilities.logging import get_logger
from key_value.aio.stores.disk import DiskStore
from pydantic import BaseModel
import time
import os

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry

from pinescript_mcp import __version__

# ---------------------------------------------------------------------------
# Prometheus Metrics (scraped by Fly.io → fly-metrics.net Grafana)
# ---------------------------------------------------------------------------
METRICS_REGISTRY = CollectorRegistry()

tool_calls_total = Counter(
    "pinescript_tool_calls_total",
    "Total MCP tool calls",
    ["tool"],
    registry=METRICS_REGISTRY,
)
tool_errors_total = Counter(
    "pinescript_tool_errors_total",
    "Tool calls that raised exceptions",
    ["tool"],
    registry=METRICS_REGISTRY,
)
tool_duration_seconds = Histogram(
    "pinescript_tool_duration_seconds",
    "Tool call duration in seconds",
    ["tool"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=METRICS_REGISTRY,
)

# Optional: pynescript for AST-based syntax validation
try:
    from pynescript.ast import parse as pine_parse
    from pynescript.ast.error import SyntaxError as PineSyntaxError
    HAS_PYNESCRIPT = True
except ImportError:
    HAS_PYNESCRIPT = False


# ---------------------------------------------------------------------------
# Pydantic Models for Structured Output
# ---------------------------------------------------------------------------

class LintIssue(BaseModel):
    """A single lint issue found in Pine Script code."""
    line: int
    rule: str
    message: str
    severity: Literal["error", "warning"]
    column: int | None = None  # Optional: column for syntax errors


class LintResult(BaseModel):
    """Result of linting Pine Script code."""
    status: Literal["ok", "issues_found"]
    count: int
    issues: list[LintIssue]


class ValidationResult(BaseModel):
    """Result of validating a Pine Script function name."""
    valid: bool
    type: Literal["namespaced", "toplevel"] | None
    function: str
    suggestion: str | None = None


class TopicMatch(BaseModel):
    """A matched documentation topic."""
    path: str
    matched_keywords: list[str]
    score: int
    read_with: list[str] = []


class ResolveResult(BaseModel):
    """Result of resolving a topic query."""
    matches: list[TopicMatch]
    query: str
    suggestion: str

# Cache directory for persistent response caching (survives Fly.io suspend)
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/pinescript-cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize MCP server
mcp = FastMCP("pinescript-docs")

# ---------------------------------------------------------------------------
# Production Middleware Stack (order matters: first added = outermost)
# ---------------------------------------------------------------------------

# 1. Rate limiting - protect from abuse (generous for docs server)
mcp.add_middleware(RateLimitingMiddleware(
    max_requests_per_second=10.0,  # 10 sustained req/s
    burst_capacity=50,             # Allow bursts up to 50
))

# 2. Structured logging - JSON logs for Fly.io log aggregation
mcp.add_middleware(StructuredLoggingMiddleware(
    include_payloads=False,        # Don't log full payloads (keeps logs compact)
))

# 3. Response limiting - prevent overwhelming client context
mcp.add_middleware(ResponseLimitingMiddleware(
    max_size=200_000,              # 200KB limit
))

# 4. Response caching with disk persistence (survives restarts)
mcp.add_middleware(ResponseCachingMiddleware(
    cache_storage=DiskStore(directory=str(CACHE_DIR)),
    call_tool_settings=CallToolSettings(
        ttl=3600,  # 1 hour
        included_tools=["get_doc", "get_section", "list_docs", "get_manifest", "list_sections"]
    )
))


_logger = get_logger("pinescript_mcp.tools")


class _timed_tool:
    """Context manager for tool timing and logging.

    Usage:
        with _timed_tool("get_doc", path=path) as log:
            ...
            log["chars"] = len(content)  # add extra fields
    """
    def __init__(self, tool_name: str, **kwargs):
        self._tool_name = tool_name
        self._extra = kwargs
        self._data: dict = {}

    def __enter__(self):
        self._start = time.time()
        self._data = {}
        return self._data

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self._start
        tool_calls_total.labels(tool=self._tool_name).inc()
        tool_duration_seconds.labels(tool=self._tool_name).observe(duration)
        if exc_type is not None:
            tool_errors_total.labels(tool=self._tool_name).inc()
        log_data = {
            "event": "tool_call",
            "tool": self._tool_name,
            **self._extra,
            **self._data,
            "duration_ms": int(duration * 1000),
        }
        _logger.info(json.dumps(log_data))
        return False

# Path resolution - support both installed package and development
try:
    from importlib.resources import files
    DOCS_ROOT = Path(str(files("pinescript_mcp").joinpath("docs")))
except (ImportError, TypeError, ModuleNotFoundError):
    DOCS_ROOT = Path(__file__).parent / "docs"

# Allowed directories for reading docs
ALLOWED_DIRS = ["concepts", "reference", "writing_scripts", "visuals"]

# Path to functions JSON
FUNCTIONS_JSON = DOCS_ROOT / "pine_v6_functions.json"

# Large docs that benefit from section-level retrieval
LARGE_DOCS = {
    "reference/functions/ta.md",
    "reference/functions/strategy.md",
    "reference/functions/collections.md",
    "reference/functions/drawing.md",
    "reference/functions/general.md",
    "concepts/execution_model.md",
}

# Known doc combinations — companion docs to read alongside a match
DOC_COMPANIONS = {
    "reference/functions/strategy.md": ["concepts/execution_model.md"],
    "reference/functions/request.md": ["concepts/timeframes.md"],
}


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
    # Migration
    "reference/migration_v5_to_v6.md": "v5 to v6 migration guide, breaking changes, renamed functions",
}

# Topic mapping for resolve_topic() — exact Pine Script API terms only.
# Natural language routing is handled by the LLM reading get_manifest().
TOPIC_MAP = {
    # Technical Analysis — exact function prefixes
    "ta.rsi": "reference/functions/ta.md",
    "ta.sma": "reference/functions/ta.md",
    "ta.ema": "reference/functions/ta.md",
    "ta.macd": "reference/functions/ta.md",
    "ta.crossover": "reference/functions/ta.md",
    "ta.crossunder": "reference/functions/ta.md",
    "ta.atr": "reference/functions/ta.md",
    "ta.vwap": "reference/functions/ta.md",
    "ta.supertrend": "reference/functions/ta.md",
    "ta.stoch": "reference/functions/ta.md",
    "ta.highest": "reference/functions/ta.md",
    "ta.lowest": "reference/functions/ta.md",
    "ta.pivothigh": "reference/functions/ta.md",
    "ta.pivotlow": "reference/functions/ta.md",
    "ta.bb": "reference/functions/ta.md",
    # Strategy — exact function prefixes
    "strategy.entry": "reference/functions/strategy.md",
    "strategy.exit": "reference/functions/strategy.md",
    "strategy.close": "reference/functions/strategy.md",
    "strategy.position_size": "reference/functions/strategy.md",
    "strategy.equity": "reference/functions/strategy.md",
    "strategy.risk": "reference/functions/strategy.md",
    # Request — exact function prefixes
    "request.security": "reference/functions/request.md",
    "request.financial": "reference/functions/request.md",
    "request.currency_rate": "reference/functions/request.md",
    # Drawing — exact function prefixes
    "line.new": "reference/functions/drawing.md",
    "box.new": "reference/functions/drawing.md",
    "label.new": "reference/functions/drawing.md",
    "polyline.new": "reference/functions/drawing.md",
    "table.new": "reference/functions/drawing.md",
    # Collections — exact function prefixes
    "array.new": "reference/functions/collections.md",
    "matrix.new": "reference/functions/collections.md",
    "map.new": "reference/functions/collections.md",
    # String functions — exact
    "str.format": "reference/functions/general.md",
    "str.tostring": "reference/functions/general.md",
    # Concepts — unambiguous exact Pine Script terms
    "repainting": "concepts/timeframes.md",
    "lookahead": "concepts/timeframes.md",
    "barstate": "concepts/execution_model.md",
    "varip": "concepts/execution_model.md",
    "calc_on_every_tick": "concepts/execution_model.md",
    "max_bars_back": "concepts/common_errors.md",
    # Visual built-in functions — exact
    "barcolor": "visuals/bar_coloring.md",
    "plotcandle": "visuals/bar_plotting.md",
    "plotshape": "reference/functions/drawing.md",
    "plotchar": "visuals/texts_and_shapes.md",
    "bgcolor": "concepts/colors_and_display.md",
    "linefill": "visuals/fills.md",
    # Migration — exact terms
    "v5 to v6": "reference/migration_v5_to_v6.md",
    "migration": "reference/migration_v5_to_v6.md",
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


@mcp.tool(
    tags={"reference", "discovery"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def list_docs():
    """List all available Pine Script v6 documentation files with descriptions.

    Returns files organised by category with descriptions.
    For small files use get_doc(path). For large files
    (ta.md, strategy.md, collections.md, drawing.md, general.md)
    use list_sections(path) then get_section(path, header).
    """
    with _timed_tool("list_docs"):
        output = ["# Pine Script v6 Documentation", ""]

        categories = {
            "Concepts": [],
            "Reference": [],
            "Functions": [],
            "Visuals": [],
            "Writing Scripts": [],
            "Migration": [],
        }

        for path, desc in DOCS.items():
            if path.startswith("concepts/"):
                categories["Concepts"].append((path, desc))
            elif path.startswith("reference/functions/"):
                categories["Functions"].append((path, desc))
            elif "migration" in path:
                categories["Migration"].append((path, desc))
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


@mcp.tool(
    tags={"reference", "discovery"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def list_sections(path: str):
    """List all section headers in a doc file. Use before get_section() to find the right header.

    Especially useful for large files like ta.md, strategy.md, collections.md, drawing.md, general.md
    which have 50-115 sections each.

    Args:
        path: Documentation file path (e.g., "reference/functions/ta.md")

    Returns top-level section headers (## level) for navigation. Subsections (###) are omitted since get_section(include_children=True) returns them when reading.
    """
    with _timed_tool("list_sections", path=path) as log:
        try:
            full_path = _validate_path(path)
            content = full_path.read_text(encoding="utf-8")
            headers = [line for line in content.splitlines()
                       if line.startswith("#") and not line.startswith("###")]
            log["headers_found"] = len(headers)
            return "\n".join(headers)
        except ValueError as e:
            log["error"] = str(e)
            return f"Error: {e}"


@mcp.tool(
    tags={"reference"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def get_doc(path: str, limit: int = 0, offset: int = 0):
    """Read a specific Pine Script v6 documentation file.

    For large files (ta.md, strategy.md, collections.md, drawing.md,
    general.md) prefer list_sections() + get_section() to avoid
    loading 1000-2800 line files into context.

    Args:
        path: Relative path to the documentation file (e.g., "reference/functions/ta.md")
        limit: Maximum characters to return. Use 30000 for large files to avoid token limits.
        offset: Character offset to start reading from (default: 0)

    Returns the contents with metadata header showing total size and current slice.
    """
    # Enforce safe default for large files before any processing
    if limit == 0 and path in LARGE_DOCS:
        limit = 30000

    with _timed_tool("get_doc", path=path, limit=limit, offset=offset) as log:
        try:
            full_path = _validate_path(path)
            content = full_path.read_text(encoding="utf-8")
            total = len(content)

            if limit > 0:
                if offset >= total:
                    return f"Error: offset {offset} exceeds file size ({total} chars). Use offset < {total}."
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
            log["error"] = str(e)
            return f"Error: {e}"


@mcp.tool(
    tags={"reference"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def get_section(path: str, header: str, include_children: bool = True):
    """Get a specific section from a documentation file by its header.

    Use after list_sections() shows available headers, or after
    resolve_topic() / search_docs() identifies the relevant file.

    Args:
        path: Documentation file path (e.g., "reference/functions/strategy.md")
        header: Header text to find (e.g., "strategy.exit()" or "## strategy.exit()")
        include_children: Include nested subsections under the header (default: True)

    Returns the section content from the header to the next same-level header.
    """
    with _timed_tool("get_section", path=path, header=header) as log:
        try:
            full_path = _validate_path(path)
            content = full_path.read_text(encoding="utf-8")
            section, start_line, end_line = _find_section(content, header, include_children)
            return f"# {path} (lines {start_line}-{end_line})\n\n{section}"
        except ValueError as e:
            log["error"] = str(e)
            return f"Error: {e}"


@mcp.tool(
    tags={"search"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def search_docs(query: str, max_results: int = 10):
    """Grep for an exact string across all Pine Script v6 documentation.

    Use this for specific function names, syntax, or code patterns (e.g., "ta.sma", "strategy.exit").
    For natural language questions, use get_manifest() for routing guidance.

    Args:
        query: Exact string to search for (case-insensitive). Use single terms, not phrases.
        max_results: Maximum number of results to return (default: 10)

    Returns matching lines with file paths and line numbers.
    """
    with _timed_tool("search_docs", query=query, max_results=max_results) as log:
        all_results = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        for rel_path in DOCS.keys():
            full_path = DOCS_ROOT / rel_path
            if not full_path.exists():
                continue
            try:
                lines = full_path.read_text(encoding="utf-8").splitlines()
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        all_results.append({
                            "file": rel_path,
                            "line": i,
                            "content": line.strip()[:200],
                            "is_header": 1 if line.strip().startswith("#") else 0
                        })
            except Exception:
                continue

        all_results.sort(key=lambda r: (-r["is_header"], r["file"], r["line"]))
        results = all_results[:max_results]
        log["results_found"] = len(results)

        if not results:
            return f"No results found for: {query}"

        output = [f"# Search results for: {query}", f"Found {len(results)} matches", ""]
        for r in results:
            output.append(f"**{r['file']}:{r['line']}**")
            output.append(f"  {r['content']}")
            output.append("")
        return "\n".join(output)


@mcp.tool(
    tags={"reference", "discovery"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def get_manifest(ctx: Context):
    """START HERE for natural language Pine Script questions.

    Returns the LLM_MANIFEST.md — a routing guide that maps topics
    to documentation files with tool call sequences for common queries.

    Read this when resolve_topic() returns 0 matches, or when the
    query is a natural language question rather than an exact API term.
    """
    with _timed_tool("get_manifest"):
        manifest_path = DOCS_ROOT / "LLM_MANIFEST.md"
        if not manifest_path.exists():
            return "Error: LLM_MANIFEST.md not found"

        content = manifest_path.read_text(encoding="utf-8")

        if ctx.transport == "streamable-http":
            http_preamble = """## Tool Discovery (claude.ai / HTTP clients)

You are connected via HTTP. Tools are discovered on demand — not all schemas
are injected upfront. Use this pattern:

1. `search_tools(query)` — find tools by name or description
2. `call_tool(name, arguments)` — execute any discovered tool

**Quick reference:**
- `call_tool("resolve_topic", {"query": "ta.rsi"})` — keyword lookup
- `call_tool("get_doc", {"path": "concepts/timeframes.md"})` — read a doc
- `call_tool("lint_script", {"script": "..."})` — already available directly
- `call_tool("search_docs", {"query": "str.format"})` — grep docs

---

"""
            return http_preamble + content

        return content


@mcp.tool(
    tags={"reference", "validation"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def get_functions(namespace: str = ""):
    """Get valid Pine Script v6 functions, optionally filtered by namespace.

    Args:
        namespace: Filter by namespace (e.g., "ta", "strategy", "request").
                   Empty string returns all functions grouped by namespace.

    Returns formatted list of functions. External agents can use this
    to ground their Pine Script generation and avoid hallucinated functions.
    """
    with _timed_tool("get_functions", namespace=namespace or "(all)"):
        if not PINE_V6_FUNCTIONS:
            return (
                "Error: Function data not loaded. "
                "The pine_v6_functions.json file may be missing from the package."
            )
        if not namespace:
            by_ns: dict[str, list[str]] = {}
            for fn in sorted(PINE_V6_FUNCTIONS):
                ns, _, name = fn.rpartition(".")
                by_ns.setdefault(ns, []).append(name)
            lines = [f"{ns}.*: {', '.join(sorted(fns))}" for ns, fns in sorted(by_ns.items())]
            lines.append(f"Top-level: {', '.join(sorted(PINE_V6_TOPLEVEL))}")
            return "\n".join(lines)

        prefix = f"{namespace}."
        matches = sorted(fn for fn in PINE_V6_FUNCTIONS if fn.startswith(prefix))
        if not matches:
            available = ", ".join(sorted(PINE_V6_NAMESPACES))
            return f"No functions found for namespace '{namespace}'. Available namespaces: {available}"
        return f"# {namespace}.* functions ({len(matches)} total)\n\n" + "\n".join(f"- {fn}" for fn in matches)


@mcp.tool(
    tags={"validation"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def validate_function(fn_name: str) -> ValidationResult:
    """Check if a Pine Script v6 function name is valid.

    Args:
        fn_name: Function name to validate (e.g., "ta.sma", "strategy.entry", "plot")

    Returns:
        ValidationResult with valid status, type, and suggestion if invalid.
    """
    with _timed_tool("validate_function", fn_name=fn_name):
        fn_name = fn_name.strip()

        if not fn_name:
            return ValidationResult(valid=False, type=None, function="", suggestion="Provide a function name to validate")
        if fn_name in PINE_V6_FUNCTIONS:
            return ValidationResult(valid=True, type="namespaced", function=fn_name)
        if fn_name in PINE_V6_TOPLEVEL:
            return ValidationResult(valid=True, type="toplevel", function=fn_name)

        if "." in fn_name:
            ns = fn_name.rpartition(".")[0]
            if ns in PINE_V6_NAMESPACES:
                suggestion = f"Not found in {ns}.*. Use get_functions('{ns}') to see all valid {ns}.* functions."
            else:
                available = ", ".join(sorted(PINE_V6_NAMESPACES))
                suggestion = f"Namespace '{ns}' not recognised. Valid namespaces: {available}"
        else:
            suggestion = "Not found. Use get_functions() to see all top-level functions, or get_functions(namespace) for a specific namespace."

        return ValidationResult(valid=False, type=None, function=fn_name, suggestion=suggestion)


@mcp.tool(
    tags={"search"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def resolve_topic(query: str) -> ResolveResult:
    """Fast lookup for exact Pine Script API terms and known concepts.

    Use for exact function names and Pine Script vocabulary
    (e.g., "ta.rsi", "strategy.entry", "repainting", "request.security").

    For natural language questions, use get_manifest() for routing
    guidance, then get_doc() or list_sections() + get_section().

    Args:
        query: Exact Pine Script term or known concept keyword.

    Returns:
        ResolveResult with matched doc paths. If no match, suggestion
        directs to get_manifest() or search_docs().
    """
    with _timed_tool("resolve_topic", query=query) as log:
        query_lower = query.lower()

        path_scores: dict[str, list[str]] = {}
        query_words = set(query_lower.split())

        for keyword, path in TOPIC_MAP.items():
            if " " in keyword:
                matched = keyword in query_lower
            else:
                matched = keyword in query_words
            if matched:
                if path not in path_scores:
                    path_scores[path] = []
                path_scores[path].append(keyword)

        log["matches_found"] = len(path_scores)

        if not path_scores:
            return ResolveResult(
                matches=[],
                query=query,
                suggestion="No keyword match. Use get_manifest() for doc routing guidance, or search_docs(query) for exact terms."
            )

        ranked = sorted(path_scores.items(), key=lambda x: len(x[1]), reverse=True)

        existing_paths = set(path_scores.keys())
        matches = []
        for path, keywords in ranked:
            companions = DOC_COMPANIONS.get(path, [])
            filtered_companions = [c for c in companions if c not in existing_paths]
            matches.append(TopicMatch(
                path=path,
                matched_keywords=keywords,
                score=len(keywords),
                read_with=filtered_companions,
            ))

        top_path = matches[0].path
        if top_path in LARGE_DOCS:
            suggestion = f"Large file — use list_sections('{top_path}') to find headers, then get_section() to read specific sections."
        elif len(matches) > 1:
            paths = [m.path for m in matches[:3]]
            suggestion = f"Read these together: {', '.join(paths)}. Use get_section() for large files."
        else:
            suggestion = f"Use get_doc('{top_path}') to read the top match"

        return ResolveResult(
            matches=matches,
            query=query,
            suggestion=suggestion
        )


# ---------------------------------------------------------------------------
# Lint Rules (subset of research/pipeline/pine_lint.py)
# ---------------------------------------------------------------------------

# Constants that are `const string` but LOOK like enums (LLMs confuse these)
CONST_STRING_NAMESPACES = {
    "adjustment", "alert.freq", "currency", "display", "earnings",
    "extend", "format", "hline.style", "label.style", "line.style",
    "location", "plot.style", "position", "scale", "session", "shape",
    "size", "strategy", "strategy.commission", "strategy.direction",
    "strategy.oca", "text", "xloc", "yloc",
}


def _lint_syntax(code: str) -> list[dict]:
    """
    Parse Pine Script into AST to detect syntax errors.

    Uses pynescript library for real syntax validation.
    Returns empty list if no errors found.
    """
    if not HAS_PYNESCRIPT:
        return []

    try:
        pine_parse(code)
        return []  # No syntax errors
    except PineSyntaxError as e:
        # pynescript SyntaxError stores details in e.details (NamedTuple)
        line = e.details.lineno if hasattr(e, 'details') else 1
        col = e.details.offset if hasattr(e, 'details') else None
        msg = e.message if hasattr(e, 'message') else str(e)
        issue = {
            "line": line,
            "rule": "S001_syntax_error",
            "message": f"Syntax error: {msg}",
            "severity": "error",
        }
        if col is not None:
            issue["column"] = col
        return [issue]
    except Exception as e:
        # Graceful fallback for unexpected parser errors
        return [{
            "line": 1,
            "rule": "S000_parse_failed",
            "message": f"AST parser failed: {str(e)[:100]}",
            "severity": "warning",
        }]


def _lint_pine(code: str) -> list[dict]:
    """
    Lint Pine Script v6 code and return a list of issues.
    Embedded subset of rules from research/pipeline/pine_lint.py.
    """
    issues = []
    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith("//"):
            continue

        # --- Rule E001: input.enum() with const string constants ---
        if re.search(r'input\.enum\s*\(', stripped):
            for ns in CONST_STRING_NAMESPACES:
                if re.search(rf'\b{re.escape(ns)}\.', stripped):
                    issues.append({
                        "line": i,
                        "rule": "E001_input_enum_const_string",
                        "message": f"input.enum() cannot be used with {ns}.* constants (they are const string, not enum). Use input.string() with options=[...] instead.",
                        "severity": "error"
                    })
                    break

        # --- Rule E003: Return type keyword on function declaration ---
        func_decl = re.match(r'^(string|int|float|bool|color|table|line|box|label)\s+(\w+)\s*\(.*\)\s*=>', stripped)
        if func_decl:
            ret_type, func_name = func_decl.group(1), func_decl.group(2)
            issues.append({
                "line": i,
                "rule": "E003_return_type_keyword",
                "message": f"Cannot use '{ret_type}' as return type on function '{func_name}()'. Remove the type keyword — Pine v6 infers return types.",
                "severity": "error"
            })

        # --- Rule E005: study() instead of indicator() ---
        if re.search(r'\bstudy\s*\(', stripped):
            issues.append({
                "line": i,
                "rule": "E005_study_removed",
                "message": "study() does not exist in Pine v6. Use indicator() instead.",
                "severity": "error"
            })

        # --- Rule E006: security() instead of request.security() ---
        if re.search(r'(?<!request\.)\bsecurity\s*\(', stripped):
            issues.append({
                "line": i,
                "rule": "E006_security_removed",
                "message": "security() does not exist in v6. Use request.security() instead.",
                "severity": "error"
            })

        # --- Rule E007: alertcondition() in strategy ---
        if re.search(r'\balertcondition\s*\(', stripped):
            for prev_line in lines[:i]:
                # Skip comment lines when checking for strategy declaration
                prev_stripped = prev_line.strip()
                if prev_stripped.startswith("//"):
                    continue
                if re.search(r'\bstrategy\s*\(', prev_stripped):
                    issues.append({
                        "line": i,
                        "rule": "E007_alertcondition_in_strategy",
                        "message": "alertcondition() only works in indicator() scripts. Strategies must use alert() with alert.freq_once_per_bar_close.",
                        "severity": "error"
                    })
                    break

        # --- Rule E009: format.currency (doesn't exist) ---
        if re.search(r'\bformat\.currency\b', stripped):
            issues.append({
                "line": i,
                "rule": "E009_format_currency",
                "message": "format.currency does not exist in Pine v6. Use format.mintick or manual string formatting.",
                "severity": "error"
            })

        # --- Rule E010: Direct comparison to na (must use na() function) ---
        if re.search(r'[!=]=\s*\bna\s*($|[^a-zA-Z0-9_(])', stripped) or re.search(r'(?<![a-zA-Z0-9_])\bna\s*[!=]=', stripped):
            issues.append({
                "line": i,
                "rule": "E010_direct_na_comparison",
                "message": "Cannot compare a value to 'na' directly. Use the na() function instead. E.g. `na(x)` not `x == na`.",
                "severity": "error"
            })

        # --- Rule E012: Hallucinated function — not in Pine v6 allowlist ---
        for fn_match in re.finditer(r'\b([a-z][a-z0-9]*(?:\.[a-z_][a-z0-9_]*)+)\s*\(', stripped):
            fn_name = fn_match.group(1)
            parts = fn_name.split(".")
            ns = None
            for depth in range(len(parts) - 1, 0, -1):
                candidate = ".".join(parts[:depth])
                if candidate in PINE_V6_NAMESPACES:
                    ns = candidate
                    break
            if ns and fn_name not in PINE_V6_FUNCTIONS:
                issues.append({
                    "line": i,
                    "rule": "E012_unknown_function",
                    "message": f"'{fn_name}()' does not exist in Pine Script v6.",
                    "severity": "error"
                })

        # --- Rule W003: lookahead_on without comment/justification ---
        if re.search(r'lookahead\s*=\s*barmerge\.lookahead_on', stripped):
            issues.append({
                "line": i,
                "rule": "W003_lookahead_on",
                "message": "barmerge.lookahead_on can cause future data leak. Use barmerge.lookahead_off unless you explicitly need historical HTF values with [1] offset.",
                "severity": "warning"
            })

        # --- Rule E013: input.enum() with options array (v6 requires enum type) ---
        if re.search(r'input\.enum\s*\([^)]*options\s*=\s*\[', stripped):
            issues.append({
                "line": i,
                "rule": "E013_input_enum_options_array",
                "message": "input.enum() does not use options=[...] array. Pass enum values directly as defval. For string options, use input.string(options=[...]) instead.",
                "severity": "error"
            })

        # --- Rule E014: strategy() without title parameter ---
        if re.search(r'\bstrategy\s*\(', stripped):
            # Check if title= or first positional arg (string) is present
            if not re.search(r'strategy\s*\(\s*["\']', stripped) and not re.search(r'strategy\s*\([^)]*title\s*=', stripped):
                issues.append({
                    "line": i,
                    "rule": "E014_strategy_missing_title",
                    "message": "strategy() requires a title parameter. Add title=\"Strategy Name\" or pass it as the first argument.",
                    "severity": "error"
                })

        # --- Rule E015: Mismatched string quotes ---
        # Check for strings that start with one quote type but don't close properly
        single_quotes = stripped.count("'") - stripped.count("\\'")
        double_quotes = stripped.count('"') - stripped.count('\\"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            # Skip if it's a comment line or inside a multi-line string context
            if not stripped.startswith("//"):
                issues.append({
                    "line": i,
                    "rule": "E015_mismatched_quotes",
                    "message": "Possible mismatched string quotes. Ensure all strings are properly closed.",
                    "severity": "error"
                })

        # --- Rule W004: max_bars_back set very high ---
        max_bars_match = re.search(r'max_bars_back\s*[=:]\s*(\d+)', stripped)
        if max_bars_match:
            value = int(max_bars_match.group(1))
            if value >= 5000:
                issues.append({
                    "line": i,
                    "rule": "W004_high_max_bars_back",
                    "message": f"max_bars_back={value} is very high and may impact performance. Consider if you really need this many historical bars.",
                    "severity": "warning"
                })

        # --- Rule W005: Variable declared with var but potentially unused ---
        # Simple heuristic: var declaration at start of line with common unused patterns
        var_match = re.match(r'^var\s+(?:int|float|bool|string|color|line|box|label|table)?\s*(\w+)\s*=', stripped)
        if var_match:
            var_name = var_match.group(1)
            # Check if variable appears elsewhere in code (simple check)
            var_usage_count = code.count(var_name)
            if var_usage_count == 1:  # Only the declaration
                issues.append({
                    "line": i,
                    "rule": "W005_potentially_unused_var",
                    "message": f"Variable '{var_name}' is declared but may be unused. Verify it's referenced elsewhere.",
                    "severity": "warning"
                })

    # --- Rule W001: Missing //@version=6 (check first non-comment line) ---
    version_found = False
    for line in lines:
        stripped_line = line.strip()
        # Skip empty lines and regular comments (but not annotations like //@)
        if not stripped_line or (stripped_line.startswith("//") and not stripped_line.startswith("//@")):
            continue
        # Check if this first significant line is a version declaration
        if stripped_line.startswith("//@version="):
            version_found = True
        break  # Only check the first significant line

    if not version_found:
        issues.insert(0, {
            "line": 1,
            "rule": "W001_missing_version",
            "message": "Missing //@version=6 declaration. Add it as the first non-comment line.",
            "severity": "warning"
        })

    return issues


@mcp.tool(
    tags={"validation"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    timeout=30,
)
async def lint_script(script: str) -> LintResult:
    """Lint Pine Script for syntax and style issues (free, no API cost).

    Fast static analysis that checks for common issues without using AI.

    Args:
        script: The Pine Script code to lint.

    Returns:
        LintResult with status, count, and list of issues found.
    """
    MAX_SCRIPT_SIZE = 50_000  # 50KB — no real Pine Script is larger
    if len(script) > MAX_SCRIPT_SIZE:
        return LintResult(
            status="issues_found",
            count=1,
            issues=[LintIssue(
                line=1,
                rule="E000_script_too_large",
                message=f"Script exceeds {MAX_SCRIPT_SIZE} chars. Truncate to lint.",
                severity="error",
            )]
        )

    with _timed_tool("lint_script", script_length=len(script)) as log:
        syntax_issues = _lint_syntax(script)
        pattern_issues = _lint_pine(script)
        raw_issues = syntax_issues + pattern_issues
        issues = [LintIssue(**issue) for issue in raw_issues]
        log["issues_found"] = len(issues)

        return LintResult(
            status="ok" if not issues else "issues_found",
            count=len(issues),
            issues=issues
        )


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

@mcp.prompt
def debug_error(error_message: str, code: str) -> str:
    """Debug a Pine Script compilation error.

    Args:
        error_message: The error message from TradingView compiler
        code: The Pine Script code that produced the error
    """
    return f"""Analyze this Pine Script v6 compilation error and suggest a fix.

**Error:**
{error_message}

**Code:**
```pine
{code}
```

**Analysis steps:**
1. Identify the root cause of the error
2. Check for Pine Script v6 syntax issues (study→indicator, security→request.security)
3. Verify all function names are valid v6 functions
4. Check for type mismatches or missing parameters
5. Provide a corrected code snippet"""


@mcp.prompt
def convert_v5_to_v6(code: str) -> str:
    """Convert Pine Script v5 code to v6.

    Args:
        code: Pine Script v5 code to convert
    """
    return f"""Convert this Pine Script v5 code to v6 syntax.

**v5 Code:**
```pine
{code}
```

**Key v5 → v6 changes to apply:**
- `study()` → `indicator()`
- `security()` → `request.security()`
- `color.new()` parameter order may differ
- Check for deprecated functions
- Add `//@version=6` header

Provide the converted v6 code with explanations for each change made."""


@mcp.prompt
def explain_function(function_name: str) -> str:
    """Explain a Pine Script function in detail.

    Args:
        function_name: The function to explain (e.g., "ta.rsi", "strategy.entry")
    """
    return f"""Explain the Pine Script v6 function: `{function_name}`

Please provide:
1. **Purpose**: What does this function do?
2. **Syntax**: Full function signature with all parameters
3. **Parameters**: Explain each parameter and its valid values
4. **Return type**: What does the function return?
5. **Example**: A practical usage example
6. **Common pitfalls**: Any gotchas or common mistakes to avoid

Use the Pine Script v6 documentation to ensure accuracy."""


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for container orchestration."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "server": "pinescript-docs", "version": __version__})


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics(request):
    """Prometheus metrics endpoint for Fly.io scraping."""
    from starlette.responses import Response
    return Response(generate_latest(METRICS_REGISTRY), media_type=CONTENT_TYPE_LATEST)


def main():
    """Entry point for the CLI."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Pine Script v6 MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8080)),
                        help="HTTP port (default: 8080 or $PORT)")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host (default: 0.0.0.0)")
    args = parser.parse_args()

    if args.http:
        from fastmcp.server.transforms.search import BM25SearchTransform
        mcp.add_transform(BM25SearchTransform(
            max_results=10,
            always_visible=["get_manifest", "lint_script"],
        ))
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
