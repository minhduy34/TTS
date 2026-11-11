from contextlib import contextmanager
import os

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from langchain_core.tools import tool

COLUMNS_QUERY = """
    SELECT
        t.table_name,
        obj_description(pc.oid, 'pg_class') AS table_comment,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        col_description(pc.oid, c.ordinal_position) AS column_comment
    FROM information_schema.tables t
    JOIN information_schema.columns c
        ON t.table_name = c.table_name AND t.table_schema = c.table_schema
    JOIN pg_class pc
        ON pc.relname = t.table_name
        AND pc.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.ordinal_position
"""

FK_QUERY = """
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name  AS references_table,
        ccu.column_name AS references_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
"""


STATEMENT_SEPARATOR = ";"
MAX_RESULT_ROWS = 200

_pool: ThreadedConnectionPool | None = None
_SCHEMA_CACHE: str | None = None


def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        db_url = os.getenv("DATABASE_URL")
        _pool = ThreadedConnectionPool(minconn=1, maxconn=5, dsn=db_url)
    return _pool


@contextmanager
def get_db_connection():
    """Acquire a connection from the pool and return it safely."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        pool.putconn(conn)


@tool
def get_schema() -> str:
    """Read the full database schema including table descriptions, column descriptions,
    data types, nullable flags, and foreign key relationships.
    ALWAYS call this first before writing any SQL query."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE

    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(COLUMNS_QUERY)
        columns = cur.fetchall()

        cur.execute(FK_QUERY)
        fks = cur.fetchall()

    fk_map: dict[tuple[str, str], str] = {
        (r["table_name"], r["column_name"]): f"→ {r['references_table']}.{r['references_column']}"
        for r in fks
    }

    schema_text = "=== DATABASE SCHEMA ===\n\n"
    current_table: str | None = None
    for i, row in enumerate(columns):
        if row["table_name"] != current_table:
            current_table = row["table_name"]
            schema_text += f"TABLE: {current_table}\n"
            schema_text += f"Description: {row['table_comment'] or '(no description)'}\n"
            schema_text += "Columns:\n"
        fk = fk_map.get((row["table_name"], row["column_name"]), "")
        nullable = "nullable" if row["is_nullable"] == "YES" else "not null"
        comment = row["column_comment"] or ""
        schema_text += f"  - {row['column_name']} ({row['data_type']}, {nullable})"
        if fk:
            schema_text += f" [FK: {fk}]"
        if comment:
            schema_text += f" -- {comment}"
        schema_text += "\n"
        is_last_row = i == len(columns) - 1
        is_last_in_table = is_last_row or columns[i + 1]["table_name"] != current_table
        if is_last_in_table:
            schema_text += "\n"
    _SCHEMA_CACHE = schema_text
    return schema_text


@tool
def execute_sql(query: str) -> dict:
    """Execute a SELECT SQL query against the student management database.
    Only SELECT and WITH...SELECT queries are permitted.
    Args:
        query: A valid PostgreSQL SELECT statement
    Returns:
        {"rows": [...], "row_count": N, "truncated": bool} on success
        {"error": "...", "rows": [], "row_count": 0} on failure or disallowed query
    """
    if STATEMENT_SEPARATOR in query.strip().rstrip(STATEMENT_SEPARATOR):
        return {"error": "Only a single SELECT statement is allowed.", "rows": [], "row_count": 0}

    normalized = query.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return {
            "error": "Only SELECT queries are allowed. INSERT/UPDATE/DELETE/DROP are forbidden.",
            "rows": [],
            "row_count": 0,
        }

    try:
        with get_db_connection() as conn:
            conn.set_session(readonly=True, autocommit=True)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SET LOCAL statement_timeout = '10s'")
            cur.execute(query)
            rows = [dict(r) for r in cur.fetchmany(MAX_RESULT_ROWS)]
            truncated = cur.fetchone() is not None
            return {"rows": rows, "row_count": len(rows), "truncated": truncated}
    except psycopg2.Error as e:
        return {"error": str(e), "rows": [], "row_count": 0}
