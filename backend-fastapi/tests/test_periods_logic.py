from app.modules.periods.service import _generate_periods, _validate_year_range
from app.core.errors import ValidationError
import pytest


def test_generate_periods_covers_twelve_months_in_order():
    periods = _generate_periods("fy_test", "2026-04-01")
    assert len(periods) == 12
    assert periods[0].period_code == "2026-04"
    assert periods[0].start_date == "2026-04-01"
    assert periods[0].end_date == "2026-04-30"
    assert periods[-1].period_code == "2027-03"
    assert periods[-1].end_date == "2027-03-31"
    # Contiguous, no gaps or overlaps.
    for i in range(1, len(periods)):
        prev_end = periods[i - 1].end_date
        curr_start = periods[i].start_date
        assert curr_start[:4] + curr_start[5:7] > prev_end[:4] + prev_end[5:7] or curr_start > prev_end


def test_generate_periods_handles_february_leap_year():
    periods = _generate_periods("fy_test", "2027-01-01")
    feb = [p for p in periods if p.period_code == "2027-02"][0]
    assert feb.end_date == "2027-02-28"

    periods_leap = _generate_periods("fy_test", "2028-01-01")
    feb_leap = [p for p in periods_leap if p.period_code == "2028-02"][0]
    assert feb_leap.end_date == "2028-02-29"


def test_validate_year_range_accepts_exact_twelve_months():
    _validate_year_range("2026-04-01", "2027-03-31")  # should not raise


def test_validate_year_range_rejects_non_first_of_month_start():
    with pytest.raises(ValidationError):
        _validate_year_range("2026-04-15", "2027-03-31")


def test_validate_year_range_rejects_wrong_end_date():
    with pytest.raises(ValidationError):
        _validate_year_range("2026-04-01", "2027-04-30")
