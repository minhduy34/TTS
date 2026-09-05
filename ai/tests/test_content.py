from unittest.mock import MagicMock, patch


def test_generate_content_returns_markdown_string():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content="## Kết quả\n| Môn | Điểm |\n|-----|------|\n| Toán | 8.5 |"
    )
    with patch("agent.content.get_llm", return_value=mock_llm):
        from agent.content import generate_content
        result = generate_content("Điểm Toán của bạn là 8.5")
        assert isinstance(result, str)
        assert len(result) > 0
        mock_llm.invoke.assert_called_once()


def test_generate_content_empty_reply_returns_empty():
    from agent.content import generate_content
    result = generate_content("")
    assert result == ""
