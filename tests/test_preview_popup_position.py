"""NotePreviewPopup の位置計算が画面/作業領域端ではみ出さないことを検証する。"""

from __future__ import annotations

import unittest

from notebase.ui.note_preview_popup import flip_position


class FlipPositionTests(unittest.TestCase):
    PW = 480
    PH = 320
    # work_area: タスクバーが下 40px にあるとして残りが作業領域
    WA_FULL = (0, 0, 1920, 1080)
    WA_TASKBAR = (0, 0, 1920, 1040)

    def test_default_offset_when_far_from_edges(self) -> None:
        x, y = flip_position(100, 100, self.PW, self.PH, work_area=self.WA_FULL)
        self.assertEqual((x, y), (116, 116))

    def test_flips_up_when_near_bottom(self) -> None:
        x, y = flip_position(100, 1075, self.PW, self.PH, work_area=self.WA_FULL)
        # フリップして y < y_root
        self.assertLess(y, 1075)
        # 領域内に収まる
        self.assertLessEqual(y + self.PH, 1080)

    def test_flips_left_when_near_right(self) -> None:
        x, y = flip_position(1915, 100, self.PW, self.PH, work_area=self.WA_FULL)
        self.assertLess(x, 1915)
        self.assertLessEqual(x + self.PW, 1920)

    def test_corner_case_bottom_right(self) -> None:
        x, y = flip_position(1915, 1075, self.PW, self.PH, work_area=self.WA_FULL)
        self.assertLessEqual(x + self.PW, 1920)
        self.assertLessEqual(y + self.PH, 1080)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)

    def test_excludes_taskbar(self) -> None:
        # 下端付近: 全画面ではフリップ不要に見えても、タスクバー除外領域では必要
        # y_root=1010 でポップアップ高 320 → 1010+16+320 = 1346 が limit を超える
        x, y = flip_position(100, 1010, self.PW, self.PH, work_area=self.WA_TASKBAR)
        self.assertLessEqual(y + self.PH, 1040, "タスクバー領域に重ならないこと")

    def test_taskbar_does_not_affect_when_above(self) -> None:
        # 上の方では taskbar 設定でも挙動変わらず
        x, y = flip_position(200, 200, self.PW, self.PH, work_area=self.WA_TASKBAR)
        self.assertEqual((x, y), (216, 216))

    def test_popup_larger_than_screen_clamps(self) -> None:
        x, y = flip_position(50, 50, 3000, 2000, work_area=self.WA_FULL)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)

    def test_custom_margin(self) -> None:
        x, y = flip_position(
            100, 100, 100, 100, work_area=self.WA_FULL, margin=8
        )
        self.assertEqual((x, y), (108, 108))


if __name__ == "__main__":
    unittest.main()
