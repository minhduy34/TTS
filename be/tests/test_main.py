from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_stream_proxies_to_ai(client):
    async def fake_aiter():
        yield b"event: status\ndata: {\"message\": \"thinking\"}\n\n"
        yield b"event: done\ndata: {\"reply\": \"ok\", \"summary\": \"\", \"content\": \"\"}\n\n"

    mock_response = MagicMock()
    mock_response.aiter_bytes = fake_aiter
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_client_instance = MagicMock()
    mock_client_instance.stream = MagicMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("main.httpx.AsyncClient", return_value=mock_client_instance):
        resp = client.get(
            "/chat/stream?session_id=test-1&message=hello",
            headers={"Accept": "text/event-stream"},
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
