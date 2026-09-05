import os
import sys
from unittest.mock import MagicMock

import pytest

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set dummy env vars before any module imports them
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

@pytest.fixture
def mock_db_conn(mocker):
    """Mock psycopg2.connect for unit tests that don't hit a real DB."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = lambda s: s
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor
    mocker.patch("psycopg2.connect", return_value=mock_conn)
    return mock_conn, mock_cursor
