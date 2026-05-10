"""YAML frontmatter のサブセット parser / serializer + NoteMeta ブリッジ。

サポートする構文:
- `---` で挟まれた frontmatter ブロック (本文先頭にのみ)
- `key: scalar` (string / int / bool / null)
- `key: [a, b, c]` インライン配列
- `key: {k1: v1, k2: v2}` インラインオブジェクト
- `"..."` または `'...'` で囲った文字列 (カンマ・コロンを含めたい場合)
- `# ...` コメント行 (frontmatter 内のみ)

サポートしない構文:
- インデントによる nesting (代わりにインラインオブジェクトを使う)
- 複数行文字列 (`|` `>`)
- アンカー / エイリアス
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from ..core.note_meta import NoteMeta
from ..core.note_status import NoteStatus
from ..core.note_type import NoteType
from ..core.schedule import Schedule, ScheduleFrequency


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """テキストを (frontmatter テキスト, 本文) に分割する。

    frontmatter が無ければ `(None, text)` を返す。
    """
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            if body.startswith("\n"):
                body = body[1:]
            return fm, body
    return None, text


def parse_frontmatter(fm_text: str) -> dict[str, Any]:
    """frontmatter テキストを dict にする。形式エラー行は読み飛ばし。"""
    out: dict[str, Any] = {}
    for raw in fm_text.split("\n"):
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        m = _KEY_RE.match(line)
        if not m:
            continue
        key = m.group(1)
        out[key] = _parse_value(m.group(2).strip())
    return out


def serialize_frontmatter(d: dict[str, Any]) -> str:
    """dict を frontmatter テキスト (フェンス込み) にする。空 dict なら `---\\n---`。"""
    lines = ["---"]
    for k, v in d.items():
        lines.append(f"{k}: {_format_value(v)}")
    lines.append("---")
    return "\n".join(lines)


def combine(fm_dict: dict[str, Any], body: str) -> str:
    """frontmatter dict と本文を結合した 1 つのテキストを返す。"""
    fm = serialize_frontmatter(fm_dict)
    if body and not body.startswith("\n"):
        return fm + "\n\n" + body
    return fm + "\n" + body


def _parse_value(v: str) -> Any:
    if v == "":
        return None
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        return [_parse_value(x) for x in _split_csv(inner)]
    if v.startswith("{") and v.endswith("}"):
        inner = v[1:-1]
        d: dict[str, Any] = {}
        for pair in _split_csv(inner):
            if ":" in pair:
                pk, pv = pair.split(":", 1)
                d[pk.strip()] = _parse_value(pv.strip())
        return d
    lo = v.lower()
    if lo in ("true", "false"):
        return lo == "true"
    if lo in ("null", "~"):
        return None
    if (v.startswith('"') and v.endswith('"')) or (
        v.startswith("'") and v.endswith("'")
    ):
        return v[1:-1]
    try:
        return int(v)
    except ValueError:
        pass
    return v


def _format_value(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_format_value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(
            f"{k}: {_format_value(val)}" for k, val in v.items()
        ) + "}"
    s = str(v)
    if any(c in s for c in ",[]{}:'\""):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _split_csv(s: str) -> list[str]:
    """カンマ区切り。引用符 / ブラケット内のカンマは無視。"""
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    in_quote: str | None = None
    for ch in s:
        if in_quote:
            cur.append(ch)
            if ch == in_quote:
                in_quote = None
        elif ch in ('"', "'"):
            in_quote = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return [p for p in parts if p]


# ------------------------------------------------------------
# NoteMeta <-> frontmatter dict
# ------------------------------------------------------------


def meta_to_dict(meta: NoteMeta) -> dict[str, Any]:
    """NoteMeta をテキストモード表示用の dict に変換する。

    `id` / `created` / `updated` / `meta_version` は出力しない (UI で編集対象外)。
    """
    d: dict[str, Any] = {"title": meta.title or ""}
    d["type"] = meta.type.to_wire()
    if meta.status is not None:
        d["status"] = meta.status.to_wire()
    if meta.tags:
        d["tags"] = list(meta.tags)
    if meta.project:
        d["project"] = meta.project
    if meta.due is not None:
        d["due"] = meta.due.strftime("%Y-%m-%d")
    if meta.schedule is not None:
        sd: dict[str, Any] = {"frequency": meta.schedule.frequency.to_wire()}
        if meta.schedule.days:
            sd["days"] = list(meta.schedule.days)
        if meta.schedule.day_of_month is not None:
            sd["day_of_month"] = meta.schedule.day_of_month
        sd["enabled"] = meta.schedule.enabled
        d["schedule"] = sd
    if meta.instance_of:
        d["instance_of"] = meta.instance_of
    if meta.estimated_minutes is not None:
        d["estimated_minutes"] = meta.estimated_minutes
    if meta.actual_minutes is not None:
        d["actual_minutes"] = meta.actual_minutes
    return d


def apply_dict_to_meta(d: dict[str, Any], meta: NoteMeta) -> None:
    """frontmatter dict の値を `meta` に in-place で反映する。

    キーが存在するフィールドのみ上書き。未知キーは無視。
    解釈不能な値はその項目だけ素通り (例外は出さない)。
    """
    if "title" in d:
        meta.title = str(d["title"] or "")
    if "type" in d and d["type"] is not None:
        meta.type = NoteType.parse(str(d["type"]))
    if "status" in d:
        v = d["status"]
        meta.status = NoteStatus.parse(str(v)) if v else None
    if "tags" in d:
        v = d["tags"]
        if isinstance(v, list):
            meta.tags = [str(t) for t in v if t is not None]
        elif v is None:
            meta.tags = []
    if "project" in d:
        v = d["project"]
        meta.project = str(v) if v else None
    if "due" in d:
        v = d["due"]
        if v:
            try:
                meta.due = datetime.strptime(str(v), "%Y-%m-%d")
            except ValueError:
                pass
        else:
            meta.due = None
    if "instance_of" in d:
        v = d["instance_of"]
        meta.instance_of = str(v) if v else None
    if "estimated_minutes" in d:
        v = d["estimated_minutes"]
        if v is None:
            meta.estimated_minutes = None
        else:
            try:
                meta.estimated_minutes = int(v)
            except (TypeError, ValueError):
                pass
    if "actual_minutes" in d:
        v = d["actual_minutes"]
        if v is None:
            meta.actual_minutes = None
        else:
            try:
                meta.actual_minutes = int(v)
            except (TypeError, ValueError):
                pass
    if "schedule" in d:
        v = d["schedule"]
        if isinstance(v, dict):
            s = Schedule()
            if "frequency" in v:
                s.frequency = ScheduleFrequency.parse(str(v["frequency"]))
            if "days" in v and isinstance(v["days"], list):
                s.days = [str(x) for x in v["days"] if x is not None]
            if "day_of_month" in v and v["day_of_month"] is not None:
                try:
                    s.day_of_month = int(v["day_of_month"])
                except (TypeError, ValueError):
                    pass
            if "enabled" in v:
                s.enabled = bool(v["enabled"])
            meta.schedule = s
        elif v is None:
            meta.schedule = None
