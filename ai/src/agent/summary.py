from langchain_core.messages import HumanMessage, SystemMessage

from agent.history import get_history
from agent.llm import get_llm

_SUMMARY_PROMPT = (
    "Summarize the following conversation between a student and a university AI assistant "
    "in 2-3 sentences in English. "
    "Focus on: what the student asked, what data was retrieved, and the key answer given. "
    "Be concise and factual."
)


async def generate_summary(session_id: str) -> str:
    history = get_history(session_id)
    if not history or len(history) < 4:
        return ""

    def _text(msg) -> str:
        c = msg.content
        if isinstance(c, list):
            return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in c)
        return str(c)

    conversation = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {_text(m)}"
        for m in history[-6:]
    )

    try:
        llm = get_llm()
        response = await llm.ainvoke([
            SystemMessage(content=_SUMMARY_PROMPT),
            HumanMessage(content=conversation),
        ])
        content = response.content
        if isinstance(content, list):
            content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
        return content.strip()[:1800]
    except Exception:
        return ""
