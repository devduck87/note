from __future__ import annotations

import json
from datetime import datetime

from ..core.note_meta import NoteMeta
from ..core.note_status import NoteStatus
from ..core.note_type import NoteType
from ..core.schedule import Schedule, ScheduleFrequency


def serialize(m: NoteMeta) -> str:
    """NoteMeta を C# 版とバイト一致する JSON 文字列に変換する。

    - フィールド順固定
    - インデント 2 スペース
    - 空でない/値ありフィールドのみ出力 (status/project/due/schedule/instance_of は省略可)
    - tags は常に出力 (空でも [] を出す)
    - 末尾に改行 1 つ
    """
    lines: list[str] = []
    lines.append(_int_field("meta_version", m.meta_version))
    lines.append(_string_field("id", m.id or ""))
    lines.append(_string_field("title", m.title or ""))
    lines.append(_string_field("type", m.type.to_wire()))
    if m.status is not None:
        lines.append(_string_field("status", m.status.to_wire()))
    lines.append(_string_array_field("tags", m.tags or []))
    if m.project:
        lines.append(_string_field("project", m.project))
    if m.due is not None:
        lines.append(_string_field("due", _format_date(m.due)))
    if m.schedule is not None:
        lines.append(_schedule_field("schedule", m.schedule))
    if m.instance_of:
        lines.append(_string_field("instance_of", m.instance_of))
    if m.estimated_minutes is not None:
        lines.append(_int_field("estimated_minutes", m.estimated_minutes))
    if m.actual_minutes is not None:
        lines.append(_int_field("actual_minutes", m.actual_minutes))
    lines.append(_string_field("created", _format_datetime(m.created)))
    lines.append(_string_field("updated", _format_datetime(m.updated)))

    return "{\n" + ",\n".join(lines) + "\n}\n"


def deserialize(text: str) -> NoteMeta:
    """JSON テキストから NoteMeta を復元する。"""
    d = json.loads(text)
    return _meta_from_dict(d)


def _meta_from_dict(d: dict) -> NoteMeta:
    m = NoteMeta()
    if "meta_version" in d and d["meta_version"] is not None:
        m.meta_version = int(d["meta_version"])
    if "id" in d:
        m.id = d["id"] or ""
    if "title" in d:
        m.title = d["title"] or ""
    if "type" in d:
        m.type = NoteType.parse(d["type"])
    if "status" in d:
        m.status = NoteStatus.parse(d["status"])
    if "tags" in d and isinstance(d["tags"], list):
        m.tags = [v if v is not None else "" for v in d["tags"]]
    if "project" in d:
        m.project = d["project"]
    if "due" in d and d["due"] is not None:
        m.due = _parse_date(d["due"])
    if "schedule" in d and isinstance(d["schedule"], dict):
        m.schedule = _schedule_from_dict(d["schedule"])
    if "instance_of" in d:
        m.instance_of = d["instance_of"]
    if "estimated_minutes" in d and d["estimated_minutes"] is not None:
        try:
            m.estimated_minutes = int(d["estimated_minutes"])
        except (TypeError, ValueError):
            m.estimated_minutes = None
    if "actual_minutes" in d and d["actual_minutes"] is not None:
        try:
            m.actual_minutes = int(d["actual_minutes"])
        except (TypeError, ValueError):
            m.actual_minutes = None
    if "created" in d and isinstance(d["created"], str):
        m.created = _parse_datetime(d["created"])
    if "updated" in d and isinstance(d["updated"], str):
        m.updated = _parse_datetime(d["updated"])
    return m


def _schedule_from_dict(d: dict) -> Schedule:
    s = Schedule()
    if "frequency" in d:
        s.frequency = ScheduleFrequency.parse(d["frequency"])
    if "days" in d and isinstance(d["days"], list):
        s.days = [v for v in d["days"] if isinstance(v, str)]
    if "day_of_month" in d and d["day_of_month"] is not None:
        s.day_of_month = int(d["day_of_month"])
    if "enabled" in d:
        s.enabled = bool(d["enabled"]) if isinstance(d["enabled"], bool) else True
    return s


def _int_field(name: str, value: int) -> str:
    return f'  "{name}": {int(value)}'


def _string_field(name: str, value: str) -> str:
    return f'  "{name}": {_escape_string(value or "")}'


def _string_array_field(name: str, values: list[str]) -> str:
    parts = [_escape_string(v or "") for v in values]
    return f'  "{name}": [' + ", ".join(parts) + "]"


def _schedule_field(name: str, s: Schedule) -> str:
    inner: list[str] = []
    inner.append(f'    "frequency": {_escape_string(s.frequency.to_wire())}')
    if s.days:
        parts = [_escape_string(d or "") for d in s.days]
        inner.append('    "days": [' + ", ".join(parts) + "]")
    if s.day_of_month is not None:
        inner.append(f'    "day_of_month": {int(s.day_of_month)}')
    inner.append(f'    "enabled": {"true" if s.enabled else "false"}')
    body = ",\n".join(inner)
    return f'  "{name}": {{\n{body}\n  }}'


def _escape_string(s: str) -> str:
    out: list[str] = ['"']
    for ch in s:
        c = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif c < 0x20:
            out.append(f"\\u{c:04X}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _parse_datetime(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return datetime(1, 1, 1)


def _parse_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return datetime(1, 1, 1)
