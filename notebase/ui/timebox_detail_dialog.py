"""タイムボックス 1 タスクの詳細編集ダイアログ。

`TimeboxCanvas` のダブルクリックから開かれ、以下を編集できる:

- ラベル / 計画分 (事前)
- 詳細: 計画時のメモ・前提条件など
- 実績分: 後で振り返るための実所要分
- 遅延理由: 計画から外れた理由 (一行)

`show()` は更新後の `TimeboxItem` を返す。キャンセル時は `None`。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..planning.timebox_format import TimeboxItem


class TimeboxDetailDialog:
    """タイムボックス 1 タスクの詳細をモーダルで編集する。"""

    def __init__(self, master: tk.Misc, item: TimeboxItem) -> None:
        self._master = master
        self._item = item
        self._result: TimeboxItem | None = None

    def show(self) -> TimeboxItem | None:
        self._build()
        self._top.wait_window()
        return self._result

    # ------------------------------------------------------------
    # construction
    # ------------------------------------------------------------

    def _build(self) -> None:
        top = tk.Toplevel(self._master)
        top.title("タスク詳細")
        top.transient(self._master.winfo_toplevel())
        top.grab_set()
        top.geometry("520x420")
        self._top = top

        body = ttk.Frame(top, padding=10)
        body.pack(fill="both", expand=True)

        # ---- 計画 ----
        plan = ttk.LabelFrame(body, text="計画 (事前)", padding=8)
        plan.pack(fill="x", pady=(0, 8))

        ttk.Label(plan, text="ラベル:").grid(row=0, column=0, sticky="w")
        self._label_var = tk.StringVar(value=self._item.label)
        ttk.Entry(plan, textvariable=self._label_var, width=48).grid(
            row=0, column=1, sticky="we", padx=(6, 0), pady=2
        )

        ttk.Label(plan, text="計画分:").grid(row=1, column=0, sticky="w")
        self._plan_var = tk.StringVar(value=str(self._item.duration_min))
        ttk.Entry(plan, textvariable=self._plan_var, width=8).grid(
            row=1, column=1, sticky="w", padx=(6, 0), pady=2
        )

        ttk.Label(plan, text="詳細:").grid(row=2, column=0, sticky="nw", pady=(4, 0))
        self._detail_text = tk.Text(plan, height=4, width=48, wrap="word")
        self._detail_text.grid(
            row=2, column=1, sticky="we", padx=(6, 0), pady=(4, 0)
        )
        self._detail_text.insert("1.0", self._item.detail)

        plan.columnconfigure(1, weight=1)

        # ---- 実績 ----
        actual = ttk.LabelFrame(body, text="実績 (事後)", padding=8)
        actual.pack(fill="x", pady=(0, 8))

        ttk.Label(actual, text="実績分:").grid(row=0, column=0, sticky="w")
        self._actual_var = tk.StringVar(
            value="" if self._item.actual_min is None else str(self._item.actual_min)
        )
        ttk.Entry(actual, textvariable=self._actual_var, width=8).grid(
            row=0, column=1, sticky="w", padx=(6, 0), pady=2
        )
        ttk.Label(
            actual,
            text="(空欄なら未記入)",
            foreground="#888888",
        ).grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(actual, text="遅延理由:").grid(
            row=1, column=0, sticky="nw", pady=(4, 0)
        )
        self._reason_text = tk.Text(actual, height=4, width=48, wrap="word")
        self._reason_text.grid(
            row=1, column=1, columnspan=2, sticky="we", padx=(6, 0), pady=(4, 0)
        )
        self._reason_text.insert("1.0", self._item.reason)

        actual.columnconfigure(1, weight=1)

        # ---- ボタン ----
        btns = ttk.Frame(body)
        btns.pack(fill="x")
        ttk.Button(btns, text="OK", command=self._on_ok).pack(side="right")
        ttk.Button(
            btns, text="キャンセル", command=self._top.destroy
        ).pack(side="right", padx=(0, 6))

        top.bind("<Escape>", lambda e: self._top.destroy())
        top.bind("<Control-Return>", lambda e: self._on_ok())

    # ------------------------------------------------------------
    # events
    # ------------------------------------------------------------

    def _on_ok(self) -> None:
        label = self._label_var.get().strip()
        if not label:
            messagebox.showwarning(
                "入力エラー", "ラベルは必須です。", parent=self._top
            )
            return

        try:
            plan_min = int(self._plan_var.get().strip())
            if plan_min < 1 or plan_min > 480:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "入力エラー",
                "計画分は 1〜480 の整数で入力してください。",
                parent=self._top,
            )
            return

        actual_raw = self._actual_var.get().strip()
        if actual_raw == "":
            actual_min: int | None = None
        else:
            try:
                actual_min = int(actual_raw)
                if actual_min < 0 or actual_min > 1440:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "入力エラー",
                    "実績分は 0〜1440 の整数か空欄で入力してください。",
                    parent=self._top,
                )
                return

        detail = _flatten(self._detail_text.get("1.0", "end-1c"))
        reason = _flatten(self._reason_text.get("1.0", "end-1c"))

        self._result = TimeboxItem(
            label=label,
            duration_min=plan_min,
            detail=detail,
            actual_min=actual_min,
            reason=reason,
        )
        self._top.destroy()


def _flatten(s: str) -> str:
    """子行は 1 行で書き出すので改行・連続空白を空白 1 つに畳む。"""
    return " ".join(s.split())
