import pytest
from salon_booking import extra_time_charge, can_book, arrival_status

# Starter test cases
def test_within_included_time():
    assert extra_time_charge("haircut", 20, "junior", False) == 0

def test_can_book():
    assert can_book(2, 1, False) is True

# Added tests for 100% Line (Code) Coverage
def test_extra_time_exceptions():
    with pytest.raises(ValueError):
        extra_time_charge("massage", 30, "junior", False)
    with pytest.raises(ValueError):
        extra_time_charge("haircut", -10, "junior", False)

def test_extra_time_junior_and_senior():
    # Covers member bonus, junior rate
    assert extra_time_charge("haircut", 50, "junior", True) == 50
    # Covers non-junior rate, extra > 60, and senior surcharge
    assert extra_time_charge("haircut", 120, "senior", True) == 2250

def test_can_book_remaining_lines():
    assert can_book(2, 1, True) is True
    assert can_book(5, 1, False) is False

def test_arrival_status_lines():
    assert arrival_status(25, True, True) == "open"
    assert arrival_status(5, False, True) == "late"
    assert arrival_status(-5, False, True) == "closed"