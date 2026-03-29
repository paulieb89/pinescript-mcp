#!/usr/bin/env python3
"""
Pine Script v6 Documentation MCP Server

Provides tools to list, search, and read Pine Script v6 documentation.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP, Context
from fastmcp.server.context import _current_transport
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware
from fastmcp.server.transforms import ResourcesAsTools, PromptsAsTools
from fastmcp.utilities.logging import get_logger
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
    ["tool", "transport", "region"],
    registry=METRICS_REGISTRY,
)
tool_errors_total = Counter(
    "pinescript_tool_errors_total",
    "Tool calls that raised exceptions",
    ["tool", "transport", "region"],
    registry=METRICS_REGISTRY,
)
tool_duration_seconds = Histogram(
    "pinescript_tool_duration_seconds",
    "Tool call duration in seconds",
    ["tool", "transport", "region"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0],
    registry=METRICS_REGISTRY,
)

# Optional: pynescript for AST-based syntax and semantic validation
try:
    from pynescript.ast import parse as pine_parse
    from pynescript.ast.error import SyntaxError as PineSyntaxError
    from pynescript.ast import (
        walk as pine_walk,
        Name, Assign, FunctionDef, TypeDef, EnumDef,
        ForTo, ForIn, Param, Attribute, Load,
    )
    from pynescript.ast import Import as PineImport
    from pynescript.ast import Tuple as PineTuple
    from pynescript.ast.grammar.antlr4.generated.PinescriptParser import PinescriptParser as _PineParser
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
    script_id: str | None = None  # content hash for edit_and_lint


class ScriptEdit(BaseModel):
    """A single line edit to apply to a cached script."""
    line: int   # 1-based line number
    old: str    # text to find on that line (for validation)
    new: str    # replacement text


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

# Transport + region — inferred from environment, used by _timed_tool for metrics labels
# Fly.io sets FLY_REGION automatically; "streamable-http" matches ctx.transport literal
_FLY_REGION = os.getenv("FLY_REGION", "local")
_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http" if os.getenv("FLY_REGION") else "stdio")

# Initialize MCP server
mcp = FastMCP(
    "pinescript-docs",
    instructions=(
        "For skills that work with these tools see https://bouch.dev/products/pine-strategy-builder "
    ),
)

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

# ---------------------------------------------------------------------------
# Transforms — expose resources and prompts as tools for clients that
# don't natively support MCP resources/prompts (most current LLM clients)
# ---------------------------------------------------------------------------
mcp.add_transform(ResourcesAsTools(mcp))
mcp.add_transform(PromptsAsTools(mcp))

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
        transport = _current_transport.get() or _TRANSPORT
        tool_calls_total.labels(tool=self._tool_name, transport=transport, region=_FLY_REGION).inc()
        tool_duration_seconds.labels(tool=self._tool_name, transport=transport, region=_FLY_REGION).observe(duration)
        if exc_type is not None:
            tool_errors_total.labels(tool=self._tool_name, transport=transport, region=_FLY_REGION).inc()
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

# ---------------------------------------------------------------------------
# Built-in identifiers for undeclared-identifier detection (E016)
# ---------------------------------------------------------------------------

# Bare variables that are built-in (many overlap with TOPLEVEL, that's fine)
_BUILTIN_VARIABLES = {
    "open", "high", "low", "close", "volume",
    "hl2", "hlc3", "hlcc4", "ohlc4",
    "bar_index", "last_bar_index", "last_bar_time",
    "time", "time_close", "time_tradingday", "timenow",
    "na", "true", "false",
    "ask", "bid",
    "dayofmonth", "dayofweek", "hour", "minute", "month",
    "second", "weekofyear", "year",
}

# Namespace roots — appear as Name nodes in Attribute access (ta.sma, barstate.isrealtime)
_BUILTIN_NS_ROOTS = (
    {ns.split(".")[0] for ns in PINE_V6_NAMESPACES}
    | {
        "adjustment", "alert", "backadjustment", "barmerge", "barstate",
        "chart", "currency", "dayofweek", "display", "dividends", "earnings",
        "extend", "font", "format", "hline", "location", "order", "plot",
        "position", "scale", "session", "settlement_as_close", "shape",
        "size", "splits", "text", "xloc", "yloc",
    }
)

# Type keywords — appear as Name(ctx=Load) in type annotations and declarations
_PINE_TYPE_KEYWORDS = {
    "float", "int", "bool", "string", "color",
    "line", "label", "box", "table", "array", "matrix", "map",
}

PINE_V6_BUILTIN_IDENTIFIERS = (
    PINE_V6_TOPLEVEL | _BUILTIN_VARIABLES | _BUILTIN_NS_ROOTS | _PINE_TYPE_KEYWORDS
)

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

# ---------------------------------------------------------------------------
# Doc Content Cache — lazy-loaded, in-memory, bounded (~1.3 MB for 36 files)
# Invalidated only by deploy (new process). Static content, no stale risk.
# ---------------------------------------------------------------------------
_DOC_LINES_CACHE: dict[str, list[str]] = {}


def _get_doc_lines(rel_path: str) -> list[str]:
    """Return doc file as list of lines, cached after first read."""
    if rel_path not in _DOC_LINES_CACHE:
        full_path = DOCS_ROOT / rel_path
        _DOC_LINES_CACHE[rel_path] = full_path.read_text(encoding="utf-8").splitlines() if full_path.exists() else []
    return _DOC_LINES_CACHE[rel_path]


def _get_doc_content(rel_path: str) -> str:
    """Return doc file as a single string, cached after first read."""
    return "\n".join(_get_doc_lines(rel_path))


# ---------------------------------------------------------------------------
# Script Cache — content-addressed, TTL-evicted, per-instance
# Enables edit_and_lint() to apply line edits without re-sending full script.
# Cache key is sha256(script)[:12] so same content = same ID on any instance.
# ---------------------------------------------------------------------------
_SCRIPT_CACHE_MAX = 100
_SCRIPT_CACHE_TTL = 1800  # 30 minutes
_SCRIPT_CACHE: dict[str, tuple[str, float]] = {}  # id → (script_text, timestamp)


def _cache_script(script: str) -> str:
    """Cache script text, return content-addressed ID."""
    script_id = hashlib.sha256(script.encode()).hexdigest()[:12]
    _SCRIPT_CACHE[script_id] = (script, time.time())
    # Evict expired + overflow
    if len(_SCRIPT_CACHE) > _SCRIPT_CACHE_MAX:
        cutoff = time.time() - _SCRIPT_CACHE_TTL
        expired = [k for k, (_, ts) in _SCRIPT_CACHE.items() if ts < cutoff]
        for k in expired:
            del _SCRIPT_CACHE[k]
        # If still over limit, evict oldest
        if len(_SCRIPT_CACHE) > _SCRIPT_CACHE_MAX:
            oldest = min(_SCRIPT_CACHE, key=lambda k: _SCRIPT_CACHE[k][1])
            del _SCRIPT_CACHE[oldest]
    return script_id


def _get_cached_script(script_id: str) -> str | None:
    """Retrieve cached script if exists and not expired."""
    entry = _SCRIPT_CACHE.get(script_id)
    if entry is None:
        return None
    text, ts = entry
    if time.time() - ts > _SCRIPT_CACHE_TTL:
        del _SCRIPT_CACHE[script_id]
        return None
    return text


# Topic mapping for resolve_topic() — exact Pine Script API terms only.
# Natural language routing is handled by the LLM reading the docs://manifest resource.
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

    # Normalize header query (strip leading #'s if present, collapse whitespace)
    header_text = re.sub(r'\s+', ' ', re.sub(r'^#+\s*', '', header).strip().lower())

    start_idx = None
    start_level = None

    for i, line in enumerate(lines):
        if line.startswith('#'):
            # Parse header level and text
            match = re.match(r'^(#+)\s*(.+)', line)
            if match:
                level = len(match.group(1))
                text = re.sub(r'\s+', ' ', match.group(2).strip().lower())

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
            _validate_path(path)  # check path is allowed
            content = _get_doc_content(path)
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
            _validate_path(path)  # check path is allowed
            content = _get_doc_content(path)
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
            _validate_path(path)  # check path is allowed
            content = _get_doc_content(path)
            section, start_line, end_line = _find_section(content, header, include_children)
            return f"# {path} (lines {start_line}-{end_line})\n\n{section}"
        except ValueError as e:
            log["error"] = str(e)
            return f"Error: {e}"


@mcp.tool(
    tags={"search"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def search_docs(query: str, max_results: int = 5):
    """Search Pine Script v6 documentation and return matching sections.

    Finds sections containing the query and returns previews with
    get_section() call hints so you can read the full content.

    Args:
        query: Exact string to search for (case-insensitive).
        max_results: Maximum sections to return (default: 5)

    Returns matching sections ranked by relevance with get_section() hints.
    """
    with _timed_tool("search_docs", query=query, max_results=max_results) as log:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        section_hits = []

        for rel_path in DOCS.keys():
            lines = _get_doc_lines(rel_path)
            if not lines:
                continue

            current_start = 0
            current_header = "(preamble)"
            current_level = 0

            for i, line in enumerate(lines):
                header_match = re.match(r'^(#+)\s*(.+)', line)
                if header_match:
                    # Close previous section — check for hits
                    section_lines = lines[current_start:i]
                    match_count = sum(1 for l in section_lines if pattern.search(l))
                    if match_count and current_header != "(preamble)":
                        section_hits.append({
                            "file": rel_path,
                            "header": current_header,
                            "level": current_level,
                            "matches": match_count,
                            "preview": "\n".join(section_lines[:30]),
                        })
                    # Open new section
                    current_header = header_match.group(2).strip()
                    current_level = len(header_match.group(1))
                    current_start = i

            # Final section
            section_lines = lines[current_start:]
            match_count = sum(1 for l in section_lines if pattern.search(l))
            if match_count and current_header != "(preamble)":
                section_hits.append({
                    "file": rel_path,
                    "header": current_header,
                    "level": current_level,
                    "matches": match_count,
                    "preview": "\n".join(section_lines[:30]),
                })

        # Sort: more matches first, then prefer ## over ###
        section_hits.sort(key=lambda x: (-x["matches"], x["level"]))
        results = section_hits[:max_results]
        log["results_found"] = len(results)

        if not results:
            return f"No results found for: {query}"

        output = [f"# Search results for: {query}", f"Found {len(results)} matching sections", ""]
        for r in results:
            output.append(f"## {r['file']} → {r['header']}")
            output.append(f"Use: get_section(\"{r['file']}\", \"{r['header']}\")")
            output.append(f"({r['matches']} matches)")
            output.append("")
            output.append(r["preview"])
            output.append("")
        return "\n".join(output)


@mcp.tool(
    tags={"reference", "validation"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def get_functions(namespace: str = ""):
    """Get valid Pine Script v6 functions, optionally filtered by namespace.

    Use before writing Pine Script to see which functions exist.
    For checking a single function name, use validate_function() instead.

    Args:
        namespace: Filter by namespace (e.g., "ta", "strategy", "request").
                   Empty string returns all functions grouped by namespace.

    Returns a formatted text list of function names.
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

    For natural language questions, read the docs://manifest resource
    for routing guidance, then use get_doc() or list_sections() + get_section().

    Args:
        query: Exact Pine Script term or known concept keyword.

    Returns:
        ResolveResult with matched doc paths. If no match, suggestion
        directs to search_docs().
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
                suggestion="No keyword match. Read the docs://manifest resource for routing guidance, or use search_docs(query) for exact terms."
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
    _in_strategy = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith("//"):
            continue

        # Track strategy declaration for E007 (O(1) instead of scanning backwards)
        if not _in_strategy and re.search(r'\bstrategy\s*\(', stripped):
            _in_strategy = True

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
        if _in_strategy and re.search(r'\balertcondition\s*\(', stripped):
            issues.append({
                "line": i,
                "rule": "E007_alertcondition_in_strategy",
                "message": "alertcondition() only works in indicator() scripts. Strategies must use alert() with alert.freq_once_per_bar_close.",
                "severity": "error"
            })

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
        # Walk the line tracking string state to detect truly unclosed strings.
        # Pine Script supports both single and double quoted strings.
        if not stripped.startswith("//"):
            in_string = False
            string_char = None
            j = 0
            while j < len(stripped):
                ch = stripped[j]
                if in_string:
                    if ch == '\\' and j + 1 < len(stripped):
                        j += 2  # skip escaped character
                        continue
                    if ch == string_char:
                        in_string = False
                else:
                    if ch == '/' and j + 1 < len(stripped) and stripped[j + 1] == '/':
                        break  # rest of line is a comment
                    if ch in ('"', "'"):
                        in_string = True
                        string_char = ch
                j += 1
            if in_string:
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
            # Check if variable appears elsewhere in code (word-boundary match)
            var_usage_count = len(re.findall(rf'\b{re.escape(var_name)}\b', code))
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
        # Check if this line is a version declaration
        if stripped_line.startswith("//@version="):
            version_found = True
            break
        # Skip other //@annotations (e.g., //@description, //@function, //@param)
        if stripped_line.startswith("//@"):
            continue
        break  # First real code line — version should have appeared by now

    if not version_found:
        issues.insert(0, {
            "line": 1,
            "rule": "W001_missing_version",
            "message": "Missing //@version=6 declaration. Add it as the first non-comment line.",
            "severity": "warning"
        })

    return issues


