from __future__ import annotations

import shutil
from datetime import datetime

from .app_paths import AppPaths


class TrashService:
    """ノートフォルダを trash/ へ移動する。"""

    def __init__(self, paths: AppPaths) -> None:
        self._paths = paths

    def move_note(self, note_id: str | None) -> None:
        """指定 ID のノートフォルダを trash/<stamp>_<id> として移動する。

        ノートが存在しない場合は何もしない。
        """
        if not note_id:
            return
        src = self._paths.note_dir(note_id)
        if not src.exists():
            return
        self._paths.trash.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        stamp = f"{now.strftime('%Y%m%d-%H%M%S')}-{now.microsecond // 1000:03d}"
        dest = self._paths.trash / f"{stamp}_{note_id}"
        shutil.move(str(src), str(dest))
