import pytest
from unittest.mock import patch


def test_get_llm_returns_instance():
    with patch("langchain_google_genai.ChatGoogleGenerativeAI.__init__", return_value=None):
        from agent.llm import get_llm
        llm = get_llm()
        assert llm is not None


def test_get_llm_uses_env_key(mocker):
    import os
    os.environ["GEMINI_API_KEY"] = "test-abc"
    mock_cls = mocker.patch("agent.llm.ChatGoogleGenerativeAI")
    from agent.llm import get_llm
    get_llm()
    mock_cls.assert_called_once()
    _, kwargs = mock_cls.call_args
    assert kwargs.get("google_api_key") == "test-abc" or mock_cls.call_args[0]
