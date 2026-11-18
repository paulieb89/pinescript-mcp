---
status: landed
repo: pinescript-mcp
date: 2026-11-18
supersedes: none
sessions: one Claude Code session, 2026-11-18 (fleet-wide _HttpGuard removal)
---

# Handoff: GET /mcp returns 405 (0.7.7)

## Purpose and scope

Stop held-open `GET /mcp` streams from tying up connection slots, the same fix
govuk-mcp shipped in 0.3.2. Shape A of the fleet handoff template
([uk-due-diligence-mcp/docs/plans/TEMPLATE-handoff.md](https://github.com/paulieb89/uk-due-diligence-mcp/blob/main/docs/plans/TEMPLATE-handoff.md)).
Changes: [CHANGELOG](../../CHANGELOG.MD) v0.7.6 → v0.7.7, PRs #9 (fix) and #10 (release).

## What shipped

- **0.7.7, tag `v0.7.7` → `f1edba9`**, released 2026-11-18 ~19:26 UTC via `release.yml`.
  Rollback image recorded before release: Fly v54,
  `registry.fly.io/pinescript-mcp:deployment-01KV5PPW0BXD889FHC1Q2796B0`.
- `_HttpGuard` removed; app construction moved into `create_app()`;
  `tests/test_mcp_get_405.py` added. With the guard in place, the GET test hangs on
  the held stream. 38 tests pass.
- Checks:
  - prod `GET /mcp` → 405 in 0.09 s;
  - `/health`, PyPI and Fly v55 all show 0.7.7;
  - 12 tools listed, and `search_docs` works;
  - `fly_app_concurrency`: 26–35 around the clock and 25 just before release;
    no data after release, while serving 46 responses in 10 minutes;
  - three held test connections read exactly 3, so no data means zero.

## Root cause

`_HttpGuard` answered `GET /mcp` with 200 and held an empty event stream open.
Clients (mostly Claude Code, across the fleet) open that optional stream and
keep it, so each one held a connection slot. Same cause as
[govuk-mcp #7](https://github.com/paulieb89/govuk-mcp/issues/7). It was not
uk-business-mcp's proxy.

## Gotchas

- `.bumpversion.toml` has `commit = true, tag = true`. For a release-prep PR, run
  `uvx bump-my-version bump patch --no-commit --no-tag` and tag the merge commit
  afterwards.
- Fly's `fly_app_concurrency` omits the series at zero and keeps the last
  non-zero value for ~5 min.
- Pre-existing lint: unused `fastmcp.Context` import in `server.py`.

## Open issues

None in this repo. Fleet: [mcpfleet-obs #11](https://github.com/uk-agents/mcpfleet-obs/issues/11)
(move the transport layer into the shared package).

## Recommended next step

pinescript is on FastMCP 3.3.0 / mcp 1.26.0. Fold it into the fleet's FastMCP
4.1.8 move (uk-due-diligence-mcp #49, uk-legal-mcp #116, govuk-mcp #11), or adopt
the shared transport layer from mcpfleet-obs #11 once it exists.

## Re-verify

```bash
curl -sS -m 10 -o /dev/null -w '%{http_code}\n' -H 'Accept: text/event-stream' https://pinescript-mcp.fly.dev/mcp   # 405
curl -s https://pinescript-mcp.fly.dev/health
# Fly Prometheus (Authorization: FlyV1 <fly auth token>): fly_app_concurrency{app="pinescript-mcp"}
```
