import calendar
import os
import re
from datetime import date, timedelta

import psycopg2
import psycopg2.extras
from langchain_core.tools import tool

# ── Constants ──────────────────────────────────────────────────────────────────
MONTHS_PER_QUARTER = 3
QUARTERS_PER_YEAR = 4
DAYS_PER_WEEK = 7
YEAR_START_MONTH = 1
YEAR_END_MONTH = 12
YEAR_START_DAY = 1
YEAR_END_DAY = 31


def _get_conn() -> psycopg2.extensions.connection:
    """Open a new database connection using DATABASE_URL."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def _last_day(year: int, month: int) -> int:
    """Return the last calendar day of the given month."""
    return calendar.monthrange(year, month)[1]


def _quarter_of_month(month: int) -> int:
    """Return the quarter number (1–4) for a given month."""
    return (month - 1) // MONTHS_PER_QUARTER + 1


def _quarter_range(year: int, quarter: int) -> tuple[date, date]:
    """Return (start_date, end_date) for the given quarter."""
    start_month = (quarter - 1) * MONTHS_PER_QUARTER + 1
    end_month = start_month + MONTHS_PER_QUARTER - 1
    start = date(year, start_month, 1)
    end = date(year, end_month, _last_day(year, end_month))
    return start, end


def _resolve_month(today: date, expr: str) -> dict[str, str] | None:
    """Parse tháng expressions; return dict or None if not matched."""
    if expr in ("tháng này", "tháng nay"):
        start = today.replace(day=1)
        end = today.replace(day=_last_day(today.year, today.month))
        return {
            "start_date": str(start),
            "end_date": str(end),
            "label": f"Tháng {today.month}/{today.year}",
        }

    if expr == "tháng trước":
        last_of_prev = today.replace(day=1) - timedelta(days=1)
        start = last_of_prev.replace(day=1)
        return {
            "start_date": str(start),
            "end_date": str(last_of_prev),
            "label": f"Tháng {last_of_prev.month}/{last_of_prev.year}",
        }

    m = re.fullmatch(r"tháng\s+(\d{1,2})", expr)
    if m:
        month = int(m.group(1))
        if 1 <= month <= 12:
            year = today.year if month <= today.month else today.year - 1
            start = date(year, month, 1)
            end = date(year, month, _last_day(year, month))
            return {
                "start_date": str(start),
                "end_date": str(end),
                "label": f"Tháng {month}/{year}",
            }

    return None


def _resolve_quarter(today: date, expr: str) -> dict[str, str] | None:
    """Parse quý expressions; return dict or None if not matched."""
    current_quarter = _quarter_of_month(today.month)

    if expr in ("quý này", "quý nay"):
        start, end = _quarter_range(today.year, current_quarter)
        return {
            "start_date": str(start),
            "end_date": str(end),
            "label": f"Quý {current_quarter}/{today.year}",
        }

    if expr == "quý trước":
        quarter_start_month = (current_quarter - 1) * MONTHS_PER_QUARTER + 1
        last_of_prev = date(today.year, quarter_start_month, 1) - timedelta(days=1)
        prev_quarter = _quarter_of_month(last_of_prev.month)
        start, end = _quarter_range(last_of_prev.year, prev_quarter)
        return {
            "start_date": str(start),
            "end_date": str(end),
            "label": f"Quý {prev_quarter}/{last_of_prev.year}",
        }

    m = re.fullmatch(r"(\d+)\s+quý trước", expr)
    if m:
        n = int(m.group(1))
        total_months_back = n * MONTHS_PER_QUARTER
        pivot_month = today.month - total_months_back
        pivot_year = today.year
        while pivot_month <= 0:
            pivot_month += 12
            pivot_year -= 1
        target_quarter = _quarter_of_month(pivot_month)
        start, end = _quarter_range(pivot_year, target_quarter)
        return {
            "start_date": str(start),
            "end_date": str(end),
            "label": f"Quý {target_quarter}/{pivot_year}",
        }

    return None


def _resolve_year(today: date, expr: str) -> dict[str, str] | None:
    """Parse năm expressions; return dict or None if not matched."""
    if expr in ("năm nay", "năm này"):
        return {
            "start_date": f"{today.year}-01-01",
            "end_date": f"{today.year}-12-31",
            "label": f"Năm {today.year}",
        }

    if expr == "năm ngoái":
        prev_year = today.year - 1
        return {
            "start_date": f"{prev_year}-01-01",
            "end_date": f"{prev_year}-12-31",
            "label": f"Năm {prev_year}",
        }

    return None


def _resolve_week(today: date, expr: str) -> dict[str, str] | None:
    """Parse tuần expressions; return dict or None if not matched."""
    if expr in ("tuần này", "tuần nay"):
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=DAYS_PER_WEEK - 1)
        return {
            "start_date": str(monday),
            "end_date": str(sunday),
            "label": "Tuần này",
        }

    if expr == "tuần trước":
        last_monday = today - timedelta(days=today.weekday() + DAYS_PER_WEEK)
        last_sunday = last_monday + timedelta(days=DAYS_PER_WEEK - 1)
        return {
            "start_date": str(last_monday),
            "end_date": str(last_sunday),
            "label": "Tuần trước",
        }

    return None


def _resolve_semester(today: date, expr: str) -> dict[str, str] | None:
    """Query dim_semester table for học kỳ expressions.

    Returns dict on success, None if no matching row found.
    Raises psycopg2.Error on unexpected database errors.
    """
    if "học kỳ" not in expr:
        return None

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if any(w in expr for w in ("này", "nay", "hiện tại")):
                cur.execute(
                    "SELECT * FROM dim_semester WHERE is_current = TRUE LIMIT 1"
                )
                row = cur.fetchone()
            elif "trước" in expr:
                cur.execute(
                    "SELECT start_date FROM dim_semester WHERE is_current = TRUE LIMIT 1"
                )
                current = cur.fetchone()
                if not current:
                    return None
                cur.execute(
                    "SELECT * FROM dim_semester"
                    " WHERE end_date < %s ORDER BY end_date DESC LIMIT 1",
                    (current["start_date"],),
                )
                row = cur.fetchone()
            else:
                return None
    except psycopg2.Error:
        raise
    finally:
        conn.close()

    if not row:
        return None
    return {
        "start_date": str(row["start_date"]),
        "end_date": str(row["end_date"]),
        "label": row["semester_name"],
    }


@tool
def resolve_time_range(expression: str) -> dict[str, str]:
    """Convert a Vietnamese relative time expression into an absolute date range.

    Supported expressions:
    - Monthly: 'tháng này', 'tháng trước', 'tháng N' (N = 1–12)
    - Quarterly: 'quý này', 'quý trước', 'N quý trước'
    - Yearly: 'năm nay', 'năm ngoái'
    - Weekly: 'tuần này', 'tuần trước'
    - Semester: 'học kỳ này', 'học kỳ trước' (requires DB with dim_semester)

    Returns:
        {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": str}
        Falls back to the current month if the expression is not recognised.
    """
    today = date.today()
    expr = expression.lower().strip()

    result = _resolve_month(today, expr)
    if result:
        return result

    result = _resolve_quarter(today, expr)
    if result:
        return result

    result = _resolve_year(today, expr)
    if result:
        return result

    result = _resolve_week(today, expr)
    if result:
        return result

    if "học kỳ" in expr:
        result = _resolve_semester(today, expr)
        if result:
            return result

    # Fallback: current month
    start = today.replace(day=1)
    end = today.replace(day=_last_day(today.year, today.month))
    return {
        "start_date": str(start),
        "end_date": str(end),
        "label": f"Tháng {today.month}/{today.year} (mặc định)",
    }
