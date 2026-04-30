# AGENTS.md — pinescript-mcp

AI agent instructions for working in this repo. See `/home/bch/dev/ops/OPS.md` for credentials, fleet overview, and release tooling.

## Repo shape

`src/pinescript_mcp/server.py` is the entry point. Documentation data lives alongside it. Supports both stdio (uvx) and HTTP (Fly).

## Deploy

```bash
fly deploy --ha=false
```

Single instance, lhr region. App name: `pinescript-mcp`. Fly.io account: articat1066@gmail.com.

## Version bump

1. Update `version` in `pyproject.toml`
2. Update version string in the `smithery_server_card` route in `src/pinescript_mcp/server.py`
3. Commit, tag `vX.Y.Z`, push + push tags
4. GitHub Actions publishes to PyPI automatically on tag
5. `fly deploy --ha=false`
6. Cut a new Glama release

## Standard routes (must always be present)

- `/.well-known/mcp/server-card.json` — Smithery metadata
- `/.well-known/glama.json` — Glama maintainer claim
- `/health` — Fly health check

Verify after deploy:
```bash
curl https://pinescript-mcp.fly.dev/.well-known/mcp/server-card.json
curl https://pinescript-mcp.fly.dev/.well-known/glama.json
curl https://pinescript-mcp.fly.dev/health
```

## README badge order

```
PyPI → SafeSkill → Glama card → Smithery
```

## Do not

- Do not use `FASTMCP_PORT` — the server reads `PORT` env var only
- Do not set `internal_port` in fly.toml to anything other than 8080
- Do not commit API keys
