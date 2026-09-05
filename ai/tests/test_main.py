# ai/tests/test_main.py
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


async def _aiter(items):
    for item in items:
        yield item


@pytest.fixture
def client():
    with patch("agent.deep_agent.get_deep_agent") as mock_getter, \
         patch("agent.llm.ChatGoogleGenerativeAI"):
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
    with patch("main.get_deep_agent") as mock_getter:
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
