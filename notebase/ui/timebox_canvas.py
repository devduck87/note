"""タスクごとに矩形を持つ対話的タイムボックスキャンバス。

- 高さ ∝ duration_min (PX_PER_MIN で調整)
- 下端ドラッグ → リサイズ (5 分刻みにスナップ)
- 中央ドラッグ → 並べ替え (release 時に target スロットへ移動)
- ダブルクリック → 詳細編集ダイアログ (詳細メモ / 実績分 / 遅延理由)

実績分 (`actual_min`) が記録されている矩形は「(計画m → 実績m)」を
ヘッダに併記し、計画より長引いた場合は朱色で警告表示する。
詳細・遅延理由が入っていればラベル下に小さく追記表示する。

`on_change(items)` は確定操作 (リサイズ / 並べ替え / 詳細編集) ごとに呼ばれる。
ドラッグ中は呼ばない (Markdown 保存サイクルが頻発しないように)。
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ..planning.timebox_format import (
    TimeboxItem,
    add_minutes,
    format_hhmm,
    parse_hhmm,
)

PX_PER_MIN = 2
MIN_DURATION = 5
EDGE_ZONE_PX = 6
MIN_BOX_PX = 24

_TIME_FONT = ("Consolas", 10, "bold")
_LABEL_FONT = ("Helvetica", 10)
_DURATION_FONT = ("Consolas", 9)
_NOTE_FONT = ("Helvetica", 9, "italic")


class TimeboxCanvas(tk.Canvas):
    """タイムボックスを対話的に編集できる Canvas。"""

    def __init__(
        self,
        parent: tk.Misc,
        items: list[TimeboxItem],
        start_time: str,
        *,
        on_change: Callable[[list[TimeboxItem]], None] | None = None,
        width: int = 480,
        background: str = "#fafcff",
    ) -> None:
        super().__init__(
            parent,
            width=width,
            highlightthickness=0,
            background=background,
            cursor="arrow",
        )
        self._items: list[TimeboxItem] = list(items)
        self._start_time = start_time
        self._on_change = on_change

        # ドラッグ状態: ('resize', idx, start_y, orig_min) | ('reorder', idx, start_y, dy)
        self._drag: tuple | None = None
        # 並べ替え中のドロップインジケータ位置 (None なら非表示)
        self._drop_indicator_y: int | None = None

        self.bind("<Motion>", self._on_motion)
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double_click)

        self._redraw()

    # ------------------------------------------------------------
    # public
    # ------------------------------------------------------------

    def items(self) -> list[TimeboxItem]:
        return list(self._items)

    # ------------------------------------------------------------
    # 描画
    # ------------------------------------------------------------

    def _box_height(self, item: TimeboxItem) -> int:
        base = max(MIN_BOX_PX, item.duration_min * PX_PER_MIN)
        # 詳細 / 遅延理由が入っているならラベル下に 1 行追加するため余白を確保。
        extras = 0
        if item.detail:
            extras += 14
        if item.reason:
            extras += 14
        if extras and base < 28 + extras:
            return 28 + extras
        return base

    def _box_y_range(self, idx: int) -> tuple[int, int]:
        """idx 番目の矩形の (top, bottom) を返す。"""
        y = 0
        for i, it in enumerate(self._items):
            h = self._box_height(it)
            if i == idx:
                return (y, y + h)
            y += h
        return (y, y)

    def _total_height(self) -> int:
        return sum(self._box_height(it) for it in self._items) or MIN_BOX_PX

    def _redraw(self) -> None:
        self.delete("all")
        w = int(self.cget("width"))
        cur = parse_hhmm(self._start_time)
        y = 0
        for i, it in enumerate(self._items):
            h = self._box_height(it)
            end = add_minutes(cur, it.duration_min)
            # 実績がある場合は遅延の有無で色を変える
            overran = it.actual_min is not None and it.actual_min > it.duration_min
            fill = "#fff1e8" if overran else "#e8f4ff"
            outline = "#cc6600" if overran else "#0050a0"
            self.create_rectangle(
                1, y + 1, w - 1, y + h - 1,
                fill=fill,
                outline=outline,
                width=1,
                tags=(f"box{i}", "box"),
            )
            # 時刻 (左上)
            self.create_text(
                8, y + 6,
                anchor="nw",
                text=f"{format_hhmm(cur)}–{format_hhmm(end)}",
                font=_TIME_FONT,
                fill=outline,
                tags=(f"box{i}",),
            )
            # ラベル (時刻の右、改行で複数行も許容)
            self.create_text(
                90, y + 6,
                anchor="nw",
                text=it.label,
                font=_LABEL_FONT,
                fill="#202020",
                width=w - 180,
                tags=(f"box{i}",),
            )
            # 所要分 (右上): 実績があれば「計画m → 実績m」、なければ「(計画m)」
            if it.actual_min is not None:
                duration_text = f"({it.duration_min}m → {it.actual_min}m)"
                duration_color = "#cc3300" if overran else "#1a7a1a"
            else:
                duration_text = f"({it.duration_min}m)"
                duration_color = "#666666"
            self.create_text(
                w - 8, y + 6,
                anchor="ne",
                text=duration_text,
                font=_DURATION_FONT,
                fill=duration_color,
                tags=(f"box{i}",),
            )
            # 詳細 / 遅延理由 (ラベル下に 1 行ずつ)
            note_y = y + 26
            if it.detail:
                self.create_text(
                    90, note_y,
                    anchor="nw",
                    text=f"📝 {it.detail}",
                    font=_NOTE_FONT,
                    fill="#404040",
                    width=w - 100,
                    tags=(f"box{i}",),
                )
                note_y += 14
            if it.reason:
                self.create_text(
                    90, note_y,
                    anchor="nw",
                    text=f"⚠ {it.reason}",
                    font=_NOTE_FONT,
                    fill="#aa3300",
                    width=w - 100,
                    tags=(f"box{i}",),
                )
            # 下端のリサイズハンドル (細い帯)
            self.create_rectangle(
                1, y + h - EDGE_ZONE_PX, w - 1, y + h - 1,
                fill="",
                outline="",
                tags=(f"edge{i}", "edge"),
            )
            cur = end
            y += h

        # ドロップインジケータ (並べ替え中のみ)
        if self._drop_indicator_y is not None:
            self.create_line(
                0, self._drop_indicator_y, w, self._drop_indicator_y,
                fill="#cc6600",
                width=2,
                tags=("drop_indicator",),
            )

        self.config(height=max(MIN_BOX_PX, self._total_height()))

    # ------------------------------------------------------------
    # ヒットテスト
    # ------------------------------------------------------------

    def _hit(self, x: int, y: int) -> tuple[int, str] | None:
        """(idx, zone) を返す。zone は 'edge' か 'body'。範囲外なら None。"""
        cy = 0
        for i, it in enumerate(self._items):
            h = self._box_height(it)
            if cy <= y < cy + h:
                if y >= cy + h - EDGE_ZONE_PX:
                    return (i, "edge")
                return (i, "body")
            cy += h
        return None

    def _index_for_drop_y(self, y: int) -> int:
        """並べ替えで cursor がいる Y に対応する挿入先 index を返す。"""
        cy = 0
        for i, it in enumerate(self._items):
            h = self._box_height(it)
            mid = cy + h / 2
            if y < mid:
                return i
            cy += h
        return len(self._items)

    # ------------------------------------------------------------
    # イベント
    # ------------------------------------------------------------

    def _on_motion(self, event: tk.Event) -> None:
        if self._drag is not None:
            return
        hit = self._hit(event.x, event.y)
        if hit is None:
            self.config(cursor="arrow")
            return
        _, zone = hit
        self.config(cursor="sb_v_double_arrow" if zone == "edge" else "fleur")

    def _on_press(self, event: tk.Event) -> None:
        hit = self._hit(event.x, event.y)
        if hit is None:
            return
        idx, zone = hit
        if zone == "edge":
            self._drag = ("resize", idx, event.y, self._items[idx].duration_min)
        else:
            self._drag = ("reorder", idx, event.y, 0)

    def _on_drag(self, event: tk.Event) -> None:
        if self._drag is None:
            return
        kind = self._drag[0]
        if kind == "resize":
            _, idx, start_y, orig_min = self._drag
            delta_px = event.y - start_y
            # 5 分刻みにスナップ
            delta_min = round(delta_px / PX_PER_MIN / 5) * 5
            new_min = max(MIN_DURATION, orig_min + delta_min)
            if new_min != self._items[idx].duration_min:
                cur = self._items[idx]
                self._items[idx] = TimeboxItem(
                    label=cur.label,
                    duration_min=new_min,
                    detail=cur.detail,
                    actual_min=cur.actual_min,
                    reason=cur.reason,
                )
                self._redraw()
        elif kind == "reorder":
            _, idx, start_y, _ = self._drag
            # ドロップインジケータ位置 = cursor 位置 (ただしスロット境界にスナップ)
            target = self._index_for_drop_y(event.y)
            cy = 0
            for i, it in enumerate(self._items):
                if i == target:
                    self._drop_indicator_y = cy
                    break
                cy += self._box_height(it)
            else:
                self._drop_indicator_y = cy
            # 移動先表示のため再描画 (元位置はそのまま、線だけ動く)
            self._drag = ("reorder", idx, start_y, event.y - start_y)
            self._redraw()

    def _on_release(self, event: tk.Event) -> None:
        if self._drag is None:
            return
        kind = self._drag[0]
        changed = False
        if kind == "resize":
            changed = True  # _on_drag で既にアイテム更新済み
        elif kind == "reorder":
            _, idx, _, _ = self._drag
            target = self._index_for_drop_y(event.y)
            # target は「移動後の挿入位置」だが、idx より大きい場合は -1 する
            if target > idx:
                target -= 1
            if target != idx:
                item = self._items.pop(idx)
                self._items.insert(target, item)
                changed = True
        self._drag = None
        self._drop_indicator_y = None
        self._redraw()
        if changed and self._on_change is not None:
            self._on_change(list(self._items))

    def _on_double_click(self, event: tk.Event) -> None:
        """矩形のダブルクリックで詳細編集ダイアログを開く。"""
        # ドラッグ中の誤発火を防ぐ
        if self._drag is not None:
            return
        hit = self._hit(event.x, event.y)
        if hit is None:
            return
        idx, _ = hit
        # 遅延 import: timebox_detail_dialog → timebox_canvas の循環を避けるため。
        from .timebox_detail_dialog import TimeboxDetailDialog

        dlg = TimeboxDetailDialog(self, self._items[idx])
        result = dlg.show()
        if result is None:
            return
        self._items[idx] = result
        self._redraw()
        if self._on_change is not None:
            self._on_change(list(self._items))
