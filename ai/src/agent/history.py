from typing import Dict, List

from langchain_core.messages import BaseMessage

_store: Dict[str, List[BaseMessage]] = {}
MAX_HISTORY = 20


def get_history(session_id: str) -> List[BaseMessage]:
    return list(_store.get(session_id, []))


def add_messages(session_id: str, messages: List[BaseMessage]) -> None:
    if session_id not in _store:
        _store[session_id] = []
    _store[session_id].extend(messages)
    if len(_store[session_id]) > MAX_HISTORY:
        _store[session_id] = _store[session_id][-MAX_HISTORY:]


def clear_history(session_id: str) -> None:
    _store.pop(session_id, None)
