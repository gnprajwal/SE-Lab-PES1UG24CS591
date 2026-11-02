import pytest
from salon_booking import extra_time_charge, can_book, arrival_status

# Starter test cases
def test_within_included_time():
    assert extra_time_charge("haircut", 20, "junior", False) == 0

def test_can_book():
    assert can_book(2, 1, False) is True

# Tests for 100% Code and Branch Coverage
def test_extra_time_exceptions():
    with pytest.raises(ValueError):
        extra_time_charge("massage", 30, "junior", False)
    with pytest.raises(ValueError):
        extra_time_charge("haircut", -10, "junior", False)

def test_extra_time_all_branches():
    # Branch: is_member True & service != "spa" (True), junior (True), extra <= 60 (False branch of > 60)
    assert extra_time_charge("haircut", 50, "junior", True) == 50
    # Branch: is_member True & service == "spa" (False branch of member bonus)
    assert extra_time_charge("spa", 100, "junior", True) == 100
    # Branch: extra > 60 (True) with stylist_level == "senior" (True)
    assert extra_time_charge("haircut", 120, "senior", True) == 2250
    # Branch: extra > 60 (True) with stylist_level == "senior" (False -> junior)
    assert extra_time_charge("haircut", 100, "junior", False) == 1260

def test_can_book_all_branches():
    # Walk-in True
    assert can_book(2, 1, True) is True
    assert can_book(3, 1, True) is False
    # Walk-in False, party_size > 4 True
    assert can_book(5, 1, False) is False
    # Walk-in False, party_size <= 4, services > 2
    assert can_book(4, 3, False) is False

def test_arrival_status_all_branches():
    # is_colour True, is_weekend True, minutes_early >= cutoff ("open")
    assert arrival_status(20, True, True) == "open"
    # is_colour False, is_weekend False, minutes_early >= cutoff - 15 ("late")
    assert arrival_status(0, False, False) == "late"
    # is_colour False, is_weekend False, minutes_early < cutoff - 15 ("closed")
    assert arrival_status(-15, False, False) == "closed"