from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path

from .migrate import migrate_legacy_memo_root
from .platform.file_dnd import initialize_ole, uninitialize_ole
from .storage.app_paths import AppPaths
from .ui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="notebase", description="Markdown ノートアプリ")
    parser.add_argument(
        "--memo-root",
        type=Path,
        default=None,
        help="MemoRoot のパス。指定しなければ NOTEBASE_ROOT 環境変数 / リポジトリ直下の MemoRoot/ を使う。",
    )
    args = parser.parse_args(argv)

    if args.memo_root is not None:
        paths = AppPaths(args.memo_root)
    else:
        paths = AppPaths.default()

    paths.ensure_layout()
    legacy = migrate_legacy_memo_root(paths)
    if legacy is not None:
        print(
            f"[notebase] Migrated legacy notes from {legacy} → {paths.root}",
            file=sys.stderr,
        )

    initialize_ole()
    try:
        root = tk.Tk()
        MainWindow(root, paths)
        root.mainloop()
    finally:
        uninitialize_ole()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
