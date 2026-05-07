from __future__ import annotations

import unittest

from notebase.ui.main_window import _toggle_task_line


class ToggleTaskLineTests(unittest.TestCase):
    def test_open_to_done(self) -> None:
        self.assertEqual(_toggle_task_line("- [ ] do thing"), "- [x] do thing")

    def test_done_to_open(self) -> None:
        self.assertEqual(_toggle_task_line("- [x] done"), "- [ ] done")

    def test_uppercase_x_normalized_to_space(self) -> None:
        # 大文字 X もチェック扱いとして off へ
        self.assertEqual(_toggle_task_line("- [X] DONE"), "- [ ] DONE")

    def test_indent_preserved(self) -> None:
        self.assertEqual(
            _toggle_task_line("    - [ ] nested"), "    - [x] nested"
        )

    def test_alt_bullet(self) -> None:
        self.assertEqual(_toggle_task_line("* [ ] x"), "* [x] x")
        self.assertEqual(_toggle_task_line("+ [x] y"), "+ [ ] y")

    def test_non_task_returns_none(self) -> None:
        self.assertIsNone(_toggle_task_line("- not a task"))
        self.assertIsNone(_toggle_task_line("plain text"))
        self.assertIsNone(_toggle_task_line(""))

    def test_preserves_block_id(self) -> None:
        self.assertEqual(
            _toggle_task_line("- [ ] task body ^abc"),
            "- [x] task body ^abc",
        )


if __name__ == "__main__":
    unittest.main()
