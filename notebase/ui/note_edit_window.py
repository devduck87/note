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
from ..core.note_type_config import (
    BUILTIN_CONFIGS,
    NoteTypeConfig,
    get_config,
)
from ..core.schedule import Schedule, ScheduleFrequency
from ..markdown import frontmatter
from ..storage.note_repository import NoteRepository
from .markdown_text import MarkdownText
from .note_picker_dialog import NotePickerDialog

_WEEKDAY_LABELS: list[tuple[str, str]] = [
    ("mon", "月"),
    ("tue", "火"),
    ("wed", "水"),
    ("thu", "木"),
    ("fri", "金"),
    ("sat", "土"),
    ("sun", "日"),
]
_FREQUENCY_OPTIONS: list[tuple[str, ScheduleFrequency]] = [
    ("毎日", ScheduleFrequency.DAILY),
    ("毎週", ScheduleFrequency.WEEKLY),
    ("毎月", ScheduleFrequency.MONTHLY),
]


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
        type_configs: dict[NoteType, NoteTypeConfig] | None = None,
    ) -> None:
        self._master = master
        self._repo = repo
        self._meta = meta
        self._body = body
        self._is_new = is_new
        self._type_configs = type_configs or BUILTIN_CONFIGS
        self._result: NoteMeta | None = None
        self._mode: str = "form"  # "form" | "text"

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

        # モード切替バー
        mode_bar = ttk.Frame(top)
        mode_bar.pack(side="top", fill="x", padx=8, pady=(8, 0))
        ttk.Label(
            mode_bar,
            text="入力モード:",
        ).pack(side="left")
        self._mode_btn = ttk.Button(
            mode_bar, text="テキストに切替", command=self._on_toggle_mode
        )
        self._mode_btn.pack(side="left", padx=(6, 0))

        # フォームモードのコンテナ
        self._form_view = ttk.Frame(top)
        self._form_view.pack(fill="both", expand=True)

        # テキストモードのコンテナ (初期は非表示)
        self._text_view = ttk.Frame(top)
        text_label = ttk.LabelFrame(
            self._text_view,
            text="テキスト (frontmatter + 本文 Markdown)",
        )
        text_label.pack(fill="both", expand=True, padx=8, pady=8)
        self._text_widget = tk.Text(text_label, wrap="word", undo=True)
        self._text_widget.pack(fill="both", expand=True, padx=4, pady=4)

        form = ttk.Frame(self._form_view)
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
        self._type_cb = ttk.Combobox(
            form,
            textvariable=self._type_var,
            values=[label for label, _ in _TYPE_OPTIONS],
            state="readonly",
        )
        self._type_cb.grid(row=1, column=1, sticky="ew", padx=(4, 8), pady=(4, 0))
        self._type_cb.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._update_type_dependent_fields(),
        )

        self._status_label = ttk.Label(form, text="ステータス:")
        self._status_label.grid(row=1, column=2, sticky="w", pady=(4, 0))
        self._status_var = tk.StringVar(
            value=_status_label(self._meta.status)
        )
        self._status_cb = ttk.Combobox(
            form,
            textvariable=self._status_var,
            values=[label for label, _ in _STATUS_OPTIONS],
            state="readonly",
        )
        self._status_cb.grid(row=1, column=3, sticky="ew", padx=(4, 0), pady=(4, 0))

        # タグ / プロジェクト
        self._tags_label = ttk.Label(form, text="タグ (カンマ区切り):")
        self._tags_label.grid(row=2, column=0, sticky="w", pady=(4, 0))
        self._tags_var = tk.StringVar(value=", ".join(self._meta.tags or []))
        self._tags_entry = ttk.Entry(form, textvariable=self._tags_var)
        self._tags_entry.grid(row=2, column=1, sticky="ew", padx=(4, 8), pady=(4, 0))

        self._project_label = ttk.Label(form, text="プロジェクト:")
        self._project_label.grid(row=2, column=2, sticky="w", pady=(4, 0))
        self._project_var = tk.StringVar(value=self._meta.project or "")
        self._project_entry = ttk.Entry(form, textvariable=self._project_var)
        self._project_entry.grid(row=2, column=3, sticky="ew", padx=(4, 0), pady=(4, 0))

        # 期限
        self._due_label = ttk.Label(form, text="期限 (yyyy-MM-dd):")
        self._due_label.grid(row=3, column=0, sticky="w", pady=(4, 0))
        self._due_var = tk.StringVar(
            value=self._meta.due.strftime("%Y-%m-%d") if self._meta.due else ""
        )
        self._due_entry = ttk.Entry(form, textvariable=self._due_var, width=14)
        self._due_entry.grid(row=3, column=1, sticky="w", padx=(4, 0), pady=(4, 0))

        # 見積 / 実績 (タスクログ専用)
        self._estimated_label = ttk.Label(form, text="見積 (分):")
        self._estimated_var = tk.StringVar(
            value=str(self._meta.estimated_minutes) if self._meta.estimated_minutes is not None else ""
        )
        self._estimated_entry = ttk.Entry(
            form, textvariable=self._estimated_var, width=8
        )
        self._actual_label = ttk.Label(form, text="実績 (分):")
        self._actual_var = tk.StringVar(
            value=str(self._meta.actual_minutes) if self._meta.actual_minutes is not None else ""
        )
        self._actual_entry = ttk.Entry(
            form, textvariable=self._actual_var, width=8
        )
        self._estimated_label.grid(row=4, column=0, sticky="w", pady=(4, 0))
        self._estimated_entry.grid(row=4, column=1, sticky="w", padx=(4, 0), pady=(4, 0))
        self._actual_label.grid(row=4, column=2, sticky="w", pady=(4, 0))
        self._actual_entry.grid(row=4, column=3, sticky="w", padx=(4, 0), pady=(4, 0))

        # スケジュール (周期ノート専用)
        self._schedule_frame = ttk.LabelFrame(form, text="スケジュール")
        self._schedule_frame.grid(
            row=5, column=0, columnspan=4, sticky="ew", pady=(6, 0)
        )
        self._build_schedule_widgets(self._schedule_frame)

        # 本文エディタ
        editor_frame = ttk.LabelFrame(self._form_view, text="本文 (Markdown)")
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

        self._update_type_dependent_fields()

    # ------------------------------------------------------------
    # schedule / 種別連動表示
    # ------------------------------------------------------------

    def _build_schedule_widgets(self, parent: ttk.LabelFrame) -> None:
        sched = self._meta.schedule or Schedule()
        inner = ttk.Frame(parent)
        inner.pack(fill="x", padx=6, pady=6)

        # 頻度
        ttk.Label(inner, text="頻度:").grid(row=0, column=0, sticky="w")
        freq_label = next(
            (label for label, f in _FREQUENCY_OPTIONS if f == sched.frequency),
            _FREQUENCY_OPTIONS[0][0],
        )
        self._freq_var = tk.StringVar(value=freq_label)
        freq_cb = ttk.Combobox(
            inner,
            textvariable=self._freq_var,
            values=[label for label, _ in _FREQUENCY_OPTIONS],
            state="readonly",
            width=8,
        )
        freq_cb.grid(row=0, column=1, sticky="w", padx=(4, 12))
        freq_cb.bind(
            "<<ComboboxSelected>>", lambda _e: self._update_schedule_subfields()
        )

        # enabled
        self._sched_enabled_var = tk.BooleanVar(value=sched.enabled)
        ttk.Checkbutton(
            inner, text="有効", variable=self._sched_enabled_var
        ).grid(row=0, column=2, sticky="w")

        # 曜日 (weekly)
        self._weekly_frame = ttk.Frame(inner)
        ttk.Label(self._weekly_frame, text="曜日:").pack(side="left")
        days_set = set(sched.days or [])
        self._weekday_vars: dict[str, tk.BooleanVar] = {}
        for code, label in _WEEKDAY_LABELS:
            v = tk.BooleanVar(value=code in days_set)
            self._weekday_vars[code] = v
            ttk.Checkbutton(self._weekly_frame, text=label, variable=v).pack(
                side="left"
            )
        self._weekly_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # 月の何日 (monthly)
        self._monthly_frame = ttk.Frame(inner)
        ttk.Label(self._monthly_frame, text="日:").pack(side="left")
        self._day_of_month_var = tk.IntVar(value=sched.day_of_month or 1)
        ttk.Spinbox(
            self._monthly_frame,
            from_=1,
            to=31,
            textvariable=self._day_of_month_var,
            width=4,
        ).pack(side="left", padx=(4, 0))
        self._monthly_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self._update_schedule_subfields()

    def _update_schedule_subfields(self) -> None:
        freq_label = self._freq_var.get()
        freq = next(
            (f for label, f in _FREQUENCY_OPTIONS if label == freq_label),
            ScheduleFrequency.DAILY,
        )
        if freq == ScheduleFrequency.WEEKLY:
            self._weekly_frame.grid()
        else:
            self._weekly_frame.grid_remove()
        if freq == ScheduleFrequency.MONTHLY:
            self._monthly_frame.grid()
        else:
            self._monthly_frame.grid_remove()

    def _update_type_dependent_fields(self) -> None:
        type_label = self._type_var.get()
        note_type = next(
            (t for label, t in _TYPE_OPTIONS if label == type_label),
            self._meta.type,
        )
        cfg = get_config(self._type_configs, note_type)
        fields = set(cfg.fields)

        groups: dict[str, tuple] = {
            "status": (self._status_label, self._status_cb),
            "tags": (self._tags_label, self._tags_entry),
            "project": (self._project_label, self._project_entry),
            "due": (self._due_label, self._due_entry),
            "estimated_minutes": (self._estimated_label, self._estimated_entry),
            "actual_minutes": (self._actual_label, self._actual_entry),
            "schedule": (self._schedule_frame,),
        }
        for name, widgets in groups.items():
            visible = name in fields
            for w in widgets:
                if visible:
                    w.grid()
                else:
                    w.grid_remove()

    # ------------------------------------------------------------
    # mode switching
    # ------------------------------------------------------------

    def _on_toggle_mode(self) -> None:
        if self._mode == "form":
            if not self._sync_form_to_text(show_errors=True):
                return
            self._form_view.pack_forget()
            self._text_view.pack(fill="both", expand=True)
            self._mode = "text"
            self._mode_btn.configure(text="フォームに切替")
        else:
            if not self._sync_text_to_form(show_errors=True):
                return
            self._text_view.pack_forget()
            self._form_view.pack(fill="both", expand=True)
            self._mode = "form"
            self._mode_btn.configure(text="テキストに切替")

    def _sync_form_to_text(self, *, show_errors: bool) -> bool:
        """フォームの現在値 + 本文 → テキストエリアにシリアライズ。"""
        transient = self._collect_form_into_meta(show_errors=show_errors)
        if transient is None:
            return False
        body = self._editor.get()
        fm_dict = frontmatter.meta_to_dict(transient)
        text = frontmatter.combine(fm_dict, body)
        self._text_widget.delete("1.0", "end")
        self._text_widget.insert("1.0", text)
        return True

    def _sync_text_to_form(self, *, show_errors: bool) -> bool:
        """テキスト全体を parse → フォーム + 本文に反映。"""
        raw = self._text_widget.get("1.0", "end-1c")
        fm_text, body = frontmatter.split_frontmatter(raw)
        if fm_text is None:
            if show_errors:
                messagebox.showwarning(
                    "frontmatter なし",
                    "テキスト先頭に `---` で挟まれた frontmatter ブロックが必要です。",
                    parent=self._top,
                )
            return False
        fm_dict = frontmatter.parse_frontmatter(fm_text)
        # 一時 meta に重ねて parse 結果を反映 (id/created/updated は保持)
        transient = NoteMeta(
            id=self._meta.id,
            title=self._meta.title,
            type=self._meta.type,
            status=self._meta.status,
            tags=list(self._meta.tags or []),
            project=self._meta.project,
            due=self._meta.due,
            schedule=self._meta.schedule,
            instance_of=self._meta.instance_of,
            estimated_minutes=self._meta.estimated_minutes,
            actual_minutes=self._meta.actual_minutes,
            created=self._meta.created,
            updated=self._meta.updated,
        )
        frontmatter.apply_dict_to_meta(fm_dict, transient)
        # フォームに反映
        self._title_var.set(transient.title or "")
        self._type_var.set(transient.type.display_name())
        self._status_var.set(_status_label(transient.status))
        self._tags_var.set(", ".join(transient.tags or []))
        self._project_var.set(transient.project or "")
        self._due_var.set(
            transient.due.strftime("%Y-%m-%d") if transient.due else ""
        )
        self._estimated_var.set(
            str(transient.estimated_minutes)
            if transient.estimated_minutes is not None
            else ""
        )
        self._actual_var.set(
            str(transient.actual_minutes)
            if transient.actual_minutes is not None
            else ""
        )
        self._set_schedule_ui(transient.schedule)
        self._editor.set(body)
        self._update_type_dependent_fields()
        return True

    def _set_schedule_ui(self, sched: Schedule | None) -> None:
        s = sched or Schedule()
        freq_label = next(
            (label for label, f in _FREQUENCY_OPTIONS if f == s.frequency),
            _FREQUENCY_OPTIONS[0][0],
        )
        self._freq_var.set(freq_label)
        self._sched_enabled_var.set(s.enabled)
        days_set = set(s.days or [])
        for code, var in self._weekday_vars.items():
            var.set(code in days_set)
        if s.day_of_month is not None:
            self._day_of_month_var.set(s.day_of_month)
        self._update_schedule_subfields()

    def _collect_form_into_meta(
        self, *, show_errors: bool
    ) -> NoteMeta | None:
        """フォームの値を新しい NoteMeta に集めて返す (id 等は self._meta から継承)。

        検証エラーで show_errors=True なら警告ダイアログを出して None を返す。
        """
        title = self._title_var.get().strip()
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
                if show_errors:
                    messagebox.showwarning(
                        "期限の形式エラー",
                        "期限は yyyy-MM-dd 形式で入力してください。",
                        parent=self._top,
                    )
                return None

        cfg = get_config(self._type_configs, note_type)
        fields = set(cfg.fields)

        estimated: int | None = None
        actual: int | None = None
        if "estimated_minutes" in fields or "actual_minutes" in fields:
            e = _parse_optional_int(self._estimated_var.get())
            a = _parse_optional_int(self._actual_var.get())
            if e is _INVALID or a is _INVALID:
                if show_errors:
                    messagebox.showwarning(
                        "工数の形式エラー",
                        "見積 / 実績は整数 (分) で入力してください。",
                        parent=self._top,
                    )
                return None
            estimated = e if "estimated_minutes" in fields else None
            actual = a if "actual_minutes" in fields else None

        schedule: Schedule | None = None
        if "schedule" in fields:
            freq_label = self._freq_var.get()
            freq = next(
                (f for label, f in _FREQUENCY_OPTIONS if label == freq_label),
                ScheduleFrequency.DAILY,
            )
            schedule = Schedule(
                frequency=freq,
                enabled=bool(self._sched_enabled_var.get()),
            )
            if freq == ScheduleFrequency.WEEKLY:
                schedule.days = [
                    code
                    for code, _label in _WEEKDAY_LABELS
                    if self._weekday_vars[code].get()
                ]
            elif freq == ScheduleFrequency.MONTHLY:
                schedule.day_of_month = int(self._day_of_month_var.get())

        return NoteMeta(
            id=self._meta.id,
            title=title,
            type=note_type,
            status=status,
            tags=tags,
            project=project,
            due=due,
            schedule=schedule,
            instance_of=self._meta.instance_of,
            estimated_minutes=estimated,
            actual_minutes=actual,
            created=self._meta.created,
            updated=self._meta.updated,
        )

    # ------------------------------------------------------------
    # actions
    # ------------------------------------------------------------

    def _on_save(self) -> None:
        # テキストモードで保存される場合は先にフォームへ反映
        if self._mode == "text":
            if not self._sync_text_to_form(show_errors=True):
                return

        transient = self._collect_form_into_meta(show_errors=True)
        if transient is None:
            return
        if not transient.title:
            messagebox.showwarning(
                "タイトル必須", "タイトルを入力してください。", parent=self._top
            )
            return

        self._meta.title = transient.title
        self._meta.type = transient.type
        self._meta.status = transient.status
        self._meta.tags = transient.tags
        self._meta.project = transient.project
        self._meta.due = transient.due
        self._meta.estimated_minutes = transient.estimated_minutes
        self._meta.actual_minutes = transient.actual_minutes
        self._meta.schedule = transient.schedule

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


