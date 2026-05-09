from __future__ import annotations

import unittest

from notebase.planning.timebox_format import (
    TimeboxItem,
    add_minutes,
    format_hhmm,
    parse_hhmm,
    render_timebox_lines,
)


class ParseFormatTests(unittest.TestCase):
    def test_parse_valid(self) -> None:
        self.assertEqual(format_hhmm(parse_hhmm("09:00")), "09:00")
        self.assertEqual(format_hhmm(parse_hhmm("23:59")), "23:59")

    def test_parse_invalid_falls_back(self) -> None:
        self.assertEqual(format_hhmm(parse_hhmm("bad")), "09:00")
        self.assertEqual(format_hhmm(parse_hhmm("")), "09:00")
        self.assertEqual(format_hhmm(parse_hhmm(None)), "09:00")

    def test_add_minutes(self) -> None:
        t = parse_hhmm("09:00")
        self.assertEqual(format_hhmm(add_minutes(t, 90)), "10:30")
        self.assertEqual(format_hhmm(add_minutes(t, 0)), "09:00")
        # 負の値は 0 として扱う
        self.assertEqual(format_hhmm(add_minutes(t, -10)), "09:00")


class RenderTimeboxLinesTests(unittest.TestCase):
    def test_basic(self) -> None:
        items = [
            TimeboxItem("朝のルーティン", 15),
            TimeboxItem("仕様書レビュー", 60),
            TimeboxItem("テスト追加", 30),
        ]
        lines = render_timebox_lines(items, "09:00")
        self.assertEqual(
            lines,
            [
                "- 09:00–09:15 朝のルーティン (15m)",
                "- 09:15–10:15 仕様書レビュー (60m)",
                "- 10:15–10:45 テスト追加 (30m)",
            ],
        )

    def test_empty_items(self) -> None:
        self.assertEqual(render_timebox_lines([], "09:00"), [])

    def test_custom_start(self) -> None:
        lines = render_timebox_lines([TimeboxItem("x", 30)], "13:30")
        self.assertEqual(lines, ["- 13:30–14:00 x (30m)"])

    def test_invalid_start_falls_back(self) -> None:
        lines = render_timebox_lines([TimeboxItem("x", 30)], "bad")
        self.assertEqual(lines, ["- 09:00–09:30 x (30m)"])

    def test_omits_child_lines_when_unset(self) -> None:
        # detail / actual_min / reason がデフォルトのままなら子行は出さない
        lines = render_timebox_lines([TimeboxItem("x", 30)], "09:00")
        self.assertEqual(lines, ["- 09:00–09:30 x (30m)"])

    def test_emits_child_lines_when_set(self) -> None:
        items = [
            TimeboxItem(
                "朝のルーティン",
                15,
                detail="ストレッチとコーヒー",
                actual_min=20,
                reason="寝坊した",
            ),
            TimeboxItem("レビュー", 30, detail="PR #42"),
        ]
        lines = render_timebox_lines(items, "09:00")
        self.assertEqual(
            lines,
            [
                "- 09:00–09:15 朝のルーティン (15m)",
                "  - 詳細: ストレッチとコーヒー",
                "  - 実績: 20m",
                "  - 遅延理由: 寝坊した",
                "- 09:15–09:45 レビュー (30m)",
                "  - 詳細: PR #42",
            ],
        )

    def test_actual_zero_emits(self) -> None:
        # actual_min が 0 でも (None ではない) 子行は出す
        lines = render_timebox_lines(
            [TimeboxItem("x", 30, actual_min=0)], "09:00"
        )
        self.assertEqual(
            lines,
            [
                "- 09:00–09:30 x (30m)",
                "  - 実績: 0m",
            ],
        )


if __name__ == "__main__":
    unittest.main()
