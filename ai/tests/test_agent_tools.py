# ai/tests/test_agent_tools.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


def test_out_of_scope_reply_contains_topic():
    from agent.tools.agent_tools import out_of_scope_reply
    result = out_of_scope_reply.invoke({"topic": "thời tiết"})
    assert "thời tiết" in result or "mình" in result


def test_out_of_scope_reply_returns_string():
    from agent.tools.agent_tools import out_of_scope_reply
    result = out_of_scope_reply.invoke({"topic": "bóng đá"})
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_call_sql_agent_appends_date_range():
    with patch("agent.tools.agent_tools.get_sql_agent") as mock_getter:
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [MagicMock(content="Kết quả: 10 sinh viên")]
        }
        mock_getter.return_value = mock_agent
        from agent.tools.agent_tools import call_sql_agent
        result = await call_sql_agent.ainvoke({
            "question": "Bao nhiêu sinh viên?",
            "date_range": {"start_date": "2026-08-01", "end_date": "2026-08-31", "label": "Tháng 8"}
        })
        assert "answer" in result
        call_args = mock_agent.ainvoke.call_args
        messages = call_args[0][0]["messages"]
        assert "2026-08-01" in messages[0]["content"]


def test_tool_registry_has_three_tools():
    from agent.tool_registry import DEEP_AGENT_TOOLS
    assert len(DEEP_AGENT_TOOLS) == 3
    names = [t.name for t in DEEP_AGENT_TOOLS]
    assert "resolve_time_range" in names
    assert "call_sql_agent" in names
    assert "out_of_scope_reply" in names
