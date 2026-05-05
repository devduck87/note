"""手動スモーク: 実データの MemoRoot でメインウィンドウを構築し即終了する。"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from notebase.migrate import migrate_legacy_memo_root
from notebase.storage.app_paths import AppPaths
from notebase.ui.main_window import MainWindow


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    paths = AppPaths(repo_root / "MemoRoot")
    paths.ensure_layout()
    legacy = migrate_legacy_memo_root(paths)
    if legacy:
        print(f"Migrated from {legacy}")

    metas = list((paths.notes).iterdir()) if paths.notes.exists() else []
    print(f"Found {len(metas)} note dirs in {paths.notes}")

    root = tk.Tk()
    root.withdraw()
    win = MainWindow(root, paths)
    root.update_idletasks()
    root.update()
    # 1 ノートを表示
    children = win._notes_tree.get_children()
    print(f"Treeview rows: {len(children)}")
    if children:
        win._notes_tree.selection_set(children[0])
        root.update_idletasks()
        root.update()
    root.destroy()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
