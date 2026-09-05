# ai/tests/test_main.py
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _parse_done_event(text: str) -> dict | None:
    """Parse SSE stream text and return the payload of the 'done' event."""
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_type = ""
        data = {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    pass
        if event_type == "done":
            return data
    return None


@pytest.fixture
def client():
    with patch("agent.deep_agent.get_deep_agent") as mock_getter, \
         patch("agent.llm.ChatGoogleGenerativeAI"), \
         patch("main.generate_summary", new=AsyncMock(return_value="")), \
         patch("main.generate_content", new=AsyncMock(return_value="")):
        mock_agent = MagicMock()
        async def empty_stream(*a, **kw):
            return
            yield  # makes it an async generator
        mock_agent.astream_events = empty_stream
        mock_getter.return_value = mock_agent
        from main import app
        with TestClient(app) as c:
            yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_stream_returns_200(client):
    with patch("main.get_deep_agent") as mock_getter, \
         patch("main.generate_summary", new=AsyncMock(return_value="")), \
         patch("main.generate_content", new=AsyncMock(return_value="")):
        mock_agent = MagicMock()
        async def fake_stream(*args, **kwargs):
            yield {
                "event": "on_chain_end",
                "data": {"output": {"messages": [MagicMock(content="Xin chào bạn! 👋")]}},
                "name": "",
            }
        mock_agent.astream_events = fake_stream
        mock_getter.return_value = mock_agent
        resp = client.get(
            "/chat/stream?session_id=test-1&message=xin+chao",
            headers={"Accept": "text/event-stream"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert "reasoning" in resp.text
        done_payload = _parse_done_event(resp.text)
        assert done_payload is not None, "No 'done' event found in SSE stream"
        for key in ("reply", "reasoning", "sql_query", "summary", "content"):
            assert key in done_payload, f"Missing key '{key}' in done payload"


def test_chat_stream_accepts_summary_and_returns_content(client):
    with patch("main.get_deep_agent") as mock_getter, \
         patch("main.generate_summary", new=AsyncMock(return_value="Student asked about GPA.")), \
         patch("main.generate_content", new=AsyncMock(return_value="## Kết quả\nGPA: 3.5")):
        mock_agent = MagicMock()
        async def fake_stream(*args, **kwargs):
            yield {
                "event": "on_chain_end",
                "data": {"output": {"messages": [MagicMock(content="GPA của bạn là 3.5")]}},
                "name": "",
            }
        mock_agent.astream_events = fake_stream
        mock_getter.return_value = mock_agent
        resp = client.get(
            "/chat/stream?session_id=test-2&message=gpa&summary=Student+asked+about+credits",
            headers={"Accept": "text/event-stream"},
        )
        assert resp.status_code == 200
        assert "summary" in resp.text
        assert "content" in resp.text
        done_payload = _parse_done_event(resp.text)
        assert done_payload is not None, "No 'done' event found in SSE stream"
        assert done_payload.get("summary") == "Student asked about GPA."
        assert done_payload.get("content") == "## Kết quả\nGPA: 3.5"
