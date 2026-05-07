"""ホバー時に表示する小型プレビュー Toplevel。

C# 版 NotePreviewPopup 相当。リンク上に 500ms 滞在で表示し、
リンクから離れて 100ms 経過したら閉じる。
プレビュー側のリンクはクリック不可 (誤クリック誘発を防ぐ)。
"""

from __future__ import annotations

import sys
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


def _get_work_area(screen_w: int, screen_h: int) -> tuple[int, int, int, int]:
    """画面の作業領域 (left, top, right, bottom) を返す。

    Windows ではタスクバーを除く領域を `SystemParametersInfoW` で取得する。
    取得に失敗した場合は (0, 0, screen_w, screen_h) を返す。
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class _RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG),
                ]

            SPI_GETWORKAREA = 0x0030
            rect = _RECT()
            if ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
            ):
                return (rect.left, rect.top, rect.right, rect.bottom)
        except (OSError, AttributeError):
            pass
    return (0, 0, screen_w, screen_h)


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

        # サイズ確定後に画面端を考慮した位置決め (画面外にはみ出さないようフリップ)
        self._top.update_idletasks()
        x, y = self._compute_position(x_root, y_root)
        self._top.geometry(f"+{x}+{y}")
        self._top.deiconify()
        self._top.lift()
        self._current_target = (note_id, anchor)

    def _compute_position(self, x_root: int, y_root: int) -> tuple[int, int]:
        """ポップアップが画面内に収まる位置を返す。"""
        assert self._top is not None
        try:
            pw = self._top.winfo_reqwidth()
            ph = self._top.winfo_reqheight()
            sw = self._top.winfo_screenwidth()
            sh = self._top.winfo_screenheight()
        except tk.TclError:
            return (x_root + 16, y_root + 16)
        work = _get_work_area(sw, sh)
        return flip_position(x_root, y_root, pw, ph, work_area=work)

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


def flip_position(
    x_root: int,
    y_root: int,
    popup_w: int,
    popup_h: int,
    *,
    work_area: tuple[int, int, int, int],
    margin: int = 16,
) -> tuple[int, int]:
    """ポップアップの最終位置を決める純粋関数。

    `work_area` は (left, top, right, bottom) の作業領域 (Windows ならタスクバー除外)。
    既定はカーソル右下 +16px。作業領域からはみ出す場合は反対側へフリップ。
    領域より大きいポップアップでも領域内にクランプ。
    """
    left, top, right, bottom = work_area
    x = x_root + margin
    y = y_root + margin
    if x + popup_w > right:
        x = x_root - popup_w - margin
    if y + popup_h > bottom:
        y = y_root - popup_h - margin
    # 領域上端/左端より上/左には行かない
    x = max(left, x)
    y = max(top, y)
    return (x, y)
