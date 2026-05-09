"""タイムボックス出力の Markdown 1 行を組み立てる共通ヘルパー。

`HH:MM` のパースと加算、および
`- HH:MM–HH:MM <label> (Nm)` 形式の生成を集約する。

`TimeboxItem` には事前メモ (`detail`)、実績分 (`actual_min`)、
遅延理由 (`reason`) を持たせ、シリアライズ時にインデントされた
子行 (`  - 詳細:` / `  - 実績:` / `  - 遅延理由:`) として書き出す。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_START = "09:00"

DETAIL_LABEL = "詳細"
ACTUAL_LABEL = "実績"
REASON_LABEL = "遅延理由"


@dataclass
class TimeboxItem:
    """1 タイムボックス行に対応するデータ。

    `label` / `duration_min` が必須の計画情報。
    `detail` / `actual_min` / `reason` は付随情報で、
    どれも未設定なら子行は出力されない (後方互換)。
    """

    label: str
    duration_min: int
    detail: str = ""
    actual_min: int | None = None
    reason: str = ""


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
    """`items` を Markdown 行リストに変換。

    親行は `- HH:MM–HH:MM label (Nm)`。`detail` / `actual_min` / `reason`
    のうち設定されているものだけを 2 スペースインデントの子行として続ける。
    """
    cur = parse_hhmm(start_time)
    out: list[str] = []
    for it in items:
        end = add_minutes(cur, it.duration_min)
        out.append(
            f"- {format_hhmm(cur)}–{format_hhmm(end)} {it.label} ({it.duration_min}m)"
        )
        if it.detail:
            out.append(f"  - {DETAIL_LABEL}: {it.detail}")
        if it.actual_min is not None:
            out.append(f"  - {ACTUAL_LABEL}: {it.actual_min}m")
        if it.reason:
            out.append(f"  - {REASON_LABEL}: {it.reason}")
        cur = end
    return out
