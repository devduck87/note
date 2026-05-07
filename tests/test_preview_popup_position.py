"""NotePreviewPopup の位置計算が画面端ではみ出さないことを検証する (純粋関数)。"""

from __future__ import annotations

import unittest

from notebase.ui.note_preview_popup import flip_position


class FlipPositionTests(unittest.TestCase):
    SW = 1920
    SH = 1080
    PW = 480
    PH = 320

    def test_default_offset_when_far_from_edges(self) -> None:
        x, y = flip_position(100, 100, self.PW, self.PH, self.SW, self.SH)
        self.assertEqual((x, y), (116, 116))

    def test_flips_up_when_near_bottom(self) -> None:
        # y_root が下端付近 → ポップアップ下端が画面外になるので上へフリップ
        x, y = flip_position(100, self.SH - 5, self.PW, self.PH, self.SW, self.SH)
        # 上方向にフリップされて y < y_root
        self.assertLess(y, self.SH - 5)
        # 下端は画面内
        self.assertLessEqual(y + self.PH, self.SH)

    def test_flips_left_when_near_right(self) -> None:
        x, y = flip_position(self.SW - 5, 100, self.PW, self.PH, self.SW, self.SH)
        self.assertLess(x, self.SW - 5)
        self.assertLessEqual(x + self.PW, self.SW)

    def test_corner_case_bottom_right(self) -> None:
        x, y = flip_position(
            self.SW - 5, self.SH - 5, self.PW, self.PH, self.SW, self.SH
        )
        self.assertLessEqual(x + self.PW, self.SW)
        self.assertLessEqual(y + self.PH, self.SH)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)

    def test_popup_larger_than_screen_clamps_to_zero(self) -> None:
        # ポップアップが画面より大きい (異常ケース) でも負座標にしない
        x, y = flip_position(50, 50, 3000, 2000, 1920, 1080)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)

    def test_custom_margin(self) -> None:
        x, y = flip_position(100, 100, 100, 100, 1920, 1080, margin=8)
        self.assertEqual((x, y), (108, 108))


if __name__ == "__main__":
    unittest.main()
