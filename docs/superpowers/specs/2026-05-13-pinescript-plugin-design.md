# Pinescript Plugin — Design Spec

**Date:** 2026-05-13
**Status:** Approved, ready for implementation planning
**Owner:** bch

## Purpose

Ship a Claude Code plugin in the `pinescript-mcp` repository that turns Claude into a useful pairing partner for Pine Script v6 authoring. The plugin's value proposition is **first-try, validated Pine Script code from natural-language descriptions** — no hallucinated function names, no v5/v6 confusion.

Secondary goal: build plugin-authoring practice while the Claude Code / Codex / Cursor plugin ecosystems are still new, using a domain (Pine Script) and infrastructure (`pinescript-mcp` on PyPI + Fly.io) the author already owns.

## Scope

**In scope (v0.1):**
- Two agentskills.io spec-compliant skills.
- Claude Code plugin wrapper (`.claude-plugin/plugin.json`, `.mcp.json`).
- README with install instructions and example prompts.
- Validation via the `skills-ref` CLI.

**Out of scope (deferred to v0.2 or later):**
- A `pine-reviewer` autonomous agent for repainting/lookahead/security checks.
- A dedicated `v5-to-v6-migration` skill.
- A PreToolUse hook validating `.pine` file writes.
- Marketplace listing or distribution beyond install-by-URL.
- Codex or Cursor variants.

## Killer flow

> User: *"Write me a Pine Script indicator that plots an RSI divergence signal on a 5-minute chart."*
>
> Claude (with plugin installed): clarifies intent if needed, fetches the relevant Pine v6 doc sections via the MCP server, validates every function call against the v6 allowlist, returns production-ready v6 code with `//@version=6` and a brief explanation. No invented functions. No v5 holdovers.

## Architecture

Two layers, cleanly separated:

