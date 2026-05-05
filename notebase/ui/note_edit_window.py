"""ノート編集ウィンドウ (新規作成 + 既存編集)。

C# 版 NoteEditForm 相当。
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable

from ..core.note_meta import NoteMeta
from ..core.note_status import NoteStatus
from ..core.note_type import NoteType
from ..storage.note_repository import NoteRepository
from .markdown_text import MarkdownText
from .note_picker_dialog import NotePickerDialog


_TYPE_OPTIONS: list[tuple[str, NoteType]] = [
    (t.display_name(), t) for t in NoteType
]
_STATUS_OPTIONS: list[tuple[str, NoteStatus | None]] = [
    ("(なし)", None),
    ("active", NoteStatus.ACTIVE),
    ("done", NoteStatus.DONE),
    ("pending", NoteStatus.PENDING),
    ("archived", NoteStatus.ARCHIVED),
]


class NoteEditWindow:
    """1 ノート分の編集モーダルウィンドウ。"""

    def __init__(
        self,
        master: tk.Misc,
        repo: NoteRepository,
        meta: NoteMeta,
        body: str,
        *,
        is_new: bool,
    ) -> None:
        self._master = master
        self._repo = repo
        self._meta = meta
        self._body = body
        self._is_new = is_new
        self._result: NoteMeta | None = None

    def show(self) -> NoteMeta | None:
        self._build()
        self._top.wait_window()
        return self._result

    # ------------------------------------------------------------
    # UI
    # ------------------------------------------------------------

    def _build(self) -> None:
        top = tk.Toplevel(self._master)
        top.title("新規ノート" if self._is_new else f"編集: {self._meta.title or self._meta.id}")
        top.transient(self._master.winfo_toplevel())
        top.grab_set()
        top.geometry("760x600")
        top.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._top = top

        form = ttk.Frame(top)
        form.pack(fill="x", padx=8, pady=8)
        for col in range(4):
            form.grid_columnconfigure(col, weight=1 if col == 1 or col == 3 else 0)

        # タイトル
        ttk.Label(form, text="タイトル:").grid(row=0, column=0, sticky="w")
        self._title_var = tk.StringVar(value=self._meta.title or "")
        ttk.Entry(form, textvariable=self._title_var).grid(
            row=0, column=1, columnspan=3, sticky="ew", padx=(4, 0)
        )

        # 種別 / ステータス
        ttk.Label(form, text="種別:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._type_var = tk.StringVar(value=self._meta.type.display_name())
        type_cb = ttk.Combobox(
            form,
            textvariable=self._type_var,
            values=[label for label, _ in _TYPE_OPTIONS],
            state="readonly",
        )
        type_cb.grid(row=1, column=1, sticky="ew", padx=(4, 8), pady=(4, 0))

        ttk.Label(form, text="ステータス:").grid(row=1, column=2, sticky="w", pady=(4, 0))
        self._status_var = tk.StringVar(
            value=_status_label(self._meta.status)
        )
        ttk.Combobox(
            form,
            textvariable=self._status_var,
            values=[label for label, _ in _STATUS_OPTIONS],
            state="readonly",
        ).grid(row=1, column=3, sticky="ew", padx=(4, 0), pady=(4, 0))

        # タグ / プロジェクト
        ttk.Label(form, text="タグ (カンマ区切り):").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self._tags_var = tk.StringVar(value=", ".join(self._meta.tags or []))
        ttk.Entry(form, textvariable=self._tags_var).grid(
            row=2, column=1, sticky="ew", padx=(4, 8), pady=(4, 0)
        )

        ttk.Label(form, text="プロジェクト:").grid(row=2, column=2, sticky="w", pady=(4, 0))
        self._project_var = tk.StringVar(value=self._meta.project or "")
        ttk.Entry(form, textvariable=self._project_var).grid(
            row=2, column=3, sticky="ew", padx=(4, 0), pady=(4, 0)
        )

        # 期限
        ttk.Label(form, text="期限 (yyyy-MM-dd):").grid(row=3, column=0, sticky="w", pady=(4, 0))
        self._due_var = tk.StringVar(
            value=self._meta.due.strftime("%Y-%m-%d") if self._meta.due else ""
        )
        ttk.Entry(form, textvariable=self._due_var, width=14).grid(
            row=3, column=1, sticky="w", padx=(4, 0), pady=(4, 0)
        )

        # 本文エディタ
        editor_frame = ttk.LabelFrame(top, text="本文 (Markdown)")
        editor_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._editor = MarkdownText(editor_frame)
        self._editor.pack(fill="both", expand=True, padx=4, pady=4)
        self._editor.set(self._body)
        self._editor.note_dir = self._repo.get_note_dir(self._meta.id)
        self._editor.text.bind("<Control-l>", self._on_open_picker)
        self._editor.text.bind("<Control-L>", self._on_open_picker)

        # ボタン
        btn_row = ttk.Frame(top)
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btn_row, text="保存", command=self._on_save).pack(
            side="right", padx=(4, 0)
        )
        ttk.Button(btn_row, text="キャンセル", command=self._on_cancel).pack(side="right")
        ttk.Button(
            btn_row, text="画像を追加…", command=self._on_add_image
        ).pack(side="left")
        top.bind("<Control-s>", lambda e: self._on_save())

    # ------------------------------------------------------------
    # actions
    # ------------------------------------------------------------

    def _on_save(self) -> None:
        title = self._title_var.get().strip()
        if not title:
            messagebox.showwarning(
                "タイトル必須", "タイトルを入力してください。", parent=self._top
            )
            return

        type_label = self._type_var.get()
        note_type = next(
            (t for label, t in _TYPE_OPTIONS if label == type_label),
            self._meta.type,
        )

        status_label = self._status_var.get()
        status = next(
            (s for label, s in _STATUS_OPTIONS if label == status_label),
            None,
        )

        tags_raw = self._tags_var.get().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        project = self._project_var.get().strip() or None

        due_raw = self._due_var.get().strip()
        due: datetime | None = None
        if due_raw:
            try:
                due = datetime.strptime(due_raw, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning(
                    "期限の形式エラー",
                    "期限は yyyy-MM-dd 形式で入力してください。",
                    parent=self._top,
                )
                return

        self._meta.title = title
        self._meta.type = note_type
        self._meta.status = status
        self._meta.tags = tags
        self._meta.project = project
        self._meta.due = due

        body = self._editor.get()
        try:
            if self._is_new:
                saved = self._repo.save_new(self._meta, body)
            else:
                saved = self._repo.save_existing(self._meta, body)
        except OSError as exc:
            messagebox.showerror(
                "保存エラー", f"保存に失敗しました: {exc}", parent=self._top
            )
            return

        self._result = saved
        self._top.destroy()

    def _on_cancel(self) -> None:
        if self._is_new:
            # 新規ドラフトはキャンセルで trash 行き
            self._repo.move_to_trash(self._meta.id)
        self._result = None
        self._top.destroy()

    def _on_open_picker(self, event: tk.Event) -> str:
        dlg = NotePickerDialog(
            self._top, self._repo, exclude_id=self._meta.id
        )
        snippet = dlg.show()
        if snippet:
            self._editor.insert_at_cursor(snippet)
        return "break"

    def _on_add_image(self) -> None:
        from tkinter import filedialog

        paths = filedialog.askopenfilenames(
            parent=self._top,
            title="画像を選択",
            filetypes=[
                ("画像", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("すべて", "*.*"),
            ],
        )
        if not paths:
            return
        self._editor.attach_dropped_files(list(paths))


def _status_label(s: NoteStatus | None) -> str:
    return next((label for label, st in _STATUS_OPTIONS if st == s), "(なし)")


def choose_note_type(master: tk.Misc) -> NoteType | None:
    """新規作成時の種別選択モーダル。OK で選んだ種別、キャンセルで None。"""
    top = tk.Toplevel(master)
    top.title("ノート種別")
    top.transient(master.winfo_toplevel())
    top.grab_set()
    top.geometry("280x260")

    chosen: dict[str, NoteType | None] = {"value": None}

    ttk.Label(top, text="作成するノートの種別を選んでください:").pack(
        padx=12, pady=(12, 6), anchor="w"
    )
    var = tk.StringVar(value=NoteType.MEMO.value)
    inner = ttk.Frame(top)
    inner.pack(padx=12, fill="x")
    for t in NoteType:
        ttk.Radiobutton(
            inner, text=t.display_name(), value=t.value, variable=var
        ).pack(anchor="w")

    btn_row = ttk.Frame(top)
    btn_row.pack(fill="x", padx=12, pady=(8, 12))

    def on_ok() -> None:
        chosen["value"] = NoteType.parse(var.get())
        top.destroy()

    ttk.Button(btn_row, text="OK", command=on_ok).pack(side="right", padx=(4, 0))
    ttk.Button(btn_row, text="キャンセル", command=top.destroy).pack(side="right")
    top.bind("<Return>", lambda e: on_ok())
    top.bind("<Escape>", lambda e: top.destroy())

    top.wait_window()
    return chosen["value"]
