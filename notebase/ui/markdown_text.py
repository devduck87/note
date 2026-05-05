"""Markdown 編集用の Text ウィジェット。

C# 版の MarkdownTextBox 相当。
- 等幅フォント / 折り返し無し / 縦スクロール
- Ctrl+V による画像貼付 (Win32 クリップボード DIB を Python で PNG にエンコード)
- Explorer 等からのファイル DnD (OLE IDropTarget を ctypes COM で実装)
- ファイル選択ダイアログによる画像取り込み (DnD のフォールバック)
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from ..platform.clipboard_image import get_clipboard_png
from ..platform.file_dnd import DropTarget
from ..storage.image_store import ImageStore


class MarkdownText(ttk.Frame):
    """スクロールバー付き Text + 画像貼付フックのコンポーネント。"""

    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._note_dir: Path | None = None
        self._image_store = ImageStore()
        self._drop_target: DropTarget | None = None

        self.text = tk.Text(
            self,
            wrap="none",
            font=("Consolas", 10),
            undo=True,
            maxundo=200,
        )
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.config(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.text.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.text.bind("<Control-v>", self._on_paste)
        self.text.bind("<Control-V>", self._on_paste)
        # OLE DnD は実 HWND が必要なので、ウィジェットが Map された後に登録する
        self.text.bind("<Map>", self._on_map, add=True)
        self.text.bind("<Destroy>", self._on_destroy, add=True)

    # ------------------------------------------------------------
    # public
    # ------------------------------------------------------------

    @property
    def note_dir(self) -> Path | None:
        return self._note_dir

    @note_dir.setter
    def note_dir(self, value: str | Path | None) -> None:
        self._note_dir = Path(value) if value else None

    def get(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set(self, body: str) -> None:
        self.text.delete("1.0", "end")
        if body:
            self.text.insert("1.0", body)
        self.text.edit_reset()

    def insert_at_cursor(self, snippet: str) -> None:
        self.text.insert("insert", snippet)

    def attach_dropped_files(self, paths: list[str]) -> None:
        """ファイル選択ダイアログ経由で渡されたファイルを画像として取り込む。"""
        if self._note_dir is None:
            return
        for p in paths:
            try:
                rel = self._image_store.save_dropped_image(self._note_dir, p)
            except (OSError, ValueError):
                continue
            self.text.insert("insert", f"![]({rel})\n")

    # ------------------------------------------------------------
    # paste handler
    # ------------------------------------------------------------

    def _on_paste(self, event: tk.Event) -> str | None:
        # クリップボードに画像があり note_dir が設定されていれば PNG として取り込む
        if self._note_dir is not None:
            png = get_clipboard_png()
            if png:
                try:
                    rel = self._image_store.save_pasted_png_bytes(
                        self._note_dir, png
                    )
                except OSError:
                    return None
                self.text.insert("insert", f"![]({rel})\n")
                return "break"
        return None  # 既定のテキスト貼付に任せる

    # ------------------------------------------------------------
    # OLE Drag & Drop
    # ------------------------------------------------------------

    def _on_map(self, _event: tk.Event) -> None:
        if self._drop_target is not None:
            return
        try:
            hwnd = int(self.text.winfo_id())
        except tk.TclError:
            return
        if not hwnd:
            return
        self._drop_target = DropTarget(hwnd, self._on_files_dropped)

    def _on_destroy(self, _event: tk.Event) -> None:
        if self._drop_target is not None:
            self._drop_target.revoke()
            self._drop_target = None

    def _on_files_dropped(self, paths: list[str]) -> None:
        # OLE スレッドから呼ばれる可能性に備え、Tk スレッドへスケジュール
        self.after(0, lambda: self.attach_dropped_files(paths))
