import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage


@pytest.mark.asyncio
async def test_generate_summary_returns_empty_when_no_history():
    with patch("agent.history._store", {}):
        from agent.summary import generate_summary
        result = await generate_summary("no-history-session")
        assert result == ""


@pytest.mark.asyncio
async def test_generate_summary_calls_llm_and_returns_string():
    from agent.history import _store
    _store["test-session-sum"] = [
        HumanMessage(content="What is my GPA?"),
        AIMessage(content="Your GPA is 3.5."),
    ]
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Student asked about GPA. GPA is 3.5."))
    with patch("agent.summary.get_llm", return_value=mock_llm):
        from agent.summary import generate_summary
        result = await generate_summary("test-session-sum")
        assert isinstance(result, str)
        assert len(result) > 0
        mock_llm.ainvoke.assert_called_once()
    _store.pop("test-session-sum", None)
