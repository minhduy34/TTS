from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import get_llm

_CONTENT_PROMPT = (
    "You are formatting an AI assistant's reply into a structured Markdown document in Vietnamese. "
    "Rules:\n"
    "- Start with a short summary (1-2 sentences) of what was asked and answered\n"
    "- If the reply contains tabular data (scores, credits, courses, scholarships), "
    "format it as a Markdown table\n"
    "- Use Vietnamese headers and text\n"
    "- Be concise — no extra explanation beyond what the reply contains\n"
    "- If the reply contains no data worth tabling, just return the summary paragraph"
)


async def generate_content(reply: str, sql_query: str = "") -> str:
    if not reply:
        return ""

    # Skip extra LLM formatting call for simple conversational replies without SQL data
    if not sql_query and not any(kw in reply.lower() for kw in ["|", "bảng", "học kỳ", "sinh viên", "học bổng", "tín chỉ"]):
        return ""

    prompt = f"Reply to format:\n{reply}"
    if sql_query:
        prompt += f"\n\nSQL query used:\n{sql_query}"

    llm = get_llm()
    response = await llm.ainvoke([
        SystemMessage(content=_CONTENT_PROMPT),
        HumanMessage(content=prompt),
    ])
    content = response.content
    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return content.strip()
