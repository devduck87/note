from __future__ import annotations

from enum import Enum


class NoteStatus(Enum):
    ACTIVE = "active"
    DONE = "done"
    PENDING = "pending"
    ARCHIVED = "archived"

    def to_wire(self) -> str:
        return self.value

    @classmethod
    def parse(cls, s: str | None) -> "NoteStatus | None":
        if s is None:
            return None
        for st in cls:
            if st.value == s:
                return st
        return None