_INVALID = object()


def _parse_optional_int(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return _INVALID


_TODO_GROUP = "_todo_group"

_NEW_TYPE_OPTIONS: list[tuple[str, str]] = [
    ("備忘録", NoteType.MEMO.value),
    ("手順書", NoteType.PROCEDURE.value),
    ("やるべきこと", _TODO_GROUP),
    ("タスクログ", NoteType.LOG.value),
]


def choose_note_type(
    master: tk.Misc,
) -> NoteType | tuple[NoteType, Schedule] | None:
    """新規作成時の種別選択モーダル。

    戻り値:
        - `NoteType` のみ: 単発系 (備忘録 / 手順書 / タスクログ / やるべきこと-単発)
        - `(NoteType, Schedule)`: 周期 (やるべきこと-周期 のみ)
        - `None`: キャンセル
    """
    top = tk.Toplevel(master)
    top.title("ノート種別")
    top.transient(master.winfo_toplevel())
    top.grab_set()
    top.geometry("280x220")

    chosen: dict[str, object] = {"value": None}

    ttk.Label(top, text="作成するノートの種別を選んでください:").pack(
        padx=12, pady=(12, 6), anchor="w"
    )
    var = tk.StringVar(value=NoteType.MEMO.value)
    inner = ttk.Frame(top)
    inner.pack(padx=12, fill="x")
    for label, value in _NEW_TYPE_OPTIONS:
        ttk.Radiobutton(inner, text=label, value=value, variable=var).pack(
            anchor="w"
        )

    btn_row = ttk.Frame(top)
    btn_row.pack(fill="x", padx=12, pady=(8, 12))

    def on_ok() -> None:
        v = var.get()
        if v == _TODO_GROUP:
            sub = _choose_todo_subtype(top)
            if sub is None:
                return
            chosen["value"] = sub
        else:
            chosen["value"] = NoteType.parse(v)
        top.destroy()

    ttk.Button(btn_row, text="OK", command=on_ok).pack(side="right", padx=(4, 0))
    ttk.Button(btn_row, text="キャンセル", command=top.destroy).pack(side="right")
    top.bind("<Return>", lambda e: on_ok())
    top.bind("<Escape>", lambda e: top.destroy())

    top.wait_window()
    return chosen["value"]  # type: ignore[return-value]


def _choose_todo_subtype(
    master: tk.Misc,
) -> NoteType | tuple[NoteType, Schedule] | None:
    """『やるべきこと』の単発/周期選択ダイアログ。"""
    top = tk.Toplevel(master)
    top.title("単発 / 周期")
    top.transient(master.winfo_toplevel())
    top.grab_set()
    top.geometry("300x240")

    chosen: dict[str, object] = {"value": None}

    ttk.Label(top, text="単発のタスクですか? 周期的に繰り返すタスクですか?").pack(
        padx=12, pady=(12, 6), anchor="w"
    )

    mode_var = tk.StringVar(value="single")
    freq_var = tk.StringVar(value=_FREQUENCY_OPTIONS[1][0])  # 毎週

    inner = ttk.Frame(top)
    inner.pack(padx=12, fill="x")

    freq_frame = ttk.Frame(inner)

    def update_freq_state() -> None:
        state = "readonly" if mode_var.get() == "recurring" else "disabled"
        freq_cb.configure(state=state)

    ttk.Radiobutton(
        inner, text="単発", value="single", variable=mode_var,
        command=update_freq_state,
    ).pack(anchor="w")
    ttk.Radiobutton(
        inner, text="周期", value="recurring", variable=mode_var,
        command=update_freq_state,
    ).pack(anchor="w")

    freq_frame.pack(anchor="w", padx=(20, 0), pady=(2, 0))
    ttk.Label(freq_frame, text="頻度:").pack(side="left")
    freq_cb = ttk.Combobox(
        freq_frame,
        textvariable=freq_var,
        values=[label for label, _ in _FREQUENCY_OPTIONS],
        state="disabled",
        width=8,
    )
    freq_cb.pack(side="left", padx=(4, 0))

    btn_row = ttk.Frame(top)
    btn_row.pack(fill="x", padx=12, pady=(8, 12))

    def on_ok() -> None:
        if mode_var.get() == "single":
            chosen["value"] = NoteType.TODO
        else:
            freq = next(
                (f for label, f in _FREQUENCY_OPTIONS if label == freq_var.get()),
                ScheduleFrequency.WEEKLY,
            )
            schedule = Schedule(frequency=freq, enabled=True)
            if freq == ScheduleFrequency.WEEKLY:
                schedule.days = ["mon", "tue", "wed", "thu", "fri"]
            elif freq == ScheduleFrequency.MONTHLY:
                schedule.day_of_month = 1
            chosen["value"] = (NoteType.ROUTINE, schedule)
        top.destroy()

    ttk.Button(btn_row, text="OK", command=on_ok).pack(side="right", padx=(4, 0))
    ttk.Button(btn_row, text="キャンセル", command=top.destroy).pack(side="right")
    top.bind("<Return>", lambda e: on_ok())
    top.bind("<Escape>", lambda e: top.destroy())

    top.wait_window()
    return chosen["value"]  # type: ignore[return-value]
