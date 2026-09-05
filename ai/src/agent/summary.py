from langchain_core.messages import HumanMessage, SystemMessage

from agent.history import get_history
from agent.llm import get_llm

_SUMMARY_PROMPT = (
    "Summarize the following conversation between a student and a university AI assistant "
    "in 2-3 sentences in English. "
    "Focus on: what the student asked, what data was retrieved, and the key answer given. "
    "Be concise and factual."
)


def generate_summary(session_id: str) -> str:
    history = get_history(session_id)
    if not history:
        return ""

    conversation = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
        for m in history[-6:]  # last 3 turns
    )

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=_SUMMARY_PROMPT),
        HumanMessage(content=conversation),
    ])
    return response.content.strip()
