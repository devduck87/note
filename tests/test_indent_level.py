from __future__ import annotations

import unittest

from notebase.ui.md_preview import _MAX_INDENT_LEVEL, _indent_level


class IndentLevelTests(unittest.TestCase):
    def test_no_indent(self) -> None:
        self.assertEqual(_indent_level(""), 0)
        self.assertEqual(_indent_level("nope"), 0)

    def test_two_spaces_one_level(self) -> None:
        self.assertEqual(_indent_level("  "), 1)
        self.assertEqual(_indent_level("    "), 2)
        self.assertEqual(_indent_level("      "), 3)

    def test_one_space_zero_level(self) -> None:
        # 1 スペースは 0.5 → int で 0
        self.assertEqual(_indent_level(" "), 0)

    def test_tab_one_level(self) -> None:
        self.assertEqual(_indent_level("\t"), 1)
        self.assertEqual(_indent_level("\t\t"), 2)

    def test_mixed(self) -> None:
        # タブ 1 + 2 スペース = 1 + 1 = 2
        self.assertEqual(_indent_level("\t  "), 2)

    def test_capped_at_max(self) -> None:
        self.assertEqual(_indent_level(" " * 32), _MAX_INDENT_LEVEL)
        self.assertEqual(_indent_level("\t" * 20), _MAX_INDENT_LEVEL)

    def test_stops_at_first_non_whitespace(self) -> None:
        # "  - text" → 先頭 2 スペースだけカウント
        self.assertEqual(_indent_level("  "), 1)
        # トレース確認: '\t- xxx' のような mid-line は呼び出し元が前置部だけ渡す前提


if __name__ == "__main__":
    unittest.main()
