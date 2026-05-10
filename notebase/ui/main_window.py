"""メインウィンドウ。

C# 版 MainForm 相当: ノート一覧 + プレビュー + プロパティパネル + ナビゲーション。
編集は note_edit_window.NoteEditWindow に委譲する。
"""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

_TASK_TOGGLE_RE = re.compile(r"^(\s*[-*+]\s+\[)([ xX])(\].*)$")


def _toggle_task_line(line: str) -> str | None:
    """`- [ ] ...` ↔ `- [x] ...` を反転する。タスク行でなければ None。"""
    m = _TASK_TOGGLE_RE.match(line)
    if not m:
        return None
    cur = m.group(2)
    new = "x" if cur == " " else " "
    return m.group(1) + new + m.group(3)

from ..core.note_meta import NoteMeta
from ..core.note_type import NoteType
from ..core.note_type_config import get_config, load_configs
from ..markdown.summary import extract as extract_summary
from ..storage.app_paths import AppPaths
from ..storage.note_repository import NoteRepository
from ..storage.trash_service import TrashService
from .daily_plan_dialog import DailyPlanDialog
from .md_preview import LinkInfo, MarkdownRenderer
from .note_edit_window import NoteEditWindow, choose_note_type
from .note_preview_popup import NotePreviewPopup


