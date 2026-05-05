from __future__ import annotations

import os
from pathlib import Path


class AppPaths:
    """MemoRoot 配下の各サブパスを提供する。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @property
    def notes(self) -> Path:
        return self.root / "notes"

    @property
    def trash(self) -> Path:
        return self.root / "trash"

    @property
    def outputs(self) -> Path:
        return self.root / "outputs"

    @property
    def indexes(self) -> Path:
        return self.root / "indexes"

    @property
    def templates(self) -> Path:
        return self.root / "templates"

    @property
    def canvases(self) -> Path:
        return self.root / "canvases"

    @property
    def config(self) -> Path:
        return self.root / "config"

    def note_dir(self, note_id: str) -> Path:
        return self.notes / note_id

    def meta_path(self, note_id: str) -> Path:
        return self.note_dir(note_id) / "meta.json"

    def index_md_path(self, note_id: str) -> Path:
        return self.note_dir(note_id) / "index.md"

    def images_dir(self, note_id: str) -> Path:
        return self.note_dir(note_id) / "images"

    def ensure_layout(self) -> None:
        for p in (
            self.root,
            self.notes,
            self.trash,
            self.outputs,
            self.indexes,
            self.templates,
            self.canvases,
            self.config,
        ):
            p.mkdir(parents=True, exist_ok=True)

    @classmethod
    def default(cls) -> "AppPaths":
        """既定の MemoRoot を返す。

        優先順:
          1. 環境変数 NOTEBASE_ROOT
          2. リポジトリ直下の MemoRoot/  (notebase パッケージの 2 階層上)
        """
        env = os.environ.get("NOTEBASE_ROOT")
        if env:
            return cls(env)
        # __file__ = .../notebase/storage/app_paths.py → 2 階層上がリポジトリルート
        repo_root = Path(__file__).resolve().parent.parent.parent
        return cls(repo_root / "MemoRoot")
