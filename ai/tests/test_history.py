from langchain_core.messages import HumanMessage


def test_add_and_get():
    from agent.history import add_messages, clear_history, get_history
    clear_history("s1")
    add_messages("s1", [HumanMessage(content="xin chào")])
    history = get_history("s1")
    assert len(history) == 1
    assert history[0].content == "xin chào"


def test_multiple_sessions_isolated():
    from agent.history import add_messages, clear_history, get_history
    clear_history("sA")
    clear_history("sB")
    add_messages("sA", [HumanMessage(content="A")])
    add_messages("sB", [HumanMessage(content="B")])
    assert get_history("sA")[0].content == "A"
    assert get_history("sB")[0].content == "B"


def test_clear():
    from agent.history import add_messages, clear_history, get_history
    add_messages("s2", [HumanMessage(content="hi")])
    clear_history("s2")
    assert get_history("s2") == []


def test_max_history_trim():
    from agent.history import MAX_HISTORY, add_messages, clear_history, get_history
    clear_history("s3")
    msgs = [HumanMessage(content=f"msg{i}") for i in range(MAX_HISTORY + 4)]
    add_messages("s3", msgs)
    assert len(get_history("s3")) == MAX_HISTORY


def test_get_returns_copy():
    from agent.history import add_messages, clear_history, get_history
    clear_history("s4")
    add_messages("s4", [HumanMessage(content="x")])
    h = get_history("s4")
    h.append(HumanMessage(content="mutated"))
    assert len(get_history("s4")) == 1  # original unchanged
