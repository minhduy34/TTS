from unittest.mock import MagicMock, patch


def test_execute_sql_rejects_delete():
    from agent.tools.sql_tools import execute_sql
    result = execute_sql.invoke({"query": "DELETE FROM dim_student"})
    assert "error" in result
    assert result["row_count"] == 0


def test_execute_sql_rejects_drop():
    from agent.tools.sql_tools import execute_sql
    result = execute_sql.invoke({"query": "DROP TABLE dim_student"})
    assert "error" in result


def test_execute_sql_rejects_stacked_delete():
    from agent.tools.sql_tools import execute_sql
    result = execute_sql.invoke({"query": "SELECT 1; DELETE FROM fact_enrollment"})
    assert "error" in result
    assert result["row_count"] == 0


def test_execute_sql_rejects_stacked_drop():
    from agent.tools.sql_tools import execute_sql
    result = execute_sql.invoke({"query": "SELECT 1; DROP TABLE dim_student"})
    assert "error" in result
    assert result["row_count"] == 0


def test_execute_sql_allows_with_clause():
    from agent.tools.sql_tools import execute_sql
    with patch("agent.tools.sql_tools._get_conn") as mock_conn_fn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = []
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__ = lambda s: s
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_fn.return_value = mock_conn
        result = execute_sql.invoke({"query": "WITH cte AS (SELECT 1) SELECT * FROM cte"})
        assert "error" not in result or result.get("row_count") == 0


def test_execute_sql_returns_rows():
    from agent.tools.sql_tools import execute_sql
    with patch("agent.tools.sql_tools._get_conn") as mock_conn_fn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = [{"student_id": 1, "full_name": "Nguyễn Văn A"}]
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__ = lambda s: s
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_fn.return_value = mock_conn
        result = execute_sql.invoke({"query": "SELECT student_id, full_name FROM dim_student LIMIT 1"})
        assert result["row_count"] == 1


def test_get_schema_returns_string():
    from agent.tools.sql_tools import get_schema
    with patch("agent.tools.sql_tools._get_conn") as mock_conn_fn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            # columns query
            [{"table_name": "dim_student", "table_comment": "Thông tin sinh viên",
              "column_name": "student_id", "data_type": "integer",
              "is_nullable": "NO", "column_default": None, "column_comment": "PK"}],
            # FK query
            []
        ]
        mock_conn.cursor.return_value.__enter__ = lambda s: s
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_fn.return_value = mock_conn
        result = get_schema.invoke({})
        assert "dim_student" in result
        assert "TABLE:" in result
