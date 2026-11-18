"""/mcp is stateless POST-only: GET is refused with FastMCP's native 405 (#8).

_HttpGuard answered GET /mcp with 200 and held the stream open with nothing sent.
Clients (mostly Claude Code) open that optional stream and keep it, so each held
GET occupied a connection slot (prod ran at 26-35 connections around the clock).
govuk-mcp 0.3.2 removed the same shim and went from 40-50 held connections to 0.
"""

from starlette.testclient import TestClient

from pinescript_mcp import server

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}},
}


def test_get_mcp_is_refused_with_405_and_allows_post():
    with TestClient(server.create_app()) as c:
        resp = c.get("/mcp", headers={"Accept": "text/event-stream"})

    assert resp.status_code == 405
    assert "POST" in resp.headers["allow"]


def test_post_initialize_succeeds_without_any_get_stream():
    with TestClient(server.create_app()) as c:
        resp = c.post(
            "/mcp", json=INIT,
            headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"},
        )

    assert resp.status_code == 200
    assert "serverInfo" in resp.text


def test_accept_normaliser_still_admits_a_bare_accept_header():
    with TestClient(server.create_app()) as c:
        resp = c.post("/mcp", json=INIT, headers={"Accept": "application/json", "Content-Type": "application/json"})

    assert resp.status_code == 200
