import logging
from datetime import date
from unittest.mock import patch


def test_get_logger_returns_logger(tmp_path):
    with patch("utils.logger.LOGS_DIR", tmp_path):
        from utils.logger import get_logger
        logger = get_logger("session-abc")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "session-abc"


def test_get_logger_creates_log_file(tmp_path):
    with patch("utils.logger.LOGS_DIR", tmp_path):
        from utils.logger import get_logger
        logger = get_logger("session-xyz")
        logger.info("test message")
        today = date.today().isoformat()
        log_file = tmp_path / today / "session-xyz.log"
        assert log_file.exists()
        assert "test message" in log_file.read_text(encoding="utf-8")


def test_get_logger_same_session_returns_same_logger(tmp_path):
    with patch("utils.logger.LOGS_DIR", tmp_path):
        from utils.logger import get_logger
        a = get_logger("same-session")
        b = get_logger("same-session")
        assert a is b
