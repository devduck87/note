"""本日のプラン作成ダイアログ。

候補 (今日該当 routine + 期限が今日以前の todo タスク) を一覧化し、
ユーザがチェックと所要分を編集して `type=daily` ノートとして保存する。
"""

from __future__ import annotations

import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, simpledialog, ttk
from typing import Callable

from ..core.note_type import NoteType
from ..planning.daily_planner import (
    DEFAULT_DURATION_MIN,
    DEFAULT_START_TIME,
    PlanItem,
    candidates_for,
    render_markdown,
)
from ..storage.note_repository import NoteRepository
from .note_picker_dialog import NotePickerDialog


class DailyPlanDialog:
    """本日プラン作成モーダル。show() で新ノート ID を返す (キャンセル時 None)。"""

    def __init__(self, master: tk.Misc, repo: NoteRepository) -> None:
        self._master = master
        self._repo = repo
        self._items: list[PlanItem] = []
        self._checked: list[bool] = []  # _items と並列、True ならプラン入り
        self._result: str | None = None

    def show(self) -> str | None:
        self._build()
        self._reload_candidates()
        self._top.wait_window()
        return self._result

    # ------------------------------------------------------------
    # construction
    # ------------------------------------------------------------

    def _build(self) -> None:
        top = tk.Toplevel(self._master)
        top.title("本日のプラン")
        top.transient(self._master.winfo_toplevel())
        top.grab_set()
        top.geometry("720x520")
        self._top = top

        # 上段: 対象日 / 開始時刻 / 再読込
        head = ttk.Frame(top)
        head.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Label(head, text="対象日:").pack(side="left")
        self._target_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(head, textvariable=self._target_var, width=12).pack(
            side="left", padx=(4, 12)
        )
        ttk.Label(head, text="開始:").pack(side="left")
        self._start_var = tk.StringVar(value=DEFAULT_START_TIME)
        ttk.Entry(head, textvariable=self._start_var, width=8).pack(
            side="left", padx=(4, 12)
        )
        ttk.Button(head, text="候補を再読込", command=self._reload_candidates).pack(
            side="left"
        )

        # 中段: ツリー
        body = ttk.Frame(top)
        body.pack(fill="both", expand=True, padx=8, pady=4)
        self._tree = ttk.Treeview(
            body,
            columns=("check", "kind", "text", "min"),
            show="headings",
            selectmode="browse",
        )
        self._tree.heading("check", text="✓")
        self._tree.heading("kind", text="種類")
        self._tree.heading("text", text="内容")
        self._tree.heading("min", text="所要 (分)")
        self._tree.column("check", width=36, anchor="center", stretch=False)
        self._tree.column("kind", width=70, anchor="w", stretch=False)
        self._tree.column("text", width=440)
        self._tree.column("min", width=80, anchor="e", stretch=False)
        self._tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        vsb.pack(side="right", fill="y")
        self._tree.config(yscrollcommand=vsb.set)
        self._tree.bind("<Button-1>", self._on_tree_click)
        self._tree.bind("<Double-Button-1>", self._on_tree_double_click)

        hint = ttk.Label(
            top,
            text="✓列をクリックで選択切替 / 所要分はダブルクリックで編集",
            foreground="#666666",
        )
        hint.pack(fill="x", padx=8)

        # 下段: ボタン
        btns = ttk.Frame(top)
        btns.pack(fill="x", padx=8, pady=(4, 8))
        ttk.Button(btns, text="ノートから追加…", command=self._on_add_from_picker).pack(
            side="left"
        )
        ttk.Button(btns, text="手動で追加…", command=self._on_add_manual).pack(
            side="left", padx=(4, 0)
        )
        ttk.Button(btns, text="作成", command=self._on_create).pack(
            side="right", padx=(4, 0)
        )
        ttk.Button(btns, text="キャンセル", command=self._top.destroy).pack(
            side="right"
        )
        top.bind("<Escape>", lambda e: self._top.destroy())

    # ------------------------------------------------------------
    # data
    # ------------------------------------------------------------

    def _parse_target(self) -> date | None:
        s = self._target_var.get().strip()
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning(
                "対象日の形式エラー",
                "対象日は yyyy-mm-dd 形式で入力してください。",
                parent=self._top,
            )
            return None

    def _reload_candidates(self) -> None:
        target = self._parse_target()
        if target is None:
            return
        self._items = candidates_for(self._repo, target)
        self._checked = [True] * len(self._items)  # 既定で全チェック
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for idx, item in enumerate(self._items):
            self._tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    "✓" if self._checked[idx] else "",
                    _kind_label(item.kind),
                    _display_text(item),
                    item.duration_min,
                ),
            )

    # ------------------------------------------------------------
    # events
    # ------------------------------------------------------------

    def _on_tree_click(self, event: tk.Event) -> None:
        # ✓列クリックで toggle
        if self._tree.identify_region(event.x, event.y) != "cell":
            return
        col = self._tree.identify_column(event.x)
        if col != "#1":
            return
        row = self._tree.identify_row(event.y)
        if not row:
            return
        idx = int(row)
        self._checked[idx] = not self._checked[idx]
        self._tree.set(row, "check", "✓" if self._checked[idx] else "")

    def _on_tree_double_click(self, event: tk.Event) -> None:
        if self._tree.identify_region(event.x, event.y) != "cell":
            return
        col = self._tree.identify_column(event.x)
        row = self._tree.identify_row(event.y)
        if not row:
            return
        idx = int(row)
        if col == "#4":
            new = simpledialog.askinteger(
                "所要分",
                "このタスクの所要分を入力 (1〜480):",
                parent=self._top,
                minvalue=1,
                maxvalue=480,
                initialvalue=self._items[idx].duration_min,
            )
            if new is not None:
                self._items[idx].duration_min = int(new)
                self._tree.set(row, "min", new)
        elif col == "#3":
            new = simpledialog.askstring(
                "内容を編集",
                "内容を入力:",
                parent=self._top,
                initialvalue=self._items[idx].text,
            )
            if new:
                self._items[idx].text = new.strip()
                self._tree.set(row, "text", _display_text(self._items[idx]))

    def _on_add_manual(self) -> None:
        text = simpledialog.askstring(
            "手動で追加", "内容を入力:", parent=self._top
        )
        if not text:
            return
        minutes = simpledialog.askinteger(
            "所要分",
            "所要分を入力 (1〜480):",
            parent=self._top,
            minvalue=1,
            maxvalue=480,
            initialvalue=DEFAULT_DURATION_MIN,
        )
        if minutes is None:
            return
        self._items.append(
            PlanItem(
                source_id="",
                text=text.strip(),
                duration_min=int(minutes),
                kind="manual",
            )
        )
        self._checked.append(True)
        self._refresh_tree()

    def _on_add_from_picker(self) -> None:
        dlg = NotePickerDialog(self._top, self._repo)
        snippet = dlg.show()
        if not snippet:
            return
        minutes = simpledialog.askinteger(
            "所要分",
            "所要分を入力 (1〜480):",
            parent=self._top,
            minvalue=1,
            maxvalue=480,
            initialvalue=DEFAULT_DURATION_MIN,
        )
        if minutes is None:
            return
        # スニペットをそのままテキストとして使う ([[...]] 形式を保持)
        self._items.append(
            PlanItem(
                source_id="",
                text=snippet,
                duration_min=int(minutes),
                kind="manual",
            )
        )
        self._checked.append(True)
        self._refresh_tree()

    def _on_create(self) -> None:
        target = self._parse_target()
        if target is None:
            return
        chosen = [item for item, ok in zip(self._items, self._checked) if ok]
        if not chosen:
            messagebox.showwarning(
                "選択なし",
                "プランに含めるアイテムを 1 つ以上チェックしてください。",
                parent=self._top,
            )
            return
        start = self._start_var.get().strip() or DEFAULT_START_TIME
        body = render_markdown(chosen, target, start_time=start)

        try:
            draft = self._repo.create_draft(NoteType.DAILY)
            draft.title = f"{target.strftime('%Y-%m-%d')} のプラン"
            saved = self._repo.save_new(draft, body)
        except OSError as exc:
            messagebox.showerror(
                "保存エラー", f"プランの保存に失敗: {exc}", parent=self._top
            )
            return
        self._result = saved.id
        self._top.destroy()


def _kind_label(kind: str) -> str:
    return {
        "task": "todo",
        "routine": "routine",
        "manual": "手動",
    }.get(kind, kind)


def _display_text(item: PlanItem) -> str:
    if item.kind == "task" and item.note_title and item.note_title != item.text:
        return f"{item.text}  ←  {item.note_title}"
    return item.text
