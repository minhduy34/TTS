from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from agent.llm import get_llm
from agent.tools.sql_tools import execute_sql, get_schema

_SQL_SYSTEM_PROMPT = """You are a SQL Query Agent specializing in querying a student management database.

MANDATORY PROCEDURE — follow in order:

Step 1 — Read schema: Call get_schema() first. Read every table and column description carefully.

Step 2 — Analyze and reason (write out explicitly):
  - What information does the question require?
  - Which columns to SELECT? Why those columns and not others?
  - Which tables to JOIN? What are the join conditions (which foreign keys)?
  - What WHERE filters apply?
  - Is GROUP BY / ORDER BY / LIMIT needed? Why?

Step 3 — Write the SQL and call execute_sql().

Step 4 — Validate the result:
  - On error: analyze the error, fix the query, retry (max 3 times).
  - On empty result: revisit WHERE conditions, try a simpler query.

Step 5 — Return a response that includes:
  1. The concrete data result (numbers, lists, etc.)
  2. Reasoning: why those tables/columns were chosen
  3. The executed SQL query (in a code block)

IMPORTANT: Only SELECT queries are permitted. Refuse any INSERT/UPDATE/DELETE/DROP."""

_agent = None


def get_sql_agent() -> CompiledStateGraph:
    global _agent
    if _agent is None:
        _agent = create_react_agent(
            model=get_llm(),
            tools=[get_schema, execute_sql],
            prompt=_SQL_SYSTEM_PROMPT,
        )
    return _agent
