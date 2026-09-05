# ai/src/agent/tools/agent_tools.py
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from agent.subagents.sql_query_agent import get_sql_agent

_DATE_RANGE_SUFFIX = "\nKhoảng thời gian cần lọc: từ {start_date} đến {end_date} ({label})"


@tool
async def call_sql_agent(
    question: str,
    date_range: Optional[dict] = None,
    config: Optional[RunnableConfig] = None,
) -> dict:
    """Delegate a data question to the SQL Query Agent which reads the DB schema,
    reasons about which tables/columns to query, generates SQL, executes it, and
    returns the result with reasoning.

    Args:
        question: Natural language question about student data
        date_range: Optional {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": str}
                    from resolve_time_range — appended to question so SQL agent filters by date
    """
    full_question = question
    if date_range:
        full_question += _DATE_RANGE_SUFFIX.format(
            start_date=date_range["start_date"],
            end_date=date_range["end_date"],
            label=date_range.get("label", ""),
        )

    agent = get_sql_agent()
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": full_question}]},
        config=config,
    )
    messages = result["messages"]
    last_message = messages[-1]

    # Extract SQL query from most recent execute_sql tool call
    sql_query = ""
    for msg in reversed(messages):
        for call in getattr(msg, "tool_calls", []) or []:
            if call["name"] == "execute_sql":
                sql_query = call["args"].get("query", "")
                break
        if sql_query:
            break

    # Reasoning = content from intermediate AI messages (not the final one)
    from langchain_core.messages import AIMessage as _AIMsg
    reasoning_parts = [
        m.content
        for m in messages[1:-1]
        if isinstance(m, _AIMsg) and m.content and isinstance(m.content, str)
    ]
    reasoning = "\n\n".join(reasoning_parts)

    return {"answer": last_message.content, "reasoning": reasoning, "sql_query": sql_query}


@tool
def out_of_scope_reply(topic: str) -> str:
    """Signal that the user's question is outside the student management domain.
    Call this when the user asks about anything unrelated to courses, grades,
    credits, or scholarships. The agent will then reply in its own words.

    Args:
        topic: Brief description of what the user asked about (e.g., 'thời tiết', 'bóng đá')
    """
    return f"out_of_scope: '{topic}'"