def _lint_undeclared(code: str, pattern_issues: list[dict] | None = None) -> list[dict]:
    """Walk the pynescript AST to find identifiers used but never declared.

    Uses flat scope (no nesting analysis) — all declarations are visible
    everywhere. This is conservative: may miss some true errors in nested
    scopes but avoids false positives.

    Suppresses identifiers already flagged by pattern rules (e.g. E005/E006
    catch study()/security() with better messages — E016 shouldn't duplicate).
    """
    # Build set of identifiers already covered by pattern rules
    _already_flagged: set[str] = set()
    for issue in pattern_issues or []:
        msg = issue.get("message", "")
        # Extract function name from messages like "study() does not exist..."
        if "() " in msg:
            _already_flagged.add(msg.split("(")[0].strip())
    if not HAS_PYNESCRIPT:
        return []

    try:
        tree = pine_parse(code)
    except Exception:
        return []  # parse errors handled by _lint_syntax

    all_nodes = list(pine_walk(tree))
    declared = set()
    suppress_ids = set()
    issues = []
    seen = set()  # (name, line) dedup

    try:
        # --- Pass 1: collect declared identifiers ---
        for node in all_nodes:
            if isinstance(node, Assign):
                if isinstance(node.target, Name):
                    declared.add(node.target.id)
                elif isinstance(node.target, PineTuple):
                    for elt in getattr(node.target, "elts", []):
                        if isinstance(elt, Name):
                            declared.add(elt.id)

            elif isinstance(node, FunctionDef):
                declared.add(node.name)
                for p in (node.args or []):
                    if isinstance(p, Param) and getattr(p, "name", None):
                        declared.add(p.name)

            elif isinstance(node, TypeDef):
                declared.add(node.name)

            elif isinstance(node, EnumDef):
                declared.add(node.name)

            elif isinstance(node, PineImport):
                declared.add(node.alias or node.name)

            elif isinstance(node, ForTo):
                if isinstance(node.target, Name):
                    declared.add(node.target.id)

            elif isinstance(node, ForIn):
                if isinstance(node.target, Name):
                    declared.add(node.target.id)
                elif isinstance(node.target, PineTuple):
                    for elt in getattr(node.target, "elts", []):
                        if isinstance(elt, Name):
                            declared.add(elt.id)

        # --- Build suppression set: Name nodes used as BUILTIN Attribute prefixes ---
        # e.g., `ta` in `ta.sma(...)` — suppress that specific Name instance
        # User objects like `g_levels.high` should NOT be suppressed
        for node in all_nodes:
            if isinstance(node, Attribute) and isinstance(node.value, Name):
                if node.value.id in _BUILTIN_NS_ROOTS:
                    suppress_ids.add(id(node.value))

        # --- Pass 2: check Load-context Name nodes ---
        for node in all_nodes:
            if not isinstance(node, Name):
                continue
            if not isinstance(node.ctx, Load):
                continue

            name = node.id
            line = getattr(node, "lineno", None) or 0

            if id(node) in suppress_ids:
                continue
            if name in declared:
                continue
            if name in PINE_V6_BUILTIN_IDENTIFIERS:
                continue
            if name in _already_flagged:
                continue

            key = (name, line)
            if key in seen:
                continue
            seen.add(key)

            issues.append({
                "line": line,
                "rule": "E016_undeclared_identifier",
                "message": f"'{name}' is used but never declared. Check spelling or add a declaration.",
                "severity": "warning",
            })

        return issues
    finally:
        del tree, all_nodes, suppress_ids
        # ANTLR4 PredictionContextCache grows unboundedly (~1k entries/parse).
        # No LLM accesses this; cold-parse penalty is only 0.5ms.
        if HAS_PYNESCRIPT:
            _PineParser.sharedContextCache.cache.clear()


