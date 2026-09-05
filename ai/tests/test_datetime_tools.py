import pytest
from freezegun import freeze_time
from unittest.mock import patch, MagicMock

# Pre-import to ensure langchain_core / pydantic initialise before any
# freeze_time context is active (first import inside freeze_time can fail).
from agent.tools.datetime_tools import resolve_time_range  # noqa: E402


@freeze_time("2026-09-05")
def test_tháng_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tháng trước"})
    assert result["start_date"] == "2026-08-01"
    assert result["end_date"] == "2026-08-31"
    assert "8" in result["label"] or "Tháng" in result["label"]


@freeze_time("2026-09-05")
def test_tháng_này():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tháng này"})
    assert result["start_date"] == "2026-09-01"
    assert result["end_date"] == "2026-09-30"


@freeze_time("2026-09-05")
def test_năm_ngoái():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "năm ngoái"})
    assert result["start_date"] == "2025-01-01"
    assert result["end_date"] == "2025-12-31"


@freeze_time("2026-09-05")
def test_năm_nay():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "năm nay"})
    assert result["start_date"] == "2026-01-01"
    assert result["end_date"] == "2026-12-31"


@freeze_time("2026-09-05")
def test_quý_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "quý trước"})
    assert result["start_date"] == "2026-04-01"
    assert result["end_date"] == "2026-06-30"


@freeze_time("2026-09-05")
def test_hai_quý_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "2 quý trước"})
    assert result["start_date"] == "2026-01-01"
    assert result["end_date"] == "2026-03-31"


@freeze_time("2026-09-05")
def test_tuần_trước():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tuần trước"})
    assert result["start_date"] == "2026-08-24"
    assert result["end_date"] == "2026-08-30"


@freeze_time("2026-09-05")
def test_tháng_specific():
    from agent.tools.datetime_tools import resolve_time_range
    result = resolve_time_range.invoke({"expression": "tháng 3"})
    assert result["start_date"] == "2026-03-01"
    assert result["end_date"] == "2026-03-31"
