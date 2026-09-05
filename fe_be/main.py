# be/main.py
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import httpx
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:8001")

MAX_MESSAGE_LENGTH = 2000
MAX_SESSION_ID_LENGTH = 64

app = FastAPI(title="Student AI Backend")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/chat/stream")
async def chat_stream(
    session_id: str = Query(max_length=MAX_SESSION_ID_LENGTH, pattern=r"^[A-Za-z0-9_-]+$"),
    message: str = Query(max_length=MAX_MESSAGE_LENGTH, min_length=1),
    summary: str = Query(default="", max_length=2000),
) -> StreamingResponse:
    params = {"session_id": session_id, "message": message, "summary": summary}

    async def proxy():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "GET",
                    f"{AI_BASE_URL}/chat/stream",
                    params=params,
                    timeout=120.0,
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as exc:
            import json
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n".encode()

    return StreamingResponse(
        proxy(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Mount frontend LAST — catch-all route
_frontend_dir = Path(__file__).parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
