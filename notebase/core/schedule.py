from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ScheduleFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

    def to_wire(self) -> str:
        return self.value

    @classmethod
    def parse(cls, s: str | None) -> "ScheduleFrequency":
        if s is None:
            return cls.DAILY
        for f in cls:
            if f.value == s:
                return f
        return cls.DAILY


@dataclass
class Schedule:
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    days: list[str] | None = None
    day_of_month: int | None = None
    enabled: bool = True
