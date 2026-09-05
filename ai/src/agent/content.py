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


def generate_content(reply: str, sql_query: str = "") -> str:
    if not reply:
        return ""

    prompt = f"Reply to format:\n{reply}"
    if sql_query:
        prompt += f"\n\nSQL query used:\n{sql_query}"

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=_CONTENT_PROMPT),
        HumanMessage(content=prompt),
    ])
    return response.content.strip()
