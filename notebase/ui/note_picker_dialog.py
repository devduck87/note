"""他ノートのブロックを選んで [[Title#anchor]] スニペットを返すモーダルダイアログ。

C# 版 NotePickerDialog 相当。Ctrl+L から開かれる。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..core.note_meta import NoteMeta
from ..markdown.md_index import BlockInfo, BlockKind, extract_blocks
from ..storage.note_repository import NoteRepository


class NotePickerDialog:
    """Markdown スニペットを 1 つ返すモーダルダイアログ。"""

    def __init__(
        self,
        master: tk.Misc,
        repo: NoteRepository,
        *,
        exclude_id: str | None = None,
    ) -> None:
        self._master = master
        self._repo = repo
        self._exclude_id = exclude_id
        self._result: str | None = None
        self._all_metas: list[NoteMeta] = []
        self._filtered_metas: list[NoteMeta] = []
        self._current_blocks: list[BlockInfo] = []

    def show(self) -> str | None:
        self._build()
        self._populate_notes()
        self._top.wait_window()
        return self._result

    # ------------------------------------------------------------
    # construction
    # ------------------------------------------------------------

    def _build(self) -> None:
        top = tk.Toplevel(self._master)
        top.title("ノート/ブロックを選択")
        top.transient(self._master.winfo_toplevel())
        top.grab_set()
        top.geometry("640x520")
        self._top = top

        # 上部: 検索 + ノート一覧
        upper = ttk.Frame(top)
        upper.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        search_row = ttk.Frame(upper)
        search_row.pack(fill="x")
        ttk.Label(search_row, text="検索:").pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(search_row, textvariable=self._search_var).pack(
            side="left", fill="x", expand=True, padx=(4, 0)
        )

        notes_frame = ttk.Frame(upper)
        notes_frame.pack(fill="both", expand=True, pady=(4, 0))
        self._notes_tree = ttk.Treeview(
            notes_frame,
            columns=("title", "type", "updated"),
            show="headings",
            height=8,
        )
        self._notes_tree.heading("title", text="タイトル")
        self._notes_tree.heading("type", text="種別")
        self._notes_tree.heading("updated", text="更新")
        self._notes_tree.column("title", width=320)
        self._notes_tree.column("type", width=80, anchor="w")
        self._notes_tree.column("updated", width=140, anchor="w")
        self._notes_tree.pack(side="left", fill="both", expand=True)
        notes_vsb = ttk.Scrollbar(
            notes_frame, orient="vertical", command=self._notes_tree.yview
        )
        notes_vsb.pack(side="right", fill="y")
        self._notes_tree.config(yscrollcommand=notes_vsb.set)
        self._notes_tree.bind("<<TreeviewSelect>>", self._on_note_selected)

        # 下部: ブロック一覧
        lower = ttk.Frame(top)
        lower.pack(fill="both", expand=True, padx=8, pady=4)
        self._blocks_tree = ttk.Treeview(
            lower,
            columns=("kind", "text", "id"),
            show="headings",
            height=8,
        )
        self._blocks_tree.heading("kind", text="種類")
        self._blocks_tree.heading("text", text="テキスト")
        self._blocks_tree.heading("id", text="ID")
        self._blocks_tree.column("kind", width=70, anchor="w")
        self._blocks_tree.column("text", width=420)
        self._blocks_tree.column("id", width=80, anchor="w")
        self._blocks_tree.pack(side="left", fill="both", expand=True)
        blocks_vsb = ttk.Scrollbar(
            lower, orient="vertical", command=self._blocks_tree.yview
        )
        blocks_vsb.pack(side="right", fill="y")
        self._blocks_tree.config(yscrollcommand=blocks_vsb.set)
        self._blocks_tree.bind("<Double-Button-1>", lambda e: self._confirm())
        self._blocks_tree.bind("<Return>", lambda e: self._confirm())

        # ボタン
        btn_row = ttk.Frame(top)
        btn_row.pack(fill="x", padx=8, pady=(4, 8))
        ttk.Button(btn_row, text="挿入", command=self._confirm).pack(
            side="right", padx=(4, 0)
        )
        ttk.Button(btn_row, text="キャンセル", command=top.destroy).pack(side="right")
        top.bind("<Escape>", lambda e: top.destroy())

    # ------------------------------------------------------------
    # data
    # ------------------------------------------------------------

    def _populate_notes(self) -> None:
        self._all_metas = [
            m for m in self._repo.load_all() if m.id != self._exclude_id
        ]
        # 更新日時降順
        self._all_metas.sort(key=lambda m: m.updated, reverse=True)
        self._apply_filter()

    def _apply_filter(self) -> None:
        keyword = self._search_var.get().strip().lower() if hasattr(self, "_search_var") else ""
        if keyword:
            self._filtered_metas = [
                m
                for m in self._all_metas
                if keyword in (m.title or "").lower()
                or any(keyword in (t or "").lower() for t in m.tags)
            ]
        else:
            self._filtered_metas = list(self._all_metas)
        self._notes_tree.delete(*self._notes_tree.get_children())
        for m in self._filtered_metas:
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
        # ブロック側はクリア
        self._blocks_tree.delete(*self._blocks_tree.get_children())
        self._current_blocks = []

    def _on_note_selected(self, _event: tk.Event) -> None:
        sel = self._notes_tree.selection()
        if not sel:
            return
        note_id = sel[0]
        try:
            _meta, body = self._repo.load(note_id)
        except OSError:
            return
        self._current_blocks = extract_blocks(body)
        self._blocks_tree.delete(*self._blocks_tree.get_children())
        for idx, b in enumerate(self._current_blocks):
            indent = "  " * max(0, b.context_level - 1)
            marker = _block_marker(b)
            text = (b.text or "")[:200]
            self._blocks_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(_kind_label(b.kind), f"{indent}{marker}{text}", b.existing_id or ""),
            )

    def _confirm(self) -> None:
        note_sel = self._notes_tree.selection()
        block_sel = self._blocks_tree.selection()
        if not note_sel or not block_sel:
            return
        note_id = note_sel[0]
        meta = next((m for m in self._all_metas if m.id == note_id), None)
        if meta is None:
            return
        b = self._current_blocks[int(block_sel[0])]
        title = meta.title or note_id

        if b.kind == BlockKind.HEADING:
            anchor = b.heading_slug
            self._result = f"[[{title}#{anchor}]]"
        else:
            existing = b.existing_id
            if not existing:
                existing = self._repo.ensure_block_id(note_id, b.line_end)
            if existing:
                self._result = f"[[{title}#^{existing}]]"
            else:
                # 空行など ID 付与不可の場合はノートトップへのリンクで代用
                self._result = f"[[{title}]]"

        self._top.destroy()


def _kind_label(k: BlockKind) -> str:
    return {
        BlockKind.HEADING: "見出し",
        BlockKind.PARAGRAPH: "段落",
        BlockKind.LIST_ITEM: "リスト",
        BlockKind.TASK_ITEM: "タスク",
        BlockKind.ORDERED_ITEM: "番号付",
    }.get(k, str(k))


def _block_marker(b: BlockInfo) -> str:
    if b.kind == BlockKind.HEADING:
        return "#" * b.level + " "
    if b.kind == BlockKind.LIST_ITEM:
        return "• "
    if b.kind == BlockKind.TASK_ITEM:
        return "☐ "
    if b.kind == BlockKind.ORDERED_ITEM:
        return "1. "
    return ""
