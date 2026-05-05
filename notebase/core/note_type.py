from __future__ import annotations

from enum import Enum


class NoteType(Enum):
    PROCEDURE = "procedure"
    MEMO = "memo"
    TODO = "todo"
    ROUTINE = "routine"
    CHECKLIST = "checklist"
    LOG = "log"
    DAILY = "daily"
    PROJECT = "project"

    def to_wire(self) -> str:
        return self.value

    @classmethod
    def parse(cls, s: str | None) -> "NoteType":
        if s is None:
            return cls.MEMO
        for t in cls:
            if t.value == s:
                return t
        return cls.MEMO

    def display_name(self) -> str:
        return _DISPLAY_NAMES.get(self, self.value)


_DISPLAY_NAMES: dict[NoteType, str] = {
    NoteType.PROCEDURE: "手順書",
    NoteType.MEMO: "備忘録",
    NoteType.TODO: "Todo",
    NoteType.ROUTINE: "ルーティーン",
    NoteType.CHECKLIST: "チェックリスト",
    NoteType.LOG: "ログ",
    NoteType.DAILY: "日次メモ",
    NoteType.PROJECT: "プロジェクト",
}