1. **Claude Code plugin wrapper.** Manifest + MCP wiring. Lives under `plugin/` in the existing `pinescript-mcp` repo. Coexists with the Python project (`src/`, `pyproject.toml`, `fly.toml`); does not affect the PyPI build (`hatch` only globs `src/pinescript_mcp/**`).
2. **Agentskills.io-compliant skills.** Two skills, each in its own directory with a `SKILL.md` that conforms strictly to the [agentskills.io specification](https://agentskills.io/specification.md). No Claude Code-specific extensions.

The skills depend on the `pinescript-mcp` MCP server (registered in `.mcp.json`) for doc lookup and function validation. The plugin ships pointing at the hosted Fly.io endpoint (`https://pinescript-mcp.fly.dev/mcp`) for zero-install UX; the README documents the local stdio alternative (`uvx pinescript-mcp`) for offline or private use.

## Components

### Skill 1: `pine`

The workhorse. Handles both natural-language Pine Script requests and explicit `/pine` invocation. Two activation paths, one skill — keeps the codebase free of two near-identical skills that would drift over time.

**Frontmatter (strict agentskills.io):**
```yaml
---
name: pine
description: >-
  Writes Pine Script v6 indicators and strategies from natural-language
  descriptions. Use when the user invokes /pine, asks Claude to write a
  Pine Script indicator/strategy/TradingView script, or describes an indicator
  they want built. Routes through the pinescript MCP server: fetches docs,
  validates every function call against the v6 allowlist before emitting code,
  returns production-ready scripts with //@version=6 annotation.
license: MIT
compatibility: >-
  Designed for Claude Code; requires the pinescript MCP server (hosted at
  https://pinescript-mcp.fly.dev/mcp or local via uvx pinescript-mcp).
metadata:
  version: "0.1.0"
  repository: https://github.com/paulieb89/pinescript-mcp
---
```

**Body (~1,200–1,500 words, imperative voice, under 500 lines):**
The mandatory authoring loop, step by step:

1. **Clarify intent if ambiguous.** At most one question, and only when essential (overlay vs separate pane, timeframe-locked vs adaptive, input parameters).
2. **Route via the manifest.** Read the `docs://manifest` MCP resource first to identify relevant doc sections.
3. **Read the doc sections** for any function/concept the script will use. Use `get_section` over `get_doc` where possible to keep context tight.
4. **Draft the code** with `//@version=6` annotation, correct script-type declaration (`indicator(` vs `strategy(`), and named-argument calling convention.
5. **Validate every function call** via the `validate_function` MCP tool before emitting. Non-negotiable. If a function is invalid or renamed, look up the suggested replacement and use that.
6. **Emit the code** in a code block with a brief plain-English explanation of each block (one sentence per logical section, not line-by-line).
7. **Offer next steps:** refine a parameter, explain a section in depth, save to a `.pine` file.

**Supporting files:**
- `references/v6-checklist.md` — Pine v6 gotchas (version annotation, script-type declaration, naming rules, common v5→v6 traps).
- `references/validation-workflow.md` — the exact `validate_function` call pattern and how to interpret the response.
- `assets/rsi-divergence.pine` — one fully worked, validated example indicator. Acts as a quality anchor for the model.

### Skill 2: `pine-validate`

A focused utility. Validates a Pine snippet or function reference against the v6 allowlist.

**Frontmatter (strict agentskills.io):**
```yaml
---
name: pine-validate
description: >-
  Validates Pine Script function calls against the v6 allowlist. Use when
  the user invokes /pine-validate, pastes a Pine snippet and asks if it
  compiles, asks whether a specific function like ta.adx or security() is
  valid Pine v6, or wants to check a script for hallucinated/renamed
  function references before running it on TradingView. Returns the list
  of invalid calls with known-replacement suggestions.
license: MIT
compatibility: >-
  Designed for Claude Code; requires the pinescript MCP server (hosted at
  https://pinescript-mcp.fly.dev/mcp or local via uvx pinescript-mcp).
metadata:
  version: "0.1.0"
  repository: https://github.com/paulieb89/pinescript-mcp
---
```

**Body (~400–600 words):**
1. Parse the input: extract all function references from the snippet (anything matching `<namespace>.<func>(` or `<func>(` at function-call positions).
2. For each unique function reference, call `validate_function`.
3. Report results in a compact table: function name, valid (yes/no), suggested replacement if any.
4. If all functions valid, say so explicitly.

**Supporting files:**
- `references/known-replacements.md` — a digest of the `KNOWN_REPLACEMENTS` map maintained inside the MCP server (`ta.adx → ta.dmi`, `security → request.security`, etc.), kept readable for users debugging without running the validator.

## File structure

```
pinescript-mcp/
├── src/pinescript_mcp/         # existing, untouched
├── plugin/                      # NEW — entire plugin lives here
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── .mcp.json
│   ├── skills/
│   │   ├── pine/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   │   ├── v6-checklist.md
│   │   │   │   └── validation-workflow.md
│   │   │   └── assets/
│   │   │       └── rsi-divergence.pine
│   │   └── pine-validate/
│   │       ├── SKILL.md
│   │       └── references/
│   │           └── known-replacements.md
│   └── README.md
└── README.md                    # existing — add plugin install badge
```

### `plugin/.claude-plugin/plugin.json`

```json
{
  "name": "pinescript",
  "version": "0.1.0",
  "description": "Pine Script v6 authoring assistant — writes validated TradingView indicators and strategies.",
  "author": { "name": "bch" },
  "homepage": "https://github.com/paulieb89/pinescript-mcp",
  "repository": "https://github.com/paulieb89/pinescript-mcp",
  "license": "MIT",
  "keywords": ["pine-script", "tradingview", "indicators", "trading"]
}
```

### `plugin/.mcp.json`

```json
{
  "mcpServers": {
    "pinescript": {
      "type": "http",
      "url": "https://pinescript-mcp.fly.dev/mcp"
    }
  }
}
```

## Data flow

```
User prompt
   │
   ▼
Skill activation (description match)  ──►  pine  OR  pine-validate
   │
   ▼
Skill body executes (instructions for Claude)
   │
   ▼
MCP calls to pinescript server (hosted)
   ├── docs://manifest         (resource)
   ├── get_section             (tool)
   ├── resolve_topic           (tool)
   ├── validate_function       (tool, mandatory before emit)
   ▼
Validated code or validation report returned to user
```

No state lives in the plugin. Each invocation is stateless; the MCP server caches responses for ~5 minutes via its own middleware.

## Constraints from agentskills.io spec

- Skill `name` must match parent directory name, lowercase + hyphens only, no consecutive hyphens, no leading/trailing hyphen, ≤64 chars.
- `description` ≤1024 chars and must convey both *what* the skill does and *when* to use it.
- `SKILL.md` body ≤5000 tokens recommended, ≤500 lines.
- Supporting files referenced relative to skill root, one level deep.
- No `argument-hint` or `model` frontmatter (Claude Code extensions, not in spec).
- Allowed optional dirs only: `scripts/`, `references/`, `assets/`.

## Validation & ship checklist

1. `skills-ref validate plugin/skills/pine` passes.
2. `skills-ref validate plugin/skills/pine-validate` passes.
3. Local install: `claude --plugin-dir /home/bch/dev/mcpfleet/pinescript-mcp/plugin`.
4. `/mcp` shows `pinescript` server connected.
5. Manual trigger tests:
   - *"Write me a Pine Script indicator that plots a 200 EMA with breakout signals."* → `pine` activates.
   - *"/pine RSI divergence on 5m chart"* → `pine` activates.
   - *"Is `ta.adx` a valid Pine v6 function?"* → `pine-validate` activates.
6. Emitted code includes `//@version=6` and contains only validated functions.
7. README documents: install command, prerequisite note (hosted MCP server, no setup needed), three example prompts, link to the local-MCP fallback.
8. Commit message follows repo style.

## Implementation plan (high level)

1. **Scaffolding.** Create `plugin/` directory structure, write `plugin.json`, `.mcp.json`, empty skill directories.
2. **Skill authoring via subagents.** Dispatch two parallel `skill-creator` subagents — one for `pine`, one for `pine-validate` — each given this spec and the agentskills.io specification.
3. **Review subagent output.** Reconcile against this spec. Tighten descriptions for trigger accuracy. Add the worked example asset.
4. **Validate.** Run `skills-ref validate` on both skills.
5. **Local install and manual testing.** Walk the six trigger tests above.
6. **README + plugin install badge in repo root README.**
7. **Commit.** Conventional commit message.

A detailed step-by-step plan with verification at each step will be produced by the `writing-plans` skill as the next workflow step.

## Open risks

- **Trigger accuracy.** The `description` field is the only matcher signal. If `pine` over-triggers (e.g. on any mention of "indicator"), it'll be noisy. Mitigation: lock the description to "Pine Script" / "TradingView" / "/pine" specific phrases; test 5+ negative prompts ("write me a momentum indicator" without the word "Pine") and confirm they don't fire.
- **MCP availability.** The hosted Fly.io endpoint is single-region with `min_machines_running = 1`. A cold-start or outage breaks the plugin's value entirely. Mitigation: README explicitly documents the `uvx pinescript-mcp` stdio fallback so users can self-host if needed.
- **Spec drift.** agentskills.io is new; the spec may evolve. Mitigation: pin to the version of the spec read on this design date (2026-05-13) and re-validate before each release.

## Definition of done

A user runs `claude --plugin-dir <repo>/plugin`, asks Claude to write a Pine Script RSI divergence indicator, and receives validated v6 code that compiles on TradingView on the first try. Both `skills-ref validate` calls pass. README is clear enough that a new user gets to the same outcome without asking questions.
