# ai/src/main.py
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage

from agent.deep_agent import get_deep_agent
from agent.history import add_messages, get_history

app = FastAPI(title="Student AI Assistant")

_TOOL_LABELS = {
    "resolve_time_range": "📅 Đang xác định khoảng thời gian...",
    "call_sql_agent": "📊 Đang hỏi SQL Agent...",
    "out_of_scope_reply": "🚫 Nhận diện câu hỏi ngoài phạm vi...",
    "get_schema": "📋 SQL Agent đang đọc schema database...",
    "execute_sql": "⚡ Đang thực thi SQL query...",
}


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/chat/stream")
async def chat_stream(session_id: str, message: str) -> StreamingResponse:
    async def generate():
        agent = get_deep_agent()
        history = get_history(session_id)
        messages = history + [HumanMessage(content=message)]
        final_reply = ""

        try:
            yield _sse("status", {"message": "🧠 Deep Agent đang phân tích câu hỏi..."})

            async for event in agent.astream_events(
                {"messages": messages},
                config={"recursion_limit": 25},
                version="v2",
            ):
                kind = event.get("event", "")

                if kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    label = _TOOL_LABELS.get(tool_name, f"🔧 Gọi: {tool_name}...")
                    yield _sse("status", {"message": label})

                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict) and "messages" in output:
                        msgs = output["messages"]
                        if msgs and hasattr(msgs[-1], "content") and msgs[-1].content:
                            final_reply = msgs[-1].content

            add_messages(session_id, [
                HumanMessage(content=message),
                AIMessage(content=final_reply),
            ])
            yield _sse("done", {"reply": final_reply})

        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Mount frontend LAST — catch-all route
_frontend_dir = Path(__file__).parent / "frontend"
app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="static")
