"""初回起動時の MemoRoot 移行ヘルパー。

C# 版は `NoteBase_csharp/bin/Debug/MemoRoot/` 配下にデータを置いていた。
Python 版は `<repo_root>/MemoRoot/` を使う。

新ロケーションが空かつ旧ロケーションにデータが存在する場合のみ、
旧ロケーションを丸ごとコピーする (元データは消さない)。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .storage.app_paths import AppPaths


def migrate_legacy_memo_root(target: AppPaths) -> Path | None:
    """旧 MemoRoot を target にコピーする。

    実際に移行を行った場合はコピー元のパスを返す。何もしなかった場合は None。

    条件:
    - target.notes が存在しない or 空である
    - 旧ロケーション (NoteBase_csharp/bin/Debug/MemoRoot/notes) にノートが存在する
    """
    if _is_non_empty(target.notes):
        return None

    repo_root = target.root.parent
    legacy = repo_root / "NoteBase_csharp" / "bin" / "Debug" / "MemoRoot"
    if not (legacy / "notes").exists():
        return None
    if not _is_non_empty(legacy / "notes"):
        return None

    target.ensure_layout()
    for sub in ("notes", "trash", "outputs", "indexes", "templates", "canvases", "config"):
        src = legacy / sub
        if not src.exists():
            continue
        dst = target.root / sub
        for child in src.iterdir():
            dst_child = dst / child.name
            if dst_child.exists():
                continue
            if child.is_dir():
                shutil.copytree(child, dst_child)
            else:
                shutil.copy2(child, dst_child)
    return legacy


def _is_non_empty(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return any(path.iterdir())
    except OSError:
        return False
