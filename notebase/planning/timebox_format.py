"""タイムボックス出力の Markdown 1 行を組み立てる共通ヘルパー。

`HH:MM` のパースと加算、および
`- HH:MM–HH:MM <label> (Nm)` 形式の生成を集約する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_START = "09:00"


@dataclass
class TimeboxItem:
    """1 タイムボックス行に対応するデータ。"""

    label: str
    duration_min: int


def parse_hhmm(s: str | None) -> datetime:
    """`HH:MM` を datetime (日付は 1900-01-01) に変換。失敗時は既定 09:00。"""
    if not s:
        return datetime.strptime(DEFAULT_START, "%H:%M")
    try:
        return datetime.strptime(s.strip(), "%H:%M")
    except ValueError:
        return datetime.strptime(DEFAULT_START, "%H:%M")


def format_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def add_minutes(dt: datetime, minutes: int) -> datetime:
    return dt + timedelta(minutes=max(0, minutes))


def render_timebox_lines(
    items: list[TimeboxItem],
    start_time: str = DEFAULT_START,
) -> list[str]:
    """`items` を `- HH:MM–HH:MM label (Nm)` 形式の Markdown 行リストに変換。"""
    cur = parse_hhmm(start_time)
    out: list[str] = []
    for it in items:
        end = add_minutes(cur, it.duration_min)
        out.append(
            f"- {format_hhmm(cur)}–{format_hhmm(end)} {it.label} ({it.duration_min}m)"
        )
        cur = end
    return out
