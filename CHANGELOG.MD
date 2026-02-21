# CHANGELOG

## v0.5.0 → v0.6.0 Changelog

### v0.5.0 → v0.5.1 

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