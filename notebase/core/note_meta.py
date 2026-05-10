from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .note_status import NoteStatus
from .note_type import NoteType
from .schedule import Schedule


@dataclass
class NoteMeta:
    """meta.json と 1:1 対応する dataclass。"""

    id: str = ""
    title: str = ""
    type: NoteType = NoteType.MEMO
    meta_version: int = 1
    status: NoteStatus | None = None
    tags: list[str] = field(default_factory=list)
    project: str | None = None
    due: datetime | None = None
    schedule: Schedule | None = None
    instance_of: str | None = None
    estimated_minutes: int | None = None
    actual_minutes: int | None = None
    created: datetime = field(default_factory=lambda: datetime(1, 1, 1))
    updated: datetime = field(default_factory=lambda: datetime(1, 1, 1))
