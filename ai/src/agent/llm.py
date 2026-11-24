import asyncio
import os
import time

from langchain_google_genai import ChatGoogleGenerativeAI

_FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]


class ResilientChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """Subclass of ChatGoogleGenerativeAI that automatically retries and falls back
    across Gemini Flash models when transient 503 UNAVAILABLE or 429 errors occur.
    """

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        orig_model = self.model
        try:
            for attempt, m_name in enumerate(_FALLBACK_MODELS):
                self.model = m_name
                try:
                    return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
                except Exception as e:
                    msg = str(e)
                    if attempt < len(_FALLBACK_MODELS) - 1 and (
                        "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg
                    ):
                        time.sleep(1.5)
                        continue
                    raise
        finally:
            self.model = orig_model

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        orig_model = self.model
        try:
            for attempt, m_name in enumerate(_FALLBACK_MODELS):
                self.model = m_name
                try:
                    return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
                except Exception as e:
                    msg = str(e)
                    if attempt < len(_FALLBACK_MODELS) - 1 and (
                        "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg
                    ):
                        await asyncio.sleep(1.5)
                        continue
                    raise
        finally:
            self.model = orig_model

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        orig_model = self.model
        try:
            for attempt, m_name in enumerate(_FALLBACK_MODELS):
                self.model = m_name
                try:
                    for chunk in super()._stream(messages, stop=stop, run_manager=run_manager, **kwargs):
                        yield chunk
                    return
                except Exception as e:
                    msg = str(e)
                    if attempt < len(_FALLBACK_MODELS) - 1 and (
                        "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg
                    ):
                        time.sleep(1.5)
                        continue
                    raise
        finally:
            self.model = orig_model

    async def _astream(self, messages, stop=None, run_manager=None, **kwargs):
        orig_model = self.model
        try:
            for attempt, m_name in enumerate(_FALLBACK_MODELS):
                self.model = m_name
                try:
                    async for chunk in super()._astream(messages, stop=stop, run_manager=run_manager, **kwargs):
                        yield chunk
                    return
                except Exception as e:
                    msg = str(e)
                    if attempt < len(_FALLBACK_MODELS) - 1 and (
                        "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg
                    ):
                        await asyncio.sleep(1.5)
                        continue
                    raise
        finally:
            self.model = orig_model


def get_llm(temperature: float = 0) -> ChatGoogleGenerativeAI:
    return ResilientChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=temperature,
    )
