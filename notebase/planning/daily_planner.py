"""本日のプラン: 候補集約とチェックリスト/タイムボクシング Markdown 生成。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from ..core.note_type import NoteType
from ..storage.note_repository import NoteRepository
from .routine_match import matches as schedule_matches
from .task_extract import extract_tasks

DEFAULT_DURATION_MIN = 30
DEFAULT_START_TIME = "09:00"


@dataclass
class PlanItem:
    """本日プランの 1 行。"""

    source_id: str
    """元ノート ID。タスク行の場合も親ノートの ID。"""

    text: str
    """プランに表示する文字列 (装飾を除いたタスクテキスト or routine タイトル)。"""

    duration_min: int = DEFAULT_DURATION_MIN

    note_title: str | None = None
    """出典表示用 (todo タスクの所属ノートタイトル等)。"""

    kind: str = "task"
    """task / routine / manual のどれか。表示で使う。"""


def candidates_for(repo: NoteRepository, target: date) -> list[PlanItem]:
    """`target` 日のプラン候補を集約する。

    - todo: 未完了かつ due_date <= target、または due_date 無しのものを 1 行ずつ
    - routine: enabled かつ schedule_matches で当日該当のものを 1 ノート 1 行
    - 並びは routine → todo の順 (ルーティーンを上に置く)
    """
    routine_items: list[PlanItem] = []
    task_items: list[PlanItem] = []

    for meta in repo.load_all():
        if meta.type == NoteType.ROUTINE:
            if schedule_matches(meta.schedule, target):
                routine_items.append(
                    PlanItem(
                        source_id=meta.id,
                        text=meta.title or "(無題のルーティーン)",
                        duration_min=DEFAULT_DURATION_MIN,
                        note_title=meta.title,
                        kind="routine",
                    )
                )
            continue

        if meta.type == NoteType.TODO:
            try:
                _meta, body = repo.load(meta.id)
            except OSError:
                continue
            for t in extract_tasks(meta.id, meta.title or "", body):
                if t.completed:
                    continue
                if t.due_date is not None and t.due_date > target:
                    continue
                task_items.append(
                    PlanItem(
                        source_id=meta.id,
                        text=t.text,
                        duration_min=DEFAULT_DURATION_MIN,
                        note_title=meta.title,
                        kind="task",
                    )
                )

    return routine_items + task_items


def render_markdown(
    items: list[PlanItem],
    target: date,
    start_time: str = DEFAULT_START_TIME,
) -> str:
    """チェックリストとタイムボクシングを併記した Markdown を返す。

    出力フォーマット:
        # YYYY-MM-DD のプラン

        ## チェックリスト

        - [ ] テキスト (出典)

        ## タイムボックス

        - HH:MM–HH:MM テキスト (出典) (Nm)
    """
    lines: list[str] = []
    title_date = target.strftime("%Y-%m-%d")
    lines.append(f"# {title_date} のプラン")
    lines.append("")

    lines.append("## チェックリスト")
    lines.append("")
    if items:
        for it in items:
            lines.append(f"- [ ] {_format_text(it)}")
    else:
        lines.append("(候補なし)")
    lines.append("")

    lines.append("## タイムボックス")
    lines.append("")
    if items:
        cursor = _parse_time(start_time)
        for it in items:
            end = cursor + timedelta(minutes=max(0, it.duration_min))
            lines.append(
                f"- {_fmt(cursor)}–{_fmt(end)} {_format_text(it)} ({it.duration_min}m)"
            )
            cursor = end
    else:
        lines.append("(候補なし)")

    return "\n".join(lines) + "\n"


def _format_text(item: PlanItem) -> str:
    if item.kind == "routine" and item.note_title:
        return item.text
    if item.note_title and item.note_title != item.text:
        return f"{item.text} ({item.note_title})"
    return item.text


def _parse_time(s: str) -> datetime:
    try:
        return datetime.strptime(s.strip(), "%H:%M")
    except ValueError:
        return datetime.strptime(DEFAULT_START_TIME, "%H:%M")


def _fmt(dt: datetime) -> str:
    return dt.strftime("%H:%M")
