from collections import OrderedDict
from typing import List

from langchain_core.messages import BaseMessage

_store: OrderedDict[str, List[BaseMessage]] = OrderedDict()
MAX_HISTORY = 20
MAX_SESSIONS = 500


def get_history(session_id: str) -> List[BaseMessage]:
    return list(_store.get(session_id, []))


def add_messages(session_id: str, messages: List[BaseMessage]) -> None:
    if session_id not in _store:
        if len(_store) >= MAX_SESSIONS:
            _store.popitem(last=False)  # FIFO eviction of oldest session
        _store[session_id] = []
    _store[session_id].extend(messages)
    if len(_store[session_id]) > MAX_HISTORY:
        _store[session_id] = _store[session_id][-MAX_HISTORY:]


def clear_history(session_id: str) -> None:
    _store.pop(session_id, None)
