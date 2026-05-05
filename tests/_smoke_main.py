"""手動スモーク: 一時 MemoRoot でメインウィンドウを構築し即終了する。"""

from __future__ import annotations

import tempfile
import tkinter as tk

from notebase.storage.app_paths import AppPaths
from notebase.ui.main_window import MainWindow


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        paths = AppPaths(td)
        root = tk.Tk()
        root.withdraw()
        MainWindow(root, paths)
        root.update_idletasks()
        root.update()
        root.destroy()
    print("MainWindow constructed and updated without error")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
