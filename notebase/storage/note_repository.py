from __future__ import annotations

import random
import re
import string
from datetime import datetime
from pathlib import Path
from typing import Iterator

from ..core import note_id as note_id_mod
from ..core.note_meta import NoteMeta
from ..core.note_status import NoteStatus
from ..core.note_type import NoteType
from . import meta_json
from .app_paths import AppPaths
from .atomic_writer import write_text_atomic
from .trash_service import TrashService

_BLOCK_ID_RE = re.compile(r"\s+\^([a-zA-Z0-9-]+)\s*$")
_ANY_BLOCK_ID_RE = re.compile(r"\s\^([a-zA-Z0-9-]+)")
_ID_ALPHABET = string.ascii_lowercase + string.digits


class NoteRepository:
    """ノートの保存・読み込み・ドラフト作成・ゴミ箱移動を担当する。"""

    def __init__(self, paths: AppPaths, trash: TrashService) -> None:
        self._paths = paths
        self._trash = trash

    @property
    def paths(self) -> AppPaths:
        return self._paths

    def get_note_dir(self, note_id: str) -> Path:
        return self._paths.note_dir(note_id)

    # ------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------

    def create_draft(self, note_type: NoteType) -> NoteMeta:
        """入力 UI で type 選択時に呼ばれる。仮 ID でフォルダを作成する。

        確定保存時 (save_new) でタイトルから slug を再計算してフォルダ名を rename する。
        """
        now = datetime.now()
        nid = note_id_mod.generate("untitled", now)
        nid = note_id_mod.ensure_unique(nid, self._paths.notes, now)

        self._paths.note_dir(nid).mkdir(parents=True, exist_ok=True)
        self._paths.images_dir(nid).mkdir(parents=True, exist_ok=True)

        return NoteMeta(
            id=nid,
            title="",
            type=note_type,
            status=NoteStatus.ACTIVE,
            tags=[],
            created=now,
            updated=now,
        )

    def save_new(self, meta: NoteMeta, body: str) -> NoteMeta:
        """新規ノートの初回確定保存。タイトルから slug を計算してフォルダ名を確定する。"""
        if meta is None:
            raise ValueError("meta must not be None")

        new_id = note_id_mod.replace_slug(meta.id, meta.title)
        if new_id != meta.id:
            if self._paths.note_dir(new_id).exists():
                new_id = note_id_mod.ensure_unique(new_id, self._paths.notes, datetime.now())
            self._paths.note_dir(meta.id).rename(self._paths.note_dir(new_id))
            meta.id = new_id
        return self._write_common(meta, body)

    def save_existing(self, meta: NoteMeta, body: str) -> NoteMeta:
        """既存ノートの上書き保存。フォルダ名 (ID) は変更しない。"""
        if meta is None:
            raise ValueError("meta must not be None")
        return self._write_common(meta, body)

    def _write_common(self, meta: NoteMeta, body: str) -> NoteMeta:
        meta.updated = datetime.now().replace(microsecond=0)
        body = _sync_title_h1(body, meta.title)
        write_text_atomic(self._paths.meta_path(meta.id), meta_json.serialize(meta))
        write_text_atomic(self._paths.index_md_path(meta.id), body)
        return meta

    def load(self, note_id: str) -> tuple[NoteMeta, str]:
        meta_text = self._paths.meta_path(note_id).read_text(encoding="utf-8")
        meta = meta_json.deserialize(meta_text)
        index_md = self._paths.index_md_path(note_id)
        body = index_md.read_text(encoding="utf-8") if index_md.exists() else ""
        return meta, body

    def load_all(self) -> Iterator[NoteMeta]:
        """notes/ 配下を走査して全ノートのメタを返す。壊れた meta.json はスキップ。"""
        notes = self._paths.notes
        if not notes.exists():
            return
        for d in sorted(p for p in notes.iterdir() if p.is_dir()):
            meta_path = d / "meta.json"
            if not meta_path.exists():
                continue
            try:
                meta = meta_json.deserialize(meta_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            yield meta

    def move_to_trash(self, note_id: str) -> None:
        self._trash.move_note(note_id)

    # ------------------------------------------------------------
    # ブロック ID 自動付与
    # ------------------------------------------------------------

    def ensure_block_id(self, note_id: str, line_end: int) -> str | None:
        """指定行末にブロック ID (^xxxxxx) を確保する。

        既に ID が付いていればそれを返す。無ければ生成して該当行末に追記し、上書き保存する。
        空行や範囲外の行には付与せず None を返す。
        """
        meta, body = self.load(note_id)
        normalized = (body or "").replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        if line_end < 0 or line_end >= len(lines):
            return None

        existing = _BLOCK_ID_RE.search(lines[line_end])
        if existing:
            return existing.group(1)

        all_ids = _extract_all_block_ids(body)
        new_id = ""
        for attempt in range(101):
            new_id = _generate_block_id()
            if new_id not in all_ids:
                break
        else:
            return None

        trimmed = lines[line_end].rstrip()
        if not trimmed:
            return None
        lines[line_end] = f"{trimmed} ^{new_id}"
        new_body = "\r\n".join(lines)
        self.save_existing(meta, new_body)
        return new_id


def _extract_all_block_ids(body: str | None) -> set[str]:
    if not body:
        return set()
    return {m.group(1) for m in _ANY_BLOCK_ID_RE.finditer(body)}


def _generate_block_id() -> str:
    return "".join(random.choice(_ID_ALPHABET) for _ in range(6))


def _sync_title_h1(body: str | None, title: str | None) -> str:
    """本文先頭の H1 をタイトルに同期する。

    既に H1 があれば差し替え、無ければ先頭に追加する。改行は \r\n に統一。
    """
    safe_title = title or ""
    src = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = src.split("\n")

    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1

    if i < len(lines) and lines[i].startswith("# "):
        lines[i] = f"# {safe_title}"
        return "\r\n".join(lines)

    return f"# {safe_title}\r\n\r\n" + "\r\n".join(lines)
