"""ノート種別ごとに「表示フィールド・初期値・本文テンプレート」を定義する設定。

組み込みデフォルトを `BUILTIN_CONFIGS` で持ち、ユーザは
`MemoRoot/config/note_types.json` で type 単位に上書きできる。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .note_status import NoteStatus
from .note_type import NoteType
from .schedule import Schedule, ScheduleFrequency

# 編集ウィンドウ内の動的フィールド識別子。`_update_type_dependent_fields`
# が grid()/grid_remove() の対象に使う。タイトル/種別は常時表示。
KNOWN_FIELDS = {
    "status",
    "tags",
    "project",
    "due",
    "estimated_minutes",
    "actual_minutes",
    "schedule",
}


@dataclass
class NoteTypeConfig:
    """1 つのノート種別に紐付く UI / 初期値設定。"""

    fields: list[str] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    body_template: str = ""

    def default_status(self) -> NoteStatus | None:
        v = self.defaults.get("status")
        return NoteStatus.parse(v) if v else None

    def default_tags(self) -> list[str]:
        v = self.defaults.get("tags") or []
        return [str(t) for t in v if isinstance(t, (str, int))]

    def default_schedule(self) -> Schedule | None:
        v = self.defaults.get("schedule")
        if not isinstance(v, dict):
            return None
        s = Schedule()
        if "frequency" in v:
            s.frequency = ScheduleFrequency.parse(v["frequency"])
        if "days" in v and isinstance(v["days"], list):
            s.days = [d for d in v["days"] if isinstance(d, str)]
        if "day_of_month" in v and v["day_of_month"] is not None:
            try:
                s.day_of_month = int(v["day_of_month"])
            except (TypeError, ValueError):
                pass
        if "enabled" in v:
            s.enabled = bool(v["enabled"])
        return s


BUILTIN_CONFIGS: dict[NoteType, NoteTypeConfig] = {
    NoteType.MEMO: NoteTypeConfig(
        fields=["status", "tags", "project"],
        defaults={"status": "active"},
        body_template="",
    ),
    NoteType.PROCEDURE: NoteTypeConfig(
        fields=["status", "tags", "project"],
        defaults={"status": "active"},
        body_template="## 手順\n\n1. \n",
    ),
    NoteType.TODO: NoteTypeConfig(
        fields=["status", "tags", "project", "due"],
        defaults={"status": "active"},
        body_template="- [ ] \n",
    ),
    NoteType.ROUTINE: NoteTypeConfig(
        fields=["status", "tags", "schedule"],
        defaults={
            "status": "active",
            "schedule": {"frequency": "weekly", "enabled": True},
        },
        body_template="- [ ] \n",
    ),
    NoteType.LOG: NoteTypeConfig(
        fields=[
            "status",
            "tags",
            "project",
            "estimated_minutes",
            "actual_minutes",
        ],
        defaults={"status": "active"},
        body_template="## 詳細\n\n## 作業メモ\n\n## 振り返り\n",
    ),
    NoteType.DAILY: NoteTypeConfig(
        fields=["status", "tags"],
        defaults={"status": "active"},
        body_template="",
    ),
    NoteType.PROJECT: NoteTypeConfig(
        fields=["status", "tags"],
        defaults={"status": "active"},
        body_template="",
    ),
}


def load_configs(path: Path | None) -> dict[NoteType, NoteTypeConfig]:
    """JSON ファイルから設定を読み込み、組み込みデフォルトに上書きマージ。

    - ファイルが無い / 壊れている / type が未知 の場合は組み込みデフォルトを採用
    - JSON で指定された type だけが上書き対象 (他は組み込みのまま)
    - フィールドレベルでも部分上書き可能 (defaults の一部だけ書く等)
    """
    merged: dict[NoteType, NoteTypeConfig] = {
        t: NoteTypeConfig(
            fields=list(c.fields),
            defaults=dict(c.defaults),
            body_template=c.body_template,
        )
        for t, c in BUILTIN_CONFIGS.items()
    }

    if path is None or not path.exists():
        return merged

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return merged

    if not isinstance(raw, dict):
        return merged

    for type_key, override in raw.items():
        if not isinstance(override, dict):
            continue
        try:
            note_type = NoteType.parse(type_key)
        except Exception:
            continue
        if note_type not in merged:
            continue
        cfg = merged[note_type]
        if "fields" in override and isinstance(override["fields"], list):
            cfg.fields = [
                f for f in override["fields"] if f in KNOWN_FIELDS
            ]
        if "defaults" in override and isinstance(override["defaults"], dict):
            cfg.defaults.update(override["defaults"])
        if "body_template" in override and isinstance(
            override["body_template"], str
        ):
            cfg.body_template = override["body_template"]

    return merged


def get_config(
    configs: dict[NoteType, NoteTypeConfig], note_type: NoteType
) -> NoteTypeConfig:
    return configs.get(note_type) or BUILTIN_CONFIGS.get(
        note_type, NoteTypeConfig()
    )