class MainWindow:
    def __init__(self, root: tk.Tk, paths: AppPaths) -> None:
        self._root = root
        self._paths = paths
        paths.ensure_layout()
        self._trash = TrashService(paths)
        self._repo = NoteRepository(paths, self._trash)
        self._type_configs = load_configs(paths.note_types_config)

        self._all_metas: list[NoteMeta] = []
        self._current_id: str | None = None
        self._back_stack: list[str] = []
        self._title_index: dict[str, str] = {}  # title -> note_id
        self._renderer: MarkdownRenderer | None = None
        self._popup: NotePreviewPopup | None = None

        self._build()
        self._reload_notes()

    # ------------------------------------------------------------
    # construction
    # ------------------------------------------------------------

    def _build(self) -> None:
        root = self._root
        root.title("NoteBase (Python)")
        root.geometry("1100x720")

        # ツールバー
        toolbar = ttk.Frame(root)
        toolbar.pack(side="top", fill="x")

        self._back_btn = ttk.Button(toolbar, text="◀ 戻る", command=self._on_back)
        self._back_btn.pack(side="left", padx=(4, 2), pady=4)
        self._back_btn.state(["disabled"])

        ttk.Label(toolbar, text="検索:").pack(side="left", padx=(8, 2))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_search())
        ttk.Entry(toolbar, textvariable=self._search_var, width=28).pack(
            side="left", padx=(0, 8)
        )

        ttk.Button(toolbar, text="新規 (Ctrl+N)", command=self._on_new).pack(
            side="left", padx=2
        )
        ttk.Button(toolbar, text="編集 (Ctrl+E)", command=self._on_edit).pack(
            side="left", padx=2
        )
        self._start_instance_btn = ttk.Button(
            toolbar, text="実施を開始", command=self._on_start_instance
        )
        self._start_instance_btn.pack(side="left", padx=2)
        self._start_instance_btn.state(["disabled"])
        ttk.Button(
            toolbar, text="本日のプラン…", command=self._on_open_daily_plan
        ).pack(side="left", padx=2)
        ttk.Button(toolbar, text="ゴミ箱へ", command=self._on_delete).pack(
            side="left", padx=2
        )

        # 本体: 左ノート一覧 / 右プレビュー
        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(side="top", fill="both", expand=True)

        # 左
        left = ttk.Frame(body)
        body.add(left, weight=1)
        self._notes_tree = ttk.Treeview(
            left,
            columns=("title", "type", "updated"),
            show="headings",
        )
        self._notes_tree.heading("title", text="タイトル")
        self._notes_tree.heading("type", text="種別")
        self._notes_tree.heading("updated", text="更新")
        self._notes_tree.column("title", width=240)
        self._notes_tree.column("type", width=80, anchor="w")
        self._notes_tree.column("updated", width=120, anchor="w")
        self._notes_tree.pack(side="left", fill="both", expand=True)
        left_vsb = ttk.Scrollbar(
            left, orient="vertical", command=self._notes_tree.yview
        )
        left_vsb.pack(side="right", fill="y")
        self._notes_tree.config(yscrollcommand=left_vsb.set)
        self._notes_tree.bind("<<TreeviewSelect>>", self._on_note_selected)
        self._notes_tree.bind("<Double-Button-1>", lambda e: self._on_edit())

        # 右
        right = ttk.Frame(body)
        body.add(right, weight=3)

        # 右上: プロパティパネル
        prop_frame = ttk.LabelFrame(right, text="プロパティ")
        prop_frame.pack(side="top", fill="x", padx=4, pady=(4, 2))
        for col in range(4):
            prop_frame.grid_columnconfigure(col, weight=1 if col % 2 == 1 else 0)

        self._prop_title = self._add_prop(prop_frame, 0, 0, "タイトル:")
        self._prop_type = self._add_prop(prop_frame, 0, 2, "種別:")
        self._prop_status = self._add_prop(prop_frame, 1, 0, "ステータス:")
        self._prop_tags = self._add_prop(prop_frame, 1, 2, "タグ:")
        self._prop_project = self._add_prop(prop_frame, 2, 0, "プロジェクト:")
        self._prop_due = self._add_prop(prop_frame, 2, 2, "期限:")
        self._prop_created = self._add_prop(prop_frame, 3, 0, "作成:")
        self._prop_updated = self._add_prop(prop_frame, 3, 2, "更新:")

        # 右下: プレビュー
        preview_frame = ttk.LabelFrame(right, text="プレビュー")
        preview_frame.pack(side="top", fill="both", expand=True, padx=4, pady=(0, 4))
        preview_inner = ttk.Frame(preview_frame)
        preview_inner.pack(fill="both", expand=True)
        self._preview_text = tk.Text(
            preview_inner,
            wrap="word",
            font=("Helvetica", 10),
            state="disabled",
            takefocus=0,
        )
        prev_vsb = ttk.Scrollbar(
            preview_inner, orient="vertical", command=self._preview_text.yview
        )
        self._preview_text.config(yscrollcommand=prev_vsb.set)
        self._preview_text.pack(side="left", fill="both", expand=True)
        prev_vsb.pack(side="right", fill="y")

        # キーバインド
        root.bind("<Control-n>", lambda e: self._on_new())
        root.bind("<Control-N>", lambda e: self._on_new())
        root.bind("<Control-e>", lambda e: self._on_edit())
        root.bind("<Control-E>", lambda e: self._on_edit())
        root.bind("<Alt-Left>", lambda e: self._on_back())

    def _add_prop(
        self, parent: ttk.LabelFrame, row: int, col: int, label: str
    ) -> ttk.Label:
        ttk.Label(parent, text=label).grid(
            row=row, column=col, sticky="w", padx=4, pady=2
        )
        value_label = ttk.Label(parent, text="-", anchor="w")
        value_label.grid(row=row, column=col + 1, sticky="ew", padx=4, pady=2)
        return value_label

    # ------------------------------------------------------------
    # data
    # ------------------------------------------------------------

    def _reload_notes(self, select_id: str | None = None) -> None:
        self._all_metas = list(self._repo.load_all())
        self._all_metas.sort(key=lambda m: m.updated, reverse=True)
        self._title_index = {m.title: m.id for m in self._all_metas if m.title}
        self._apply_search(select_id=select_id)

    def _apply_search(self, select_id: str | None = None) -> None:
        keyword = self._search_var.get().strip().lower()
        items = self._all_metas
        if keyword:
            items = [
                m
                for m in items
                if keyword in (m.title or "").lower()
                or any(keyword in (t or "").lower() for t in m.tags)
            ]
        self._notes_tree.delete(*self._notes_tree.get_children())
        for m in items:
            self._notes_tree.insert(
                "",
                "end",
                iid=m.id,
                values=(
                    m.title or "(無題)",
                    m.type.display_name(),
                    m.updated.strftime("%Y-%m-%d %H:%M"),
                ),
            )
        if select_id and self._notes_tree.exists(select_id):
            self._notes_tree.selection_set(select_id)
            self._notes_tree.see(select_id)
        elif items:
            first = items[0].id
            self._notes_tree.selection_set(first)
            self._notes_tree.see(first)
        else:
            self._show_note(None)

    # ------------------------------------------------------------
    # selection & navigation
    # ------------------------------------------------------------

    def _on_note_selected(self, _event: tk.Event) -> None:
        sel = self._notes_tree.selection()
        if not sel:
            return
        self._navigate_to(sel[0], push_history=True)

    def _navigate_to(self, note_id: str, *, push_history: bool) -> None:
        if self._current_id == note_id:
            return
        if push_history and self._current_id is not None:
            self._back_stack.append(self._current_id)
            self._back_btn.state(["!disabled"])
        self._current_id = note_id
        self._show_note(note_id)

    def _on_back(self) -> None:
        if not self._back_stack:
            return
        valid_ids = {m.id for m in self._all_metas}
        prev = self._back_stack.pop()
        # 削除済みは飛ばす
        while prev not in valid_ids and self._back_stack:
            prev = self._back_stack.pop()
        if not self._back_stack:
            self._back_btn.state(["disabled"])
        if prev not in valid_ids:
            return
        self._current_id = None
        if self._notes_tree.exists(prev):
            self._notes_tree.selection_set(prev)
            self._notes_tree.see(prev)

    def _show_note(self, note_id: str | None) -> None:
        if note_id is None:
            self._set_props(None)
            self._render_preview("")
            return
        try:
            meta, body = self._repo.load(note_id)
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "読み込みエラー", f"{note_id}: {exc}", parent=self._root
            )
            return
        self._set_props(meta)
        self._render_preview(body, base_dir=self._paths.note_dir(note_id))

    def _set_props(self, meta: NoteMeta | None) -> None:
        if meta is None:
            for lab in (
                self._prop_title,
                self._prop_type,
                self._prop_status,
                self._prop_tags,
                self._prop_project,
                self._prop_due,
                self._prop_created,
                self._prop_updated,
            ):
                lab.config(text="-")
            self._start_instance_btn.state(["disabled"])
            return
        self._prop_title.config(text=meta.title or "(無題)")
        self._prop_type.config(text=meta.type.display_name())
        self._prop_status.config(text=meta.status.to_wire() if meta.status else "-")
        self._prop_tags.config(text=", ".join(meta.tags) if meta.tags else "-")
        self._prop_project.config(text=meta.project or "-")
        self._prop_due.config(
            text=meta.due.strftime("%Y-%m-%d") if meta.due else "-"
        )
        self._prop_created.config(
            text=meta.created.strftime("%Y-%m-%d %H:%M")
        )
        self._prop_updated.config(
            text=meta.updated.strftime("%Y-%m-%d %H:%M")
        )
        if meta.type == NoteType.PROCEDURE:
            self._start_instance_btn.state(["!disabled"])
        else:
            self._start_instance_btn.state(["disabled"])

    def _render_preview(self, body: str, *, base_dir: Path | None = None) -> None:
        if self._renderer is None:
            self._renderer = MarkdownRenderer(
                self._preview_text,
                on_link_click=self._on_preview_link_click,
                on_link_hover=self._on_preview_link_hover,
                on_link_leave=self._on_preview_link_leave,
                title_resolver=self._resolve_title,
                base_dir=base_dir,
                readonly=True,
                on_task_toggle=self._on_task_toggle,
                on_timebox_change=self._on_timebox_change,
            )
        else:
            self._renderer._base_dir = base_dir
        self._renderer.render(body)

    def _on_timebox_change(
        self,
        start_line: int,
        end_line: int,
        start_time: str,
        items: list,
    ) -> None:
        """TimeboxCanvas からのリサイズ/並べ替え結果を Markdown へ反映する。"""
        if self._current_id is None:
            return
        from ..planning.timebox_format import render_timebox_lines

        try:
            meta, body = self._repo.load(self._current_id)
        except (OSError, ValueError):
            return
        normalized = (body or "").replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        if start_line < 0 or end_line >= len(lines) or start_line > end_line:
            return
        new_lines = render_timebox_lines(items, start_time)
        lines[start_line : end_line + 1] = new_lines
        new_body = "\r\n".join(lines)
        try:
            self._repo.save_existing(meta, new_body)
        except OSError:
            return
        self._render_preview(
            new_body, base_dir=self._paths.note_dir(self._current_id)
        )
        prev_id = self._current_id
        self._reload_notes(select_id=prev_id)
        self._current_id = prev_id

    def _on_task_toggle(self, source_line: int) -> None:
        """プレビュー上のチェックボックスをクリックされたとき: 該当行を反転して保存。"""
        if self._current_id is None:
            return
        try:
            meta, body = self._repo.load(self._current_id)
        except (OSError, ValueError):
            return
        normalized = (body or "").replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        if source_line < 0 or source_line >= len(lines):
            return
        new_line = _toggle_task_line(lines[source_line])
        if new_line is None:
            return
        lines[source_line] = new_line
        new_body = "\r\n".join(lines)
        try:
            self._repo.save_existing(meta, new_body)
        except OSError:
            return
        # プレビュー再描画 + 一覧の更新日時も refresh
        self._render_preview(
            new_body, base_dir=self._paths.note_dir(self._current_id)
        )
        # 一覧の updated 列を更新するため軽い再ロード
        prev_id = self._current_id
        self._reload_notes(select_id=prev_id)
        self._current_id = prev_id

    # ------------------------------------------------------------
    # link handling
    # ------------------------------------------------------------

    def _resolve_title(self, title: str) -> str | None:
        return self._title_index.get(title)

    def _on_preview_link_click(self, info: LinkInfo) -> None:
        # ノートリンクなら遷移、外部 URL なら webbrowser へ
        if info.target_note_id and info.target_note_id in self._title_index.values():
            self._navigate_to(info.target_note_id, push_history=True)
            if info.anchor and self._renderer:
                self._renderer.scroll_to_anchor(info.anchor)
            return
        if info.raw_url.startswith("#"):
            if self._renderer and info.anchor:
                self._renderer.scroll_to_anchor(info.anchor)
            return
        # 外部リンク
        import webbrowser

        webbrowser.open(info.raw_url)

    def _on_preview_link_hover(self, info: LinkInfo, event: tk.Event) -> None:
        if not info.target_note_id:
            return
        if self._popup is None:
            self._popup = NotePreviewPopup(
                self._root, title_resolver=self._resolve_title
            )
        self._popup.schedule_show(
            self._load_note_for_popup,
            info.target_note_id,
            info.anchor,
            event.x_root,
            event.y_root,
        )

    def _on_preview_link_leave(self, info: LinkInfo, event: tk.Event) -> None:
        if self._popup is not None:
            self._popup.schedule_hide()

    def _load_note_for_popup(
        self, note_id: str
    ) -> tuple[str, Path] | None:
        try:
            _meta, body = self._repo.load(note_id)
        except (OSError, ValueError):
            return None
        return body, self._paths.note_dir(note_id)

    # ------------------------------------------------------------
    # actions
    # ------------------------------------------------------------

    def _on_new(self) -> None:
        result = choose_note_type(self._root)
        if result is None:
            return
        if isinstance(result, tuple):
            note_type, schedule = result
        else:
            note_type, schedule = result, None
        config = get_config(self._type_configs, note_type)
        meta = self._repo.create_draft(
            note_type, schedule=schedule, config=config
        )
        # ドラフトは title 空、本文は config の body_template から開始。
        win = NoteEditWindow(
            self._root,
            self._repo,
            meta,
            config.body_template,
            is_new=True,
            type_configs=self._type_configs,
        )
        saved = win.show()
        if saved is not None:
            self._reload_notes(select_id=saved.id)

    def _on_edit(self) -> None:
        if self._current_id is None:
            return
        try:
            meta, body = self._repo.load(self._current_id)
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "読み込みエラー", f"{self._current_id}: {exc}", parent=self._root
            )
            return
        win = NoteEditWindow(
            self._root, self._repo, meta, body, is_new=False,
            type_configs=self._type_configs,
        )
        saved = win.show()
        if saved is not None:
            self._current_id = None
            self._reload_notes(select_id=saved.id)

    def _on_delete(self) -> None:
        if self._current_id is None:
            return
        if not messagebox.askyesno(
            "ゴミ箱へ移動",
            f"このノートをゴミ箱へ移動しますか?\n  {self._current_id}",
            parent=self._root,
        ):
            return
        self._repo.move_to_trash(self._current_id)
        self._current_id = None
        self._reload_notes()

    def _on_start_instance(self) -> None:
        if self._current_id is None:
            return
        try:
            template_meta, _body = self._repo.load(self._current_id)
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "読み込みエラー", f"{self._current_id}: {exc}", parent=self._root
            )
            return
        if template_meta.type != NoteType.PROCEDURE:
            return
        try:
            meta, body = self._repo.create_instance(self._current_id)
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "実施記録の作成に失敗", str(exc), parent=self._root
            )
            return
        win = NoteEditWindow(
            self._root, self._repo, meta, body, is_new=True,
            type_configs=self._type_configs,
        )
        saved = win.show()
        if saved is not None:
            self._current_id = None
            self._reload_notes(select_id=saved.id)

    def _on_open_daily_plan(self) -> None:
        dlg = DailyPlanDialog(self._root, self._repo)
        new_id = dlg.show()
        if new_id is not None:
            self._current_id = None
            self._reload_notes(select_id=new_id)
