"""指定日に対して `Schedule` がマッチするか判定する。"""

from __future__ import annotations

from datetime import date

from ..core.schedule import Schedule, ScheduleFrequency

_WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def matches(schedule: Schedule | None, target: date) -> bool:
    """`schedule` が `target` 日に有効かを返す。

    - schedule が None または enabled=False → False
    - daily → True
    - weekly → schedule.days に target の曜日 (mon/tue/.../sun) が含まれるか
    - monthly → target.day == schedule.day_of_month
    """
    if schedule is None or not schedule.enabled:
        return False

    if schedule.frequency == ScheduleFrequency.DAILY:
        return True

    if schedule.frequency == ScheduleFrequency.WEEKLY:
        if not schedule.days:
            return False
        wd = _WEEKDAY_KEYS[target.weekday()]
        normalized = {(d or "").strip().lower() for d in schedule.days}
        return wd in normalized

    if schedule.frequency == ScheduleFrequency.MONTHLY:
        return schedule.day_of_month is not None and target.day == schedule.day_of_month

    return False
