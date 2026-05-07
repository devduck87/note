"""ノート本文からタスク行を抽出する。

仕様書 §6.6 の行内メタ記法のうち `@YYYY-MM-DD` (期限) のみ解析する。
`#tag` 抽出は将来対応 (今回スコープ外)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from ..markdown.md_index import _BLOCK_ID_RE  # 末尾 ^id を取り除く

_TASK_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$")
_DATE_RE = re.compile(r"@(\d{4}-\d{2}-\d{2})")


@dataclass
class ExtractedTask:
    note_id: str
    note_title: str
    line_index: int   # 0-based
    text: str         # 装飾 (@date / ^id) を除いたタスクテキスト
    due_date: date | None
    completed: bool


def extract_tasks(note_id: str, note_title: str, body: str | None) -> list[ExtractedTask]:
    """`- [ ]` / `- [x]` 行を抽出して ExtractedTask のリストを返す。

    コードフェンス内はスキップ。期限 (`@YYYY-MM-DD`) は最初の 1 件を採用。
    末尾の `^id` は表示テキストから除く。
    """
    if not body:
        return []
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    in_fence = False
    out: list[ExtractedTask] = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _TASK_RE.match(line)
        if not m:
            continue
        completed = m.group(1).lower() == "x"
        rest = m.group(2)

        # 末尾 ^id を取り除く
        bid = _BLOCK_ID_RE.search(rest)
        if bid:
            rest = rest[: bid.start()]

        # @YYYY-MM-DD を最初の 1 件取り出す
        due: date | None = None
        dm = _DATE_RE.search(rest)
        if dm:
            try:
                due = datetime.strptime(dm.group(1), "%Y-%m-%d").date()
            except ValueError:
                due = None

        # 行から @date 記法を除き、二重空白を 1 つに丸めて trim
        text = _DATE_RE.sub("", rest).strip()
        text = re.sub(r"\s{2,}", " ", text)

        out.append(
            ExtractedTask(
                note_id=note_id,
                note_title=note_title,
                line_index=i,
                text=text,
                due_date=due,
                completed=completed,
            )
        )
    return out
