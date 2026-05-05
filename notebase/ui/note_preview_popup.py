"""ホバー時に表示する小型プレビュー Toplevel。

C# 版 NotePreviewPopup 相当。リンク上に 500ms 滞在で表示し、
リンクから離れて 100ms 経過したら閉じる。
プレビュー側のリンクはクリック不可 (誤クリック誘発を防ぐ)。
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from ..markdown.md_index import extract_section
from .md_preview import MarkdownRenderer

_HOVER_SHOW_DELAY_MS = 500
_HOVER_HIDE_DELAY_MS = 100
_POPUP_WIDTH = 60   # in chars
_POPUP_HEIGHT = 16  # in lines


class NotePreviewPopup:
    """ホバープレビューを管理するシングルトン的コンポーネント。"""

    def __init__(
        self,
        master: tk.Misc,
        *,
        title_resolver: Callable[[str], str | None] | None = None,
    ) -> None:
        self._master = master
        self._title_resolver = title_resolver
        self._top: tk.Toplevel | None = None
        self._renderer: MarkdownRenderer | None = None
        self._show_after: str | None = None
        self._hide_after: str | None = None
        self._current_target: tuple[str, str | None] | None = None  # (note_id, anchor)

    # ------------------------------------------------------------
    # public
    # ------------------------------------------------------------

    def schedule_show(
        self,
        load_callback: Callable[[str], tuple[str, Path] | None],
        note_id: str,
        anchor: str | None,
        x_root: int,
        y_root: int,
    ) -> None:
        """500ms 後に表示する予約を入れる。

        load_callback(note_id) は (body, base_dir) を返す。None なら表示しない。
        """
        self._cancel_hide()
        self._cancel_show()
        target = (note_id, anchor)
        if self._current_target == target and self._top is not None:
            return
        self._show_after = self._master.after(
            _HOVER_SHOW_DELAY_MS,
            lambda: self._do_show(load_callback, note_id, anchor, x_root, y_root),
        )

    def schedule_hide(self) -> None:
        """100ms 後に閉じる予約を入れる。"""
        self._cancel_show()
        if self._top is None:
            return
        self._hide_after = self._master.after(
            _HOVER_HIDE_DELAY_MS, self._do_hide
        )

    def hide_now(self) -> None:
        self._cancel_show()
        self._cancel_hide()
        self._do_hide()

    # ------------------------------------------------------------
    # internal
    # ------------------------------------------------------------

    def _cancel_show(self) -> None:
        if self._show_after is not None:
            try:
                self._master.after_cancel(self._show_after)
            except tk.TclError:
                pass
            self._show_after = None

    def _cancel_hide(self) -> None:
        if self._hide_after is not None:
            try:
                self._master.after_cancel(self._hide_after)
            except tk.TclError:
                pass
            self._hide_after = None

    def _do_show(
        self,
        load_callback: Callable[[str], tuple[str, Path] | None],
        note_id: str,
        anchor: str | None,
        x_root: int,
        y_root: int,
    ) -> None:
        self._show_after = None
        loaded = load_callback(note_id)
        if loaded is None:
            return
        body, base_dir = loaded
        if anchor:
            body = extract_section(body, anchor)

        if self._top is None:
            self._build_popup()

        assert self._top is not None and self._renderer is not None
        self._renderer._base_dir = base_dir  # 画像解決のため
        self._renderer._title_resolver = self._title_resolver
        self._renderer.render(body)

        # 位置決め: カーソル右下少し下に
        self._top.geometry(f"+{x_root + 16}+{y_root + 16}")
        self._top.deiconify()
        self._top.lift()
        self._current_target = (note_id, anchor)

    def _build_popup(self) -> None:
        top = tk.Toplevel(self._master)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.withdraw()
        frame = ttk.Frame(top, relief="solid", borderwidth=1)
        frame.pack(fill="both", expand=True)
        text = tk.Text(
            frame,
            width=_POPUP_WIDTH,
            height=_POPUP_HEIGHT,
            wrap="word",
            font=("Helvetica", 10),
            background="#fffff0",
        )
        vsb = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.config(yscrollcommand=vsb.set)
        text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        # プレビュー内のリンクはクリック無効 (on_link_click=None)
        self._renderer = MarkdownRenderer(
            text,
            title_resolver=self._title_resolver,
            readonly=True,
        )
        self._top = top

    def _do_hide(self) -> None:
        self._hide_after = None
        if self._top is not None:
            try:
                self._top.withdraw()
            except tk.TclError:
                pass
        self._current_target = None
