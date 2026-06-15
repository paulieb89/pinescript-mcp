#!/usr/bin/env python3
"""
Pine Script v6 Documentation MCP Server

Provides tools to list, search, and read Pine Script v6 documentation.
"""

import json
import re
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.server.context import _current_transport
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.transforms import PromptsAsTools
from fastmcp.utilities.logging import get_logger
from pydantic import Field
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

# ---------------------------------------------------------------------------
# Pydantic Models for Structured Output
# ---------------------------------------------------------------------------


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

# Response limiting removed — Lesson 33: server-side truncation drops
# structured_content on oversized responses. Per-tool limit/offset in
# get_doc / get_section / search_docs already handles large payloads.

# ---------------------------------------------------------------------------
# Transforms — expose resources and prompts as tools for clients that
# don't natively support MCP resources/prompts (most current LLM clients)
# ---------------------------------------------------------------------------
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

# Known invalid/renamed functions → specific replacement hints for validate_function()
KNOWN_REPLACEMENTS: dict[str, str] = {
    "ta.adx": "ta.adx() does NOT exist. Use ta.dmi(diLen, adxSmoothing) → returns [diPlus, diMinus, adx] as a tuple.",
    "ta.sum": "ta.sum() does NOT exist. Use math.sum(source, length) instead.",
    "security": "security() was renamed in v5. Use request.security() instead.",
    "study": "study() was renamed in v5. Use indicator() instead.",
    "input": "input() works but prefer typed variants: input.int(), input.float(), input.string(), input.bool(), etc.",
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
    """USE WHEN discovering what Pine Script v6 documentation is available.
    Returns a categorised list of doc file paths with one-line descriptions.
    AFTER calling this tool, call get_doc(path) for small files or list_sections(path) then get_section(path, header) for large files (ta.md, strategy.md, collections.md, drawing.md, general.md).
    Data sourced from bundled Pine Script v6 documentation.
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
async def list_sections(
    path: Annotated[str, Field(description="Documentation file path (e.g., 'reference/functions/ta.md').")],
):
    """USE WHEN navigating a large documentation file before reading a specific section.
    Returns a newline-separated list of # and ## headers (### excluded) in the file.
    AFTER calling this tool, call get_section(path, header) with a header from this list.
    Data sourced from bundled Pine Script v6 documentation.
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
            raise ToolError(str(e))


@mcp.tool(
    tags={"reference"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def get_doc(
    path: Annotated[str, Field(description="Relative path to the documentation file (e.g., 'reference/functions/ta.md').")],
    limit: Annotated[int, Field(description="Maximum characters to return. Use 30000 for large files. 0 = no limit.", ge=0)] = 0,
    offset: Annotated[int, Field(description="Character offset to start reading from.", ge=0)] = 0,
):
    """USE WHEN reading the full content of a Pine Script v6 documentation file.
    Returns the file content; when limit is set, a header shows the char range and offset to continue reading.
    AFTER calling this tool, use offset=<end> to continue if the header indicates more content is available. For large files (ta.md, strategy.md, collections.md, drawing.md, general.md), prefer list_sections() + get_section() instead.
    Data sourced from bundled Pine Script v6 documentation.
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
                    raise ToolError(f"offset {offset} exceeds file size ({total} chars). Use offset < {total}.")
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
            raise ToolError(str(e))


@mcp.tool(
    tags={"reference"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def get_section(
    path: Annotated[str, Field(description="Documentation file path (e.g., 'reference/functions/strategy.md').")],
    header: Annotated[str, Field(description="Header text to find (e.g., 'strategy.exit()' or '## strategy.exit()').")],
    include_children: Annotated[bool, Field(description="Include nested subsections under the matched header.")] = True,
):
    """USE WHEN reading a specific named section from a Pine Script v6 documentation file.
    Returns the section content from the matched header to the next same-level header, with file path and line range.
    AFTER calling this tool, call list_sections(path) if the header was not found, or get_section() again with a child header for a narrower subsection.
    Data sourced from bundled Pine Script v6 documentation.
    """
    with _timed_tool("get_section", path=path, header=header) as log:
        try:
            _validate_path(path)  # check path is allowed
            content = _get_doc_content(path)
            section, start_line, end_line = _find_section(content, header, include_children)
            return f"# {path} (lines {start_line}-{end_line})\n\n{section}"
        except ValueError as e:
            log["error"] = str(e)
            raise ToolError(str(e))


@mcp.tool(
    tags={"search"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def search_docs(
    query: Annotated[str, Field(description="Search terms (case-insensitive). Multi-word queries match sections containing ALL terms.", min_length=1)],
    max_results: Annotated[int, Field(description="Maximum sections to return.", ge=1, le=20)] = 5,
):
    """USE WHEN finding documentation sections that match specific terms across all Pine Script v6 docs.
    Returns up to max_results sections ranked by match count, each with a preview and a get_section() call hint.
    AFTER calling this tool, call get_section(file, header) for each result you want to read in full.
    Data sourced from bundled Pine Script v6 documentation.
    """
    with _timed_tool("search_docs", query=query, max_results=max_results) as log:
        tokens = query.strip().split()
        patterns = [re.compile(re.escape(t), re.IGNORECASE) for t in tokens]
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
                    section_text = "\n".join(section_lines)
                    if all(p.search(section_text) for p in patterns) and current_header != "(preamble)":
                        match_count = sum(sum(1 for p in patterns if p.search(l)) for l in section_lines)
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
            section_text = "\n".join(section_lines)
            if all(p.search(section_text) for p in patterns) and current_header != "(preamble)":
                match_count = sum(sum(1 for p in patterns if p.search(l)) for l in section_lines)
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
async def get_functions(
    namespace: Annotated[str, Field(description="Filter by namespace (e.g., 'ta', 'strategy', 'request'). Empty string returns all functions grouped by namespace.")] = "",
):
    """USE WHEN browsing valid Pine Script v6 functions, optionally filtered to a namespace.
    Returns function names grouped by namespace (e.g. ta.*, strategy.*) or filtered to the requested namespace.
    AFTER calling this tool, call validate_function(fn_name) to check a specific name, or get_section() to read its documentation.
    Data sourced from bundled pine_v6_functions.json.
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
async def validate_function(
    fn_name: Annotated[str, Field(description="Function name to validate (e.g., 'ta.sma', 'strategy.entry', 'plot').", min_length=1)],
) -> str:
    """USE WHEN confirming a Pine Script v6 function name is valid before using it in code.
    Returns a valid/invalid verdict with namespace suggestions or known replacement hints (e.g. ta.adx → ta.dmi, security → request.security).
    AFTER calling this tool, call get_functions(namespace) to list all valid functions in the relevant namespace if the function is invalid.
    Data sourced from bundled pine_v6_functions.json.
    """
    with _timed_tool("validate_function", fn_name=fn_name):
        fn_name = fn_name.strip()

        if not fn_name:
            return "Provide a function name to validate."
        if fn_name in PINE_V6_FUNCTIONS:
            return f"**Valid** — `{fn_name}` is a known Pine Script v6 function (namespaced)."
        if fn_name in PINE_V6_TOPLEVEL:
            return f"**Valid** — `{fn_name}` is a known Pine Script v6 function (top-level)."

        if fn_name in KNOWN_REPLACEMENTS:
            return f"**Invalid** — `{fn_name}` was renamed. {KNOWN_REPLACEMENTS[fn_name]}"

        if "." in fn_name:
            ns = fn_name.rpartition(".")[0]
            if ns in PINE_V6_NAMESPACES:
                suggestion = f"Not found in `{ns}.*`. Use `get_functions('{ns}')` to see all valid functions."
            else:
                available = ", ".join(sorted(PINE_V6_NAMESPACES))
                suggestion = f"Namespace `{ns}` not recognised. Valid namespaces: {available}"
        else:
            suggestion = "Not found. Use `get_functions()` to browse top-level functions, or `get_functions(namespace)` for a specific namespace."

        return f"**Invalid** — `{fn_name}` is not a recognised Pine Script v6 function. {suggestion}"


@mcp.tool(
    tags={"search"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
)
async def resolve_topic(
    query: Annotated[str, Field(description="Exact Pine Script term or known concept keyword (e.g., 'ta.rsi', 'strategy.entry', 'repainting').", min_length=1)],
) -> str:
    """USE WHEN looking up an exact Pine Script API term or known concept keyword.
    Returns the best-matching doc paths with matched keywords and a retrieval suggestion (get_doc or list_sections + get_section).
    AFTER calling this tool, follow the suggestion: call get_doc() for small files or list_sections() + get_section() for large files. For natural language questions use search_docs() instead.
    Data sourced from bundled TOPIC_MAP and doc file content scan.
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
            # Fallback: scan docs for an exact substring match before returning empty
            fallback_pattern = re.compile(re.escape(query), re.IGNORECASE)
            for rel_path in DOCS:
                doc_lines = _get_doc_lines(rel_path)
                if doc_lines and any(fallback_pattern.search(l) for l in doc_lines):
                    path_scores[rel_path] = [query]
                    break
            log["fallback_used"] = bool(path_scores)

        if not path_scores:
            return (
                f'No match for "{query}". '
                f"Read the docs://manifest resource for routing guidance, "
                f'or use search_docs("{query}") to search by keyword.'
            )

        ranked = sorted(path_scores.items(), key=lambda x: len(x[1]), reverse=True)

        existing_paths = set(path_scores.keys())
        matches = []
        for path, keywords in ranked:
            companions = DOC_COMPANIONS.get(path, [])
            filtered_companions = [c for c in companions if c not in existing_paths]
            matches.append({"path": path, "keywords": keywords, "read_with": filtered_companions})

        top_path = matches[0]["path"]
        if top_path in LARGE_DOCS:
            suggestion = f"Large file — use list_sections('{top_path}') to find headers, then get_section() to read specific sections."
        elif len(matches) > 1:
            paths = [m["path"] for m in matches[:3]]
            suggestion = f"Read these together: {', '.join(paths)}. Use get_section() for large files."
        else:
            suggestion = f"Use get_doc('{top_path}') to read the top match."

        lines = [f"# resolve_topic: {query}", ""]
        for m in matches:
            lines.append(f"- `{m['path']}` — matched: {', '.join(m['keywords'])}")
            if m["read_with"]:
                lines.append(f"  Read with: {', '.join(m['read_with'])}")
        lines.append("")
        lines.append(suggestion)

        return "\n".join(lines)



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


@mcp.custom_route("/.well-known/mcp/server-card.json", methods=["GET"])
async def smithery_server_card(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"serverInfo": {"name": "pinescript-mcp", "version": __version__}})


@mcp.custom_route("/.well-known/glama.json", methods=["GET"])
async def glama_claim(request):
    from starlette.responses import JSONResponse
    return JSONResponse({
        "$schema": "https://glama.ai/mcp/schemas/connector.json",
        "maintainers": [{"email": "paul@bouch.dev"}],
    })


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics(request):
    """Prometheus metrics endpoint for Fly.io scraping."""
    from starlette.responses import Response
    return Response(generate_latest(METRICS_REGISTRY), media_type=CONTENT_TYPE_LATEST)


class _HttpGuard:
    """Return a held-open SSE stream for GET /mcp; 405 for DELETE /mcp.

    claude.ai probes GET /mcp to establish an SSE stream before sending MCP
    protocol messages via POST. With stateless_http=True FastMCP only registers
    POST routes, so GET returns 405 — claude.ai treats this as a connection
    failure even though POST works fine.

    Fix: intercept GET /mcp and return 200 text/event-stream held open until
    the client disconnects. FastMCP never sees the GET; stateless semantics
    are preserved. DELETE is rejected (405) — stateless servers have no sessions.
    """

    def __init__(self, app, mcp_path: bytes = b"/mcp"):
        self.app = app
        self._mcp_path = mcp_path.rstrip(b"/")

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "").rstrip("/").encode()
            method = scope.get("method", "").upper().encode()
            if path == self._mcp_path:
                if method == b"GET":
                    await send({"type": "http.response.start", "status": 200, "headers": [
                        (b"content-type", b"text/event-stream"),
                        (b"cache-control", b"no-cache"),
                        (b"connection", b"keep-alive"),
                    ]})
                    await send({"type": "http.response.body", "body": b"", "more_body": True})
                    while True:
                        event = await receive()
                        if event["type"] == "http.disconnect":
                            break
                    return
                if method == b"DELETE":
                    from starlette.responses import Response as StarletteResponse
                    await StarletteResponse("Method Not Allowed", status_code=405, headers={"Allow": "POST"})(scope, receive, send)
                    return
        await self.app(scope, receive, send)


class _AcceptNormalizer:
    """Normalize Accept header on /mcp to prevent 406 Not Acceptable.

    Workaround for modelcontextprotocol/python-sdk#2349 — the MCP SDK
    requires both application/json AND text/event-stream in the Accept
    header, but Anthropic's MCP proxy and other clients send them
    separately per request type. Stamp the combined value on /mcp only.
    """
    def __init__(self, app, mcp_path: str = "/mcp"):
        self.app = app
        self._mcp_path = mcp_path.rstrip("/")

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("path", "").rstrip("/") == self._mcp_path:
            headers = [
                (b"accept", b"application/json, text/event-stream")
                if name.lower() == b"accept"
                else (name, value)
                for name, value in scope.get("headers", [])
            ]
            scope = {**scope, "headers": headers}
        await self.app(scope, receive, send)


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

        # Streamable HTTP only — legacy SSE transport (/sse + /messages/) dropped.
        # stateless_http=True: no per-session state, safe for Fly.io multi-instance routing.
        app = mcp.http_app(path="/mcp", stateless_http=True)

        config = uvicorn.Config(
            _HttpGuard(_AcceptNormalizer(app)),
            host=args.host,
            port=args.port,
            log_level="info",
            forwarded_allow_ips="*",
            proxy_headers=True,
        )
        server = uvicorn.Server(config)
        asyncio.run(server.serve())
    else:
        mcp.run()


if __name__ == "__main__":
    main()