@mcp.tool(
    tags={"validation"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    timeout=30,
)
async def lint_script(script: str) -> LintResult:
    """Lint Pine Script for syntax and style issues.

    Static analysis checking syntax (ANTLR4), style patterns, and undeclared
    identifiers. Requires authorization on HTTP (free for local STDIO clients).

    Args:
        script: The Pine Script code to lint.

    Returns:
        LintResult with status, count, script_id (for edit_and_lint), and list of issues found.
    """
    auth_error = _check_premium_auth()
    if auth_error is not None:
        return auth_error

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
        undeclared_issues = _lint_undeclared(script, pattern_issues) if not syntax_issues else []
        raw_issues = syntax_issues + pattern_issues + undeclared_issues
        issues = [LintIssue(**issue) for issue in raw_issues]
        script_id = _cache_script(script)
        log["issues_found"] = len(issues)
        log["script_id"] = script_id

        return LintResult(
            status="ok" if not issues else "issues_found",
            count=len(issues),
            issues=issues,
            script_id=script_id,
        )


def _check_premium_auth() -> LintResult | None:
    """Check auth for premium tools. Returns error LintResult if blocked, None if OK.

    - STDIO (local): always allowed (no headers to check)
    - HTTP without MCP_API_KEY configured: blocked (operator must configure)
    - HTTP with valid Bearer token: allowed
    """
    from fastmcp.server.dependencies import get_http_headers

    headers = get_http_headers(include=["authorization"])
    if not headers:
        return None  # STDIO transport — local use, always allowed

    # HTTP transport — require auth
    api_key = os.getenv("MCP_API_KEY", "")
    if not api_key:
        return LintResult(
            status="issues_found", count=1, script_id=None,
            issues=[LintIssue(line=0, rule="AUTH", message="Premium tool not configured on this server", severity="error")]
        )
    auth = headers.get("authorization", "")
    if auth == f"Bearer {api_key}":
        return None  # Valid key
    return LintResult(
        status="issues_found", count=1, script_id=None,
        issues=[LintIssue(line=0, rule="AUTH", message="edit_and_lint requires valid Authorization header", severity="error")]
    )


@mcp.tool(
    tags={"validation"},
    annotations={"readOnlyHint": False, "idempotentHint": False, "openWorldHint": False},
    timeout=30,
)
async def edit_and_lint(script_id: str, edits: list[ScriptEdit]) -> LintResult:
    """Apply line edits to a previously linted script and re-lint.

    Use after lint_script() returns issues. Send only the changed lines
    instead of the full script — saves tokens on fix-and-re-lint cycles.

    Args:
        script_id: The script_id returned by a previous lint_script() call.
        edits: List of line edits. Each specifies a 1-based line number,
               the old text expected on that line, and the new replacement text.

    Returns:
        LintResult with new script_id and fresh lint issues.
        If script_id not found (expired or different server instance),
        re-send the full script via lint_script() instead.
    """
    # Per-tool auth — only this tool is gated
    auth_err = _check_premium_auth()
    if auth_err is not None:
        return auth_err

    with _timed_tool("edit_and_lint", script_id=script_id, edit_count=len(edits)) as log:
        # Retrieve cached script
        script = _get_cached_script(script_id)
        if script is None:
            log["cache_hit"] = False
            return LintResult(
                status="issues_found", count=1, script_id=None,
                issues=[LintIssue(
                    line=0, rule="CACHE_MISS",
                    message=f"Script '{script_id}' not found (expired or different server instance). Re-send full script via lint_script().",
                    severity="error",
                )]
            )
        log["cache_hit"] = True

        # Apply edits
        lines = script.split("\n")
        for edit in edits:
            idx = edit.line - 1  # 0-based
            if idx < 0 or idx >= len(lines):
                return LintResult(
                    status="issues_found", count=1, script_id=script_id,
                    issues=[LintIssue(
                        line=edit.line, rule="EDIT_ERROR",
                        message=f"Line {edit.line} out of range (script has {len(lines)} lines).",
                        severity="error",
                    )]
                )
            if edit.old and edit.old not in lines[idx]:
                return LintResult(
                    status="issues_found", count=1, script_id=script_id,
                    issues=[LintIssue(
                        line=edit.line, rule="EDIT_MISMATCH",
                        message=f"Expected '{edit.old}' on line {edit.line}, found '{lines[idx].strip()}'. Script may have changed.",
                        severity="error",
                    )]
                )
            if edit.old:
                lines[idx] = lines[idx].replace(edit.old, edit.new, 1)
            else:
                lines[idx] = edit.new

        # Re-lint the modified script
        modified = "\n".join(lines)
        syntax_issues = _lint_syntax(modified)
        pattern_issues = _lint_pine(modified)
        undeclared_issues = _lint_undeclared(modified, pattern_issues) if not syntax_issues else []
        raw_issues = syntax_issues + pattern_issues + undeclared_issues
        issues = [LintIssue(**issue) for issue in raw_issues]
        new_script_id = _cache_script(modified)
        log["issues_found"] = len(issues)
        log["new_script_id"] = new_script_id

        return LintResult(
            status="ok" if not issues else "issues_found",
            count=len(issues),
            issues=issues,
            script_id=new_script_id,
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


# ---------------------------------------------------------------------------
# MCP Resources — docs corpus accessible to resource-capable clients
# ---------------------------------------------------------------------------

@mcp.resource(
    "docs://manifest",
    name="LLM Manifest",
    description="START HERE — routing guide that maps Pine Script questions to documentation files and tool call sequences",
    mime_type="text/markdown",
    tags={"discovery"},
    annotations={"readOnlyHint": True},
)
def manifest_resource() -> str:
    """Returns LLM_MANIFEST.md — the routing guide for Pine Script questions.

    Read this first when handling natural language questions, or when
    resolve_topic() returns 0 matches.
    """
    return _get_doc_content("LLM_MANIFEST.md")


@mcp.resource(
    "docs://functions",
    name="Pine Script v6 Functions",
    description="Complete list of valid Pine Script v6 functions as JSON",
    mime_type="application/json",
    tags={"reference", "validation"},
    annotations={"readOnlyHint": True},
)
def functions_resource() -> str:
    """Returns pine_v6_functions.json content."""
    return FUNCTIONS_JSON.read_text(encoding="utf-8") if FUNCTIONS_JSON.exists() else "{}"


@mcp.resource(
    "docs://{path*}",
    name="Pine Script Documentation",
    description="Read any Pine Script v6 doc by path (e.g. 'concepts/timeframes.md', 'reference/functions/ta.md')",
    mime_type="text/markdown",
    tags={"reference"},
    annotations={"readOnlyHint": True},
)
def doc_resource(path: str) -> str:
    """Returns documentation file content by path.

    Uses _validate_path() to ensure path is within allowed directories.
    """
    _validate_path(path)
    return _get_doc_content(path)


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
        import asyncio
        import uvicorn

        # Serve both transports on the same port:
        #   streamable-http at /mcp  (Claude.ai, modern clients)
        #   SSE at /sse + /messages/ (Cursor, Cline, Windsurf, ChatGPT)
        # stateless_http=True: no per-session state — safe for Fly.io multi-instance routing
        streamable_app = mcp.http_app(transport="http", stateless_http=True)
        sse_app = mcp.http_app(transport="sse", stateless_http=True)

        async def app(scope, receive, send):
            """ASGI dispatcher: route SSE paths to sse_app, everything else to streamable_app."""
            if scope["type"] == "lifespan":
                # Both apps share the same FastMCP instance; one lifespan suffices
                await streamable_app(scope, receive, send)
                return
            path = scope.get("path", "")
            if path.startswith("/sse") or path.startswith("/messages"):
                await sse_app(scope, receive, send)
            else:
                await streamable_app(scope, receive, send)

        config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
        server = uvicorn.Server(config)
        asyncio.run(server.serve())
    else:
        mcp.run()


if __name__ == "__main__":
    main()
