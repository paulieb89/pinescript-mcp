# CHANGELOG

## v0.6.5 → v0.6.7

### Fixed: E016 duplicating E005/E006 on deprecated v5 functions

`_lint_undeclared` now accepts `pattern_issues` and suppresses identifiers already flagged by other rules. When `study()` triggers E005 and `security()` triggers E006, E016 no longer adds redundant "'study' is used but never declared" noise. Typical v5 script drops from 5 issues to 3.

Extraction is message-based — parses the function name from `"study() does not exist..."` style messages via `msg.split("(")[0]`. No hardcoded rule-to-identifier mapping needed.

## v0.6.4 → v0.6.5

### Added: E016_undeclared_identifier lint rule

New AST-based lint rule that walks the pynescript parse tree to detect identifiers used but never declared. Catches the #1 gap in the linter — TradingView's `Undeclared identifier "x"` errors that previously passed through undetected.

- Collects declarations from: assignments, function params, for loops, imports, UDTs, enums
- Built-in suppression: 750+ identifiers (variables, namespaces, type keywords, constants)
- Only suppresses attribute prefixes for known builtins — user objects like `g_levels.high` still checked
- Skipped when syntax errors exist (avoids cascading false positives)
- Severity: `warning` (flat scope analysis, conservative)

### Added: Manifest lint-before-deliver instruction

LLM_MANIFEST.md now instructs Claude to always call `lint_script` on generated Pine Script before presenting it to the user. Creates a self-correction loop: write → lint → fix → re-lint → deliver clean code.

## v0.6.3 → v0.6.4

### Added: Repainting routing example in manifest

New routing example explicitly shows the two-doc retrieval pattern for repainting questions (`concepts/timeframes.md` + `reference/functions/request.md`). Comments like `← lookahead warnings, calc_on_every_tick` signal which doc carries which knowledge — closing the quality gap between claude.ai (which reads the full manifest) and Claude Code (which tends to stop after the function reference).

### Added: HTTP client call_tool hint in routing examples

Routing examples section now includes a note directing HTTP clients to wrap tool calls with `call_tool()`, matching the preamble's discovery instructions. Eliminates cold-start tool call failures.

### Removed: sync-docs.sh

The package manifest has diverged significantly from the repo-level `docs/LLM_MANIFEST.md` (212 lines vs 96). The sync script would clobber the enhanced package manifest. Removed to prevent accidental overwrites — will be rewritten when needed.

### Added: BM25 tool discovery for HTTP clients

claude.ai's 5-tool injection limit meant users couldn't access half the tools. Now HTTP mode uses FastMCP's `BM25SearchTransform` for progressive disclosure:

**claude.ai / HTTP:**
- `get_manifest` and `lint_script` always visible (pinned)
- `search_tools` + `call_tool` for on-demand discovery of all 10 tools
- Manifest opens with `call_tool` patterns — no cold-start friction

**Claude Code / stdio:** Unchanged — all 10 tools load directly, manifest has no `call_tool` instructions.

### Added: Environment-aware manifest

`get_manifest()` detects `ctx.transport == "streamable-http"` and prepends HTTP-specific discovery instructions. Stdio clients get the standard manifest. No module-level flags — uses FastMCP's built-in transport detection.

### Added: Lint input size guard

`lint_script` rejects scripts over 50KB with `E000_script_too_large`. Prevents the AST parser from stalling on pathological inputs (p95 was 4-5s on large scripts).

### Changed: FastMCP 3.0.1 → 3.1.0

Required for `BM25SearchTransform`. No breaking changes.

### Fixed: Default port 8000 → 8080

Argparse default now matches Dockerfile `ENV PORT=8080` and fly.toml `internal_port = 8080`.

## v0.6.2 → v0.6.3

### Added: Prometheus metrics endpoint

New `/metrics` endpoint exposes tool-level observability for Fly.io's managed Grafana (fly-metrics.net):
- `pinescript_tool_calls_total` — counter by tool name
- `pinescript_tool_errors_total` — counter by tool name
- `pinescript_tool_duration_seconds` — histogram with latency buckets (1ms–5s)

Instrumentation lives in `_timed_tool.__exit__()` so all 9 tools are covered with zero per-tool code. Custom `CollectorRegistry` keeps `/metrics` output clean (no default Python GC/process metrics).

Fly scrapes every 15s via `[metrics]` section in fly.toml. PromQL queries for call rate, p95 latency, error rate, and top tools all work out of the box.

New dependency: `prometheus_client>=0.21.0`.

