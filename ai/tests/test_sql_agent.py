from unittest.mock import patch, MagicMock


def test_sql_agent_creation():
    with patch("agent.llm.ChatGoogleGenerativeAI") as mock_llm:
        mock_llm.return_value = MagicMock()
        from agent.subagents.sql_query_agent import get_sql_agent
        agent = get_sql_agent()
        assert agent is not None


def test_sql_agent_singleton():
    with patch("agent.llm.ChatGoogleGenerativeAI") as mock_llm:
        mock_llm.return_value = MagicMock()
        from agent.subagents.sql_query_agent import get_sql_agent
        a1 = get_sql_agent()
        a2 = get_sql_agent()
        assert a1 is a2
