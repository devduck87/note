"""手動スモーク: MarkdownText を Tk の中で構築して DnD 登録が機能するかを確認する。

実際にドラッグはしないが、IDropTarget の登録 (RegisterDragDrop) が成功して
登録解除も例外なく終わることをチェックする。
"""

from __future__ import annotations

import tempfile
import tkinter as tk
from pathlib import Path

from notebase.platform.file_dnd import initialize_ole, uninitialize_ole
from notebase.ui.markdown_text import MarkdownText


def main() -> int:
    initialize_ole()
    try:
        with tempfile.TemporaryDirectory() as td:
            root = tk.Tk()
            root.geometry("400x300")
            md = MarkdownText(root)
            md.pack(fill="both", expand=True)
            md.note_dir = Path(td)
            root.update_idletasks()
            # 一度 deiconify → withdraw して Map イベントを発火させる
            root.deiconify()
            root.update()

            registered = md._drop_target is not None and md._drop_target.registered
            print(f"DropTarget registered: {registered}")

            # 後始末
            md.destroy()
            root.destroy()
    finally:
        uninitialize_ole()

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