## v0.6.1 → v0.6.2

### Fixed: list_sections subsection noise

`list_sections()` now returns only `##`-level headers, filtering out `### Returns`, `### Remarks`, `### Code Example` subsections that appear for every function. ta.md drops from ~200 lines to ~65 meaningful function headers. `get_section(include_children=True)` still returns full subsection content when reading.

## v0.5.2 → v0.6.0

### Breaking: TOPIC_MAP simplified (168 → 49 entries)

`resolve_topic()` now handles only exact Pine Script API terms (`ta.rsi`, `strategy.entry`, `repainting`, etc.). Natural language queries return 0 matches with a suggestion to use `get_manifest()`. This is intentional — client LLMs route natural language better than keyword matching.

Removed: all broad single-word entries (`strategy`, `rsi`, `array`, `color`, `plot`, etc.), natural language phrases (`trailing stop`, `color bars`, `format string`, etc.), and the fuzzy fallback (source of "for"/"format" false positives).

### Fixed: output schema breaking large file responses

Removed `-> str` return type annotations from 7 doc-serving tools. FastMCP auto-generated `output_schema` from these, which caused "outputSchema defined but no structured output returned" errors when `ResponseLimitingMiddleware` truncated large responses. Pydantic-returning tools (`ResolveResult`, `LintResult`, `ValidationResult`) keep their types.

### Fixed: execution_model.md missing from LARGE_DOCS

At 122KB it was the largest doc file but wasn't in `LARGE_DOCS`. `resolve_topic("varip")` now correctly suggests `list_sections()`. `get_doc` auto-limits LARGE_DOCS files to 30KB with pagination hints.

### Fixed: disk cache masking code changes

`ResponseCachingMiddleware` with 1-hour TTL was serving stale responses after code changes. Not a code fix — documented as operational awareness.

### Improved: tool signatures and docstrings

- Removed unused `ctx: Context` from all 10 tools (FastMCP injects on demand; none used it)
- `get_manifest` docstring: "START HERE for natural language Pine Script questions"
- `resolve_topic` docstring: scoped to exact terms, points to `get_manifest()` for natural language
- `get_doc` docstring: warns about large files, suggests `list_sections()` + `get_section()`
- `validate_function`: stripped fuzzy matching, points to `get_functions(namespace)` on miss
- `lint_script`: added 30s timeout (ReDoS protection)
- `resolve_topic`: removed stale "entry" tag

### Improved: LLM_MANIFEST.md and list_docs

- Tool workflow section rewritten — `resolve_topic` and `get_manifest` on equal footing
- Routing examples updated to show which path each query takes
- `list_docs` now shows Migration as its own category

### Previous changes (v0.5.2 → v0.6.0-rc)

- Duplicate "method" key fixed
- publishing_scripts.md dead reference removed
- `_timed_tool` context manager replaced ~100 lines of logging boilerplate
- `list_sections` tool added (10th tool)
- `LLM_MANIFEST.md` full rewrite with 7 routing examples
- `_logger` via `get_logger` — tool calls visible in Fly logs
- Importlib dead branches collapsed

## v0.5.1 → v0.5.2

Dependency and lockfile updates.

## v0.5.0 → v0.5.1

### MCP Annotations
Added readOnlyHint, idempotentHint, openWorldHint annotations to all tools.
This enables clients like Claude and ChatGPT to skip confirmation prompts
for these read-only documentation tools.

## v0.4.1 → v0.5.0

### Framework Migration
Migrated from mcp SDK to fastmcp package - enables middleware support and enhanced features

### New Features
Response Caching
Added ResponseCachingMiddleware with 1-hour TTL for static doc lookups (get_doc, get_section, list_docs, get_manifest)
Structured Outputs (Pydantic models)
LintResult - lint tool now returns typed JSON
ValidationResult - function validation returns typed JSON
ResolveResult / TopicMatch - topic resolution returns typed JSON

### 3 Prompt Templates
debug_error - helps debug Pine Script compilation errors
convert_v5_to_v6 - guides v5 to v6 migration
explain_function - explains Pine Script functions in detail

### 5 New Lint Rules (10 → 15 total)
Rule	Type	Description
E013	error	input.enum() with options array (v6 requires enum type)
E014	error	strategy() missing title parameter
E015	error	Mismatched string quotes
W004	warning	max_bars_back set ≥5000 (performance)
W005	warning	Variable declared with var but potentially unused
Tool Tags
All tools now have tags for component organization (search, reference, validation, linting)
