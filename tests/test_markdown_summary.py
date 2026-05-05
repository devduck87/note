from __future__ import annotations

import unittest

from notebase.markdown.summary import extract


class SummaryTests(unittest.TestCase):
    def test_strips_headings(self) -> None:
        self.assertEqual(extract("# Title\n\nbody", 100), "body")

    def test_strips_code_fence(self) -> None:
        body = "before\n\n```\ncode\n```\n\nafter"
        self.assertEqual(extract(body, 100), "before after")

    def test_strips_decorations(self) -> None:
        body = "**bold** and *em* and `code` and [link](u) and ![img](u)"
        self.assertEqual(extract(body, 100), "bold and em and code and link and img")

    def test_truncates(self) -> None:
        body = "abcdefghij"
        self.assertEqual(extract(body, 5), "abcde…")

    def test_strips_list_markers(self) -> None:
        body = "- item one\n- [x] task two"
        self.assertEqual(extract(body, 100), "item one task two")

    def test_wiki_alias(self) -> None:
        self.assertEqual(extract("see [[Foo|alias]] here", 100), "see alias here")

    def test_wiki_plain(self) -> None:
        self.assertEqual(extract("see [[Foo]] here", 100), "see Foo here")


if __name__ == "__main__":
    unittest.main()
