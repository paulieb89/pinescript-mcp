# Pinescript Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Claude Code plugin under `plugin/` in the `pinescript-mcp` repo that turns Claude into a Pine Script v6 pairing partner via two agentskills.io-compliant skills (`pine`, `pine-validate`) wired to the existing hosted MCP server.

**Architecture:** Two-layer plugin. The Claude Code wrapper (`.claude-plugin/plugin.json`, `.mcp.json`) handles install + MCP registration. Two skills under `skills/` implement the user-facing behaviour per the [agentskills.io specification](https://agentskills.io/specification.md). All MCP calls go to the hosted Fly.io endpoint; no local server required. The two skills are independent and can be authored in parallel via two `skill-creator` subagents.

**Tech Stack:** Markdown (skill content), JSON (plugin manifests), `skills-ref` CLI (validation), Claude Code (host), existing `pinescript-mcp` server on Fly.io.

**Reference docs:**
- Design spec: [docs/superpowers/specs/2026-05-13-pinescript-plugin-design.md](../specs/2026-05-13-pinescript-plugin-design.md)
- Agentskills.io spec: https://agentskills.io/specification.md

---

## File map

| Path | Responsibility |
|---|---|
| `plugin/.claude-plugin/plugin.json` | Claude Code plugin manifest. Name, version, repo, license. |
| `plugin/.mcp.json` | Registers the hosted `pinescript` MCP server. |
| `plugin/skills/pine/SKILL.md` | Pine v6 authoring workflow. Triggers on Pine Script asks + `/pine`. |
| `plugin/skills/pine/references/v6-checklist.md` | Pine v6 gotchas reference, loaded on demand. |
| `plugin/skills/pine/references/validation-workflow.md` | How to use `validate_function` from the skill. |
| `plugin/skills/pine/assets/rsi-divergence.pine` | One worked, validated v6 example indicator. |
| `plugin/skills/pine-validate/SKILL.md` | Pine snippet/function validator. Triggers on validation asks + `/pine-validate`. |
| `plugin/skills/pine-validate/references/known-replacements.md` | Reference of common invalid → valid function mappings. |
| `plugin/README.md` | Install instructions, prerequisite note, example prompts. |

---

## Task 1: Scaffolding

**Files:**
- Create: `plugin/.claude-plugin/plugin.json`
- Create: `plugin/.mcp.json`
- Create: `plugin/skills/pine/` (empty directory)
- Create: `plugin/skills/pine-validate/` (empty directory)
- Create: `plugin/skills/pine/references/` (empty directory)
- Create: `plugin/skills/pine/assets/` (empty directory)
- Create: `plugin/skills/pine-validate/references/` (empty directory)

- [ ] **Step 1: Create directory structure**

```bash
cd /home/bch/dev/mcpfleet/pinescript-mcp
mkdir -p plugin/.claude-plugin
mkdir -p plugin/skills/pine/references
mkdir -p plugin/skills/pine/assets
mkdir -p plugin/skills/pine-validate/references
```

Expected: directories exist; `ls -R plugin/` shows the tree.

- [ ] **Step 2: Write `plugin/.claude-plugin/plugin.json`**

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

- [ ] **Step 3: Write `plugin/.mcp.json`**

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

- [ ] **Step 4: Verify JSON parses**

```bash
python -c "import json; json.load(open('plugin/.claude-plugin/plugin.json')); json.load(open('plugin/.mcp.json')); print('OK')"
```

Expected output: `OK`

- [ ] **Step 5: Skip commit (user will commit after full review). Mark task complete.**

---

## Task 2: Author `pine` skill via subagent (parallel with Task 3)

**Files:**
- Create: `plugin/skills/pine/SKILL.md`
- Create: `plugin/skills/pine/references/v6-checklist.md`
- Create: `plugin/skills/pine/references/validation-workflow.md`
- Create: `plugin/skills/pine/assets/rsi-divergence.pine`

- [ ] **Step 1: Dispatch skill-creator subagent for `pine`**

Use the `Agent` tool with `subagent_type: general-purpose` and the following prompt:

```
You are authoring a Claude Code skill that conforms strictly to the agentskills.io specification (https://agentskills.io/specification.md). Use the superpowers `writing-skills` skill or the `skill-creator` skill to guide your authoring, but the final output MUST conform to the agentskills.io spec — not Claude Code-specific extensions.

REFERENCE THESE TWO DOCS BEFORE STARTING:
1. Design spec for this plugin: /home/bch/dev/mcpfleet/pinescript-mcp/docs/superpowers/specs/2026-05-13-pinescript-plugin-design.md
   - Read the "Skill 1: `pine`" section carefully — that is the contract you are fulfilling.
2. Agentskills.io specification: https://agentskills.io/specification.md (use WebFetch)

YOUR JOB: Author exactly four files for the `pine` skill in /home/bch/dev/mcpfleet/pinescript-mcp/plugin/skills/pine/:

1. SKILL.md — strict agentskills.io spec. Frontmatter fields ONLY: name, description, license, compatibility, metadata. NO argument-hint, NO model, NO Claude Code-specific extensions. Body ≤500 lines, ≤5000 tokens, imperative voice, written FOR Claude (not TO the user). The body must implement the 7-step authoring loop from the design spec verbatim in structure (clarify → manifest → docs → draft → validate → emit → next steps). Reference the supporting files using relative paths.

2. references/v6-checklist.md — Pine v6 gotchas: version annotation (`//@version=6`), script-type declaration (`indicator(` vs `strategy(`), named-argument calling convention, common v5→v6 traps (e.g. `security` is now `request.security`, `study(` is now `indicator(`). Concise reference, 200–400 lines max.

3. references/validation-workflow.md — Exact pattern for calling the `validate_function` MCP tool from within the skill workflow. Show the input shape, output shape, and what to do with invalid/renamed responses. 100–200 lines.

4. assets/rsi-divergence.pine — One complete, valid, v6-compliant Pine Script indicator implementing RSI divergence detection on the current chart. Must compile on TradingView. Include `//@version=6`, `indicator(` declaration, RSI calculation, pivot detection, divergence logic, and plotting. This file acts as a quality anchor — the model will see it as a reference for what good emitted code looks like.

CONSTRAINTS:
- The `name` frontmatter field MUST be exactly `pine` (matches the parent directory).
- The `description` field must be ≤1024 chars AND must mention BOTH the trigger phrases for natural-language asks ("write me a Pine Script indicator", "TradingView script", "Pine v6 strategy") AND the explicit `/pine` invocation. Pack with keywords. See the design spec for the exact recommended description text.
- The MCP server referenced in `compatibility` is the hosted endpoint at https://pinescript-mcp.fly.dev/mcp (with `uvx pinescript-mcp` as the local fallback).
- Available MCP tools the skill will call: resolve_topic, search_docs, list_docs, list_sections, get_doc, get_section, get_functions, validate_function, list_prompts, get_prompt. Available MCP resources: docs://manifest, docs://functions, docs://{path*}.
- The SKILL.md body MUST instruct Claude to call `validate_function` for every Pine function reference before emitting code. This is non-negotiable and is the plugin's primary value prop.

WHEN COMPLETE: List the four files you created with their absolute paths. Do NOT commit. Do NOT modify any file outside plugin/skills/pine/.
```

Run this subagent IN PARALLEL with the Task 3 subagent (same message, two Agent tool calls).

- [ ] **Step 2: Wait for subagent completion, then verify files exist**

```bash
ls -la plugin/skills/pine/SKILL.md \
       plugin/skills/pine/references/v6-checklist.md \
       plugin/skills/pine/references/validation-workflow.md \
       plugin/skills/pine/assets/rsi-divergence.pine
```

Expected: all four files exist with non-zero size.

- [ ] **Step 3: Verify SKILL.md frontmatter conforms to spec**

```bash
# Extract frontmatter
sed -n '/^---$/,/^---$/p' plugin/skills/pine/SKILL.md | head -50
```

Manually check:
- `name: pine` (exact match to dir name)
- `description` is ≤1024 chars (`wc -c` on the description value)
- No forbidden fields (no `argument-hint`, no `model`, no `tools`)
- Optional fields if present are valid: `license`, `compatibility`, `metadata`

- [ ] **Step 4: Verify SKILL.md body length**

```bash
wc -l plugin/skills/pine/SKILL.md
```

Expected: ≤500 lines.

- [ ] **Step 5: Skip commit. Mark task complete.**

---

## Task 3: Author `pine-validate` skill via subagent (parallel with Task 2)

**Files:**
- Create: `plugin/skills/pine-validate/SKILL.md`
- Create: `plugin/skills/pine-validate/references/known-replacements.md`

- [ ] **Step 1: Dispatch skill-creator subagent for `pine-validate`**

Use the `Agent` tool with `subagent_type: general-purpose`. Run IN PARALLEL with Task 2 (same message, two Agent tool calls).

```
You are authoring a Claude Code skill that conforms strictly to the agentskills.io specification (https://agentskills.io/specification.md). Use the superpowers `writing-skills` skill or `skill-creator` skill to guide your authoring, but the final output MUST conform to the agentskills.io spec — not Claude Code-specific extensions.

REFERENCE THESE TWO DOCS BEFORE STARTING:
1. Design spec for this plugin: /home/bch/dev/mcpfleet/pinescript-mcp/docs/superpowers/specs/2026-05-13-pinescript-plugin-design.md
   - Read the "Skill 2: `pine-validate`" section carefully — that is the contract you are fulfilling.
2. Agentskills.io specification: https://agentskills.io/specification.md (use WebFetch)
3. The MCP server's known-replacements logic is in /home/bch/dev/mcpfleet/pinescript-mcp/src/pinescript_mcp/server.py — search for `KNOWN_REPLACEMENTS` to find the canonical mappings. Mirror them in references/known-replacements.md.

YOUR JOB: Author exactly two files for the `pine-validate` skill in /home/bch/dev/mcpfleet/pinescript-mcp/plugin/skills/pine-validate/:

1. SKILL.md — strict agentskills.io spec. Frontmatter fields ONLY: name, description, license, compatibility, metadata. NO Claude Code-specific extensions. Body ≤300 lines, imperative voice, FOR Claude. Implement the 4-step validation workflow from the design spec: parse → call validate_function for each unique reference → report in a compact table → handle the "all valid" case.

2. references/known-replacements.md — A human-readable digest of the KNOWN_REPLACEMENTS map from the MCP server. Format as a table: invalid call | suggested replacement | reason/version note. Pull the exact mappings from src/pinescript_mcp/server.py.

CONSTRAINTS:
- The `name` frontmatter field MUST be exactly `pine-validate` (matches the parent directory).
- The `description` field must be ≤1024 chars and must trigger on both natural-language asks ("is ta.adx valid Pine v6?", "validate this Pine snippet") AND the explicit `/pine-validate` invocation. Pack with keywords.
- The MCP server referenced in `compatibility` is the hosted endpoint at https://pinescript-mcp.fly.dev/mcp (with `uvx pinescript-mcp` as the local fallback).
- The relevant MCP tool is `validate_function`. Show its exact call shape in the SKILL.md.
- The output table format must be deterministic — always: function name | valid (yes/no) | suggested replacement (if invalid).

WHEN COMPLETE: List the two files you created with their absolute paths. Do NOT commit. Do NOT modify any file outside plugin/skills/pine-validate/.
```

- [ ] **Step 2: Wait for subagent completion, then verify files exist**

```bash
ls -la plugin/skills/pine-validate/SKILL.md \
       plugin/skills/pine-validate/references/known-replacements.md
```

Expected: both files exist with non-zero size.

- [ ] **Step 3: Verify SKILL.md frontmatter conforms to spec**

```bash
sed -n '/^---$/,/^---$/p' plugin/skills/pine-validate/SKILL.md | head -50
```

Manually check:
- `name: pine-validate`
- `description` ≤1024 chars
- No forbidden fields
- Optional fields valid

- [ ] **Step 4: Verify body length**

```bash
wc -l plugin/skills/pine-validate/SKILL.md
```

Expected: ≤300 lines.

- [ ] **Step 5: Verify known-replacements matches server source of truth**

```bash
grep -A 20 "KNOWN_REPLACEMENTS" /home/bch/dev/mcpfleet/pinescript-mcp/src/pinescript_mcp/server.py | head -40
```

Cross-check the mappings in `references/known-replacements.md` against this grep. Any mismatch is a bug — fix the reference file.

- [ ] **Step 6: Skip commit. Mark task complete.**

---

## Task 4: Validate both skills against the agentskills.io spec

**Files:** (no modifications, validation only)

- [ ] **Step 1: Install `skills-ref` if not present**

```bash
which skills-ref || pipx install skills-ref || uvx --from skills-ref skills-ref --help
```

If `skills-ref` is not on PATH and pipx/uvx are unavailable, skip to Step 3 (manual checklist).

- [ ] **Step 2: Run validation on both skills**

```bash
skills-ref validate plugin/skills/pine
skills-ref validate plugin/skills/pine-validate
```

Expected: both exit 0 with no errors.

If either fails: read the error, fix in the SKILL.md or supporting files, re-run.

- [ ] **Step 3: Manual spec-compliance checklist (always run, even if Step 2 passed)**

For each of `plugin/skills/pine/SKILL.md` and `plugin/skills/pine-validate/SKILL.md`:

- [ ] `name` matches parent directory name exactly
- [ ] `name` is lowercase letters/numbers/hyphens only, 1–64 chars, no leading/trailing hyphen, no consecutive hyphens
- [ ] `description` exists, ≤1024 chars, non-empty
- [ ] `description` includes BOTH "what" and "when to use"
- [ ] Frontmatter contains no fields outside: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`
- [ ] Body is ≤500 lines (`pine`) or ≤300 lines (`pine-validate`)
- [ ] Any file references in the body use relative paths (e.g. `references/v6-checklist.md`)
- [ ] No deeply nested file references (one level deep from SKILL.md)

- [ ] **Step 4: Skip commit. Mark task complete.**

---

## Task 5: Write plugin README

**Files:**
- Create: `plugin/README.md`

- [ ] **Step 1: Write `plugin/README.md`**

```markdown
# pinescript — Claude Code plugin

Pine Script v6 authoring assistant. Writes validated TradingView indicators and strategies via the [pinescript-mcp](https://github.com/paulieb89/pinescript-mcp) server.

## What it does

- **`pine`** — write Pine Script v6 indicators and strategies from natural-language descriptions. Auto-triggers on Pine asks; also responds to `/pine <description>`.
- **`pine-validate`** — validate a Pine snippet or function name against the v6 allowlist. Auto-triggers on validation asks; also responds to `/pine-validate <snippet>`.

## Install

```bash
claude --plugin-dir /path/to/pinescript-mcp/plugin
```

Or copy the `plugin/` directory contents into your project's `.claude-plugin/`.

## Prerequisites

The plugin connects to the hosted `pinescript-mcp` server at `https://pinescript-mcp.fly.dev/mcp` — no local setup required.

For offline or private use, replace `.mcp.json` with:

```json
{
  "mcpServers": {
    "pinescript": {
      "command": "uvx",
      "args": ["pinescript-mcp"]
    }
  }
}
```

Requires `uv` / `uvx` (https://docs.astral.sh/uv/).

## Example prompts

- *"Write me a Pine Script indicator that plots a 200 EMA with breakout signals."*
- *"`/pine` RSI divergence detector on 5-minute chart"*
- *"Is `ta.adx` a valid Pine v6 function?"*
- *"`/pine-validate` security(syminfo.tickerid, 'D', close)"*

## License

MIT. See repository root `LICENSE`.
```

- [ ] **Step 2: Verify markdown renders cleanly**

```bash
cat plugin/README.md | head -50
```

Look for: no broken code-fence escapes, no triple-nested backticks issues.

- [ ] **Step 3: Skip commit. Mark task complete.**

---

## Task 6: Local install and manual trigger tests

**Files:** (no modifications)

- [ ] **Step 1: Install plugin locally**

```bash
claude --plugin-dir /home/bch/dev/mcpfleet/pinescript-mcp/plugin
```

This opens a fresh Claude Code session with the plugin loaded.

- [ ] **Step 2: Verify MCP server connected**

In the session, run `/mcp`. Expected: `pinescript` server appears as `connected`.

- [ ] **Step 3: Run trigger test 1 — natural-language Pine ask**

Prompt: `Write me a Pine Script indicator that plots a 200 EMA with breakout signals.`

Expected: `pine` skill activates. Claude calls MCP tools (visible in tool log), validates function calls via `validate_function`, returns code with `//@version=6`.

Pass criteria:
- Code includes `//@version=6`
- Code includes `indicator(`
- All `ta.*` and `request.*` calls are valid Pine v6 (no hallucinations)
- Claude visibly called `validate_function` before emitting

- [ ] **Step 4: Run trigger test 2 — explicit `/pine`**

Prompt: `/pine RSI divergence on 5-minute chart`

Expected: same as Step 3, with the script targeting 5m via `timeframe.period` or explicit `request.security`.

- [ ] **Step 5: Run trigger test 3 — validation ask**

Prompt: `Is ta.adx a valid Pine v6 function?`

Expected: `pine-validate` skill activates. Claude calls `validate_function`, returns: invalid, suggested replacement `ta.dmi` (per the KNOWN_REPLACEMENTS map).

- [ ] **Step 6: Run trigger test 4 — `/pine-validate` snippet**

Prompt: `/pine-validate security(syminfo.tickerid, "D", close)`

Expected: `pine-validate` activates. Reports `security` as invalid, suggested replacement `request.security`.

- [ ] **Step 7: Run negative-trigger test**

Prompt: `Write me a momentum indicator in Python.`

Expected: `pine` skill does NOT activate (no mention of Pine, TradingView, or `/pine`).

If it does activate falsely: the description is over-broad; tighten the keywords and re-run Tasks 2 + 4.

- [ ] **Step 8: Record results in plan checklist. Mark task complete.**

---

## Task 7: Final review and handoff

**Files:** (no modifications)

- [ ] **Step 1: Full tree review**

```bash
cd /home/bch/dev/mcpfleet/pinescript-mcp
tree plugin/ -a
```

Expected tree:

```
plugin/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
├── README.md
└── skills/
    ├── pine/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── v6-checklist.md
    │   │   └── validation-workflow.md
    │   └── assets/
    │       └── rsi-divergence.pine
    └── pine-validate/
        ├── SKILL.md
        └── references/
            └── known-replacements.md
```

- [ ] **Step 2: Cross-check against the design spec**

Open the design spec and tick each section:

- [ ] Components match: `pine` + `pine-validate` ✓
- [ ] File structure matches: `plugin/` subdirectory layout ✓
- [ ] Manifest matches: `plugin/.claude-plugin/plugin.json` with the agreed fields ✓
- [ ] MCP wiring matches: hosted Fly.io endpoint ✓
- [ ] Trigger tests passed (Task 6) ✓
- [ ] Out-of-scope items NOT shipped: no `pine-reviewer` agent, no migration skill, no hooks ✓

- [ ] **Step 3: Surface the commit message to the user**

Suggest the following commit message but do NOT commit (per repo policy of never committing without explicit ask):

```
feat: add Claude Code plugin under plugin/

Adds a Claude Code plugin (pinescript) that wraps the existing
pinescript-mcp server with two skills:

- pine: writes validated Pine v6 indicators and strategies from
  natural-language descriptions; validates every function call
  via the MCP server before emitting code.
- pine-validate: validates Pine snippets and function names
  against the v6 allowlist, reporting invalid calls with
  suggested replacements.

Skills conform to the agentskills.io specification. Plugin wires
to the hosted Fly.io MCP endpoint; README documents the local
uvx fallback.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

- [ ] **Step 4: Hand back to user for commit + ship.**

---

## Self-review

**Spec coverage check:**

| Design spec section | Covered by task |
|---|---|
| Purpose, scope, killer flow | n/a (context) |
| Architecture: plugin + skills layers | Task 1 (plugin layer), Tasks 2+3 (skills layer) |
| Component: `pine` skill + supporting files | Task 2 |
| Component: `pine-validate` skill + supporting files | Task 3 |
| File structure | Task 1, Task 7 |
| `plugin.json` content | Task 1 Step 2 |
| `.mcp.json` content | Task 1 Step 3 |
| Spec frontmatter compliance | Task 4 |
| Validation & ship checklist | Tasks 4, 6 |
| README | Task 5 |
| Trigger accuracy risk | Task 6 Step 7 (negative test) |
| MCP availability risk | Task 5 (README documents local fallback) |
| Definition of done | Task 6 + Task 7 |

No gaps.

**Placeholder scan:** None — every step has concrete commands, file contents, or exact prompts.

**Type/name consistency:**
- Skill names `pine` and `pine-validate` consistent throughout ✓
- MCP server name `pinescript` consistent in `.mcp.json` and skill `compatibility` fields ✓
- File paths consistent (always `plugin/skills/<name>/...`) ✓

**Parallelism check:** Tasks 2 and 3 are explicitly independent — they touch disjoint directories and have no shared types or interfaces. Safe to dispatch in parallel.

---

## Execution

Plan complete and saved to `docs/superpowers/plans/2026-05-13-pinescript-plugin.md`.

Per the design and the user's "parallel subagents" instruction, execution will proceed inline in this session:

1. **Task 1** — scaffolding, done by me directly (small, no learning value in delegating).
2. **Tasks 2 + 3** — dispatched as two parallel `Agent` calls in a single message.
3. **Tasks 4–7** — done by me directly, verifying and integrating subagent output.

This matches the "Inline Execution" option from the writing-plans skill template, with a parallel-subagent burst for the heavy authoring work. Proceeding now.
