# CHANGELOG

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
