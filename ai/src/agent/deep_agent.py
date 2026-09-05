from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from agent.llm import get_llm
from agent.prompt.deep_agent import SYSTEM_PROMPT
from agent.tool_registry import DEEP_AGENT_TOOLS

_deep_agent = None


def get_deep_agent() -> CompiledStateGraph:
    global _deep_agent
    if _deep_agent is None:
        _deep_agent = create_react_agent(
            model=get_llm(),
            tools=DEEP_AGENT_TOOLS,
            prompt=SYSTEM_PROMPT,
        )
    return _deep_agent
