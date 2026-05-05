from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_ASCII_SLUG_RE = re.compile(r"[^a-z0-9]+")


def generate(title: str, now: datetime) -> str:
    """yyyyMMdd-HHmmss-<slug> 形式のノート ID を生成する。"""
    stamp = now.strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{slugify(title)}"


def slugify(title: str | None) -> str:
    """タイトルを slug に変換する。

    規則:
    - 小文字化
    - ASCII 英数字以外の連続を '-' 1 文字に置換
    - 両端の '-' をトリム
    - 空文字なら "untitled"
    - 60 文字超なら 60 で切り詰め、末尾の '-' を再トリム
    """
    if not title:
        return "untitled"
    lower = title.lower()
    slug = _ASCII_SLUG_RE.sub("-", lower).strip("-")
    if not slug:
        return "untitled"
    if len(slug) > 60:
        slug = slug[:60].rstrip("-")
    if not slug:
        return "untitled"
    return slug


def ensure_unique(note_id: str, parent_dir: str | Path, now: datetime) -> str:
    """parent_dir 配下に同名フォルダがある場合、衝突回避した ID を返す。

    既存と被らない形になるまで以下の順で試す:
      1. 元の note_id
      2. note_id-<ms> (ミリ秒 3 桁)
      3. note_id-<ms>-2, note_id-<ms>-3, ... (最大 999)
    """
    parent = Path(parent_dir)
    if not (parent / note_id).exists():
        return note_id

    ms = f"{now.microsecond // 1000:03d}"
    candidate = f"{note_id}-{ms}"
    if not (parent / candidate).exists():
        return candidate

    for i in range(2, 1000):
        candidate = f"{note_id}-{ms}-{i}"
        if not (parent / candidate).exists():
            return candidate
    raise RuntimeError(f"Failed to generate unique note id: {note_id}")


def replace_slug(note_id: str, new_title: str | None) -> str:
    """ID 末尾の slug を new_title から再計算した値に差し替える。

    parts が 3 未満の場合は変更しない (壊れた ID 保護)。
    """
    parts = note_id.split("-")
    if len(parts) < 3:
        return note_id
    return f"{parts[0]}-{parts[1]}-{slugify(new_title)}"
