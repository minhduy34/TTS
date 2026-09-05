# ai/src/agent/tool_registry.py
from agent.tools.agent_tools import call_sql_agent, out_of_scope_reply
from agent.tools.datetime_tools import resolve_time_range

DEEP_AGENT_TOOLS = [resolve_time_range, call_sql_agent, out_of_scope_reply]
