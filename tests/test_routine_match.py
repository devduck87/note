from __future__ import annotations

import unittest
from datetime import date

from notebase.core.schedule import Schedule, ScheduleFrequency
from notebase.planning.routine_match import matches


class MatchesTests(unittest.TestCase):
    def test_none_returns_false(self) -> None:
        self.assertFalse(matches(None, date(2026, 5, 7)))

    def test_disabled_returns_false(self) -> None:
        s = Schedule(frequency=ScheduleFrequency.DAILY, enabled=False)
        self.assertFalse(matches(s, date(2026, 5, 7)))

    def test_daily_always_true(self) -> None:
        s = Schedule(frequency=ScheduleFrequency.DAILY)
        for day in range(1, 8):
            self.assertTrue(matches(s, date(2026, 5, day)))

    def test_weekly_match(self) -> None:
        # 2026-05-07 = Thursday
        s = Schedule(
            frequency=ScheduleFrequency.WEEKLY,
            days=["mon", "tue", "wed", "thu", "fri"],
        )
        self.assertTrue(matches(s, date(2026, 5, 7)))   # Thu
        self.assertFalse(matches(s, date(2026, 5, 9)))  # Sat

    def test_weekly_empty_days(self) -> None:
        s = Schedule(frequency=ScheduleFrequency.WEEKLY, days=[])
        self.assertFalse(matches(s, date(2026, 5, 7)))

    def test_weekly_case_insensitive(self) -> None:
        s = Schedule(frequency=ScheduleFrequency.WEEKLY, days=["THU"])
        self.assertTrue(matches(s, date(2026, 5, 7)))

    def test_monthly_match(self) -> None:
        s = Schedule(frequency=ScheduleFrequency.MONTHLY, day_of_month=7)
        self.assertTrue(matches(s, date(2026, 5, 7)))
        self.assertFalse(matches(s, date(2026, 5, 8)))

    def test_monthly_no_day(self) -> None:
        s = Schedule(frequency=ScheduleFrequency.MONTHLY, day_of_month=None)
        self.assertFalse(matches(s, date(2026, 5, 7)))


if __name__ == "__main__":
    unittest.main()
