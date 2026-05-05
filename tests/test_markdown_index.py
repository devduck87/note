from __future__ import annotations

import unittest

from notebase.markdown.md_index import (
    BlockKind,
    extract_blocks,
    extract_headings,
    extract_section,
    slugify_heading,
)


class SlugifyHeadingTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(slugify_heading(""), "")
        self.assertEqual(slugify_heading(None), "")

    def test_basic(self) -> None:
        self.assertEqual(slugify_heading("Hello World"), "hello-world")

    def test_japanese_kept(self) -> None:
        self.assertEqual(slugify_heading("見出し1"), "見出し1")

    def test_collapses_consecutive_ws(self) -> None:
        self.assertEqual(slugify_heading("a   b"), "a-b")

    def test_leading_ws_no_dash(self) -> None:
        self.assertEqual(slugify_heading("  foo"), "foo")

    def test_trailing_ws_trimmed(self) -> None:
        self.assertEqual(slugify_heading("foo  "), "foo")

    def test_keeps_dash_chars(self) -> None:
        self.assertEqual(slugify_heading("Test - Title"), "test---title")


class ExtractHeadingsTests(unittest.TestCase):
    def test_extracts_levels(self) -> None:
        body = "# H1\n\n## H2\n\nbody\n\n### H3"
        h = extract_headings(body)
        self.assertEqual([(x.level, x.text) for x in h], [(1, "H1"), (2, "H2"), (3, "H3")])

    def test_skips_in_code_fence(self) -> None:
        body = "# Real\n\n```\n# Fake\n```\n\n## Also"
        h = extract_headings(body)
        self.assertEqual([x.text for x in h], ["Real", "Also"])


class ExtractBlocksTests(unittest.TestCase):
    def test_paragraph_with_block_id(self) -> None:
        body = "first line\nsecond line ^abc123"
        blocks = extract_blocks(body)
        self.assertEqual(len(blocks), 1)
        b = blocks[0]
        self.assertEqual(b.kind, BlockKind.PARAGRAPH)
        self.assertEqual(b.existing_id, "abc123")
        self.assertEqual(b.text, "first line second line")

    def test_list_items_and_tasks(self) -> None:
        body = "- a\n- [ ] b\n- [x] c"
        blocks = extract_blocks(body)
        kinds = [b.kind for b in blocks]
        self.assertEqual(
            kinds,
            [BlockKind.LIST_ITEM, BlockKind.TASK_ITEM, BlockKind.TASK_ITEM],
        )

    def test_context_level_propagates(self) -> None:
        body = "# H1\n\n- item under H1\n\n## H2\n\n- item under H2"
        blocks = extract_blocks(body)
        # blocks: H1, list-item-1, H2, list-item-2
        self.assertEqual(blocks[1].context_level, 1)
        self.assertEqual(blocks[3].context_level, 2)


class ExtractSectionTests(unittest.TestCase):
    def test_extract_by_heading_slug(self) -> None:
        body = "# Top\n\n## Sub A\n\nA body\n\n## Sub B\n\nB body"
        section = extract_section(body, "sub-a")
        self.assertIn("## Sub A", section)
        self.assertIn("A body", section)
        self.assertNotIn("Sub B", section)

    def test_extract_by_block_id(self) -> None:
        body = "para 1\n\npara 2 ^xyz"
        section = extract_section(body, "xyz")
        self.assertEqual(section, "para 2 ^xyz")

    def test_no_match_returns_full(self) -> None:
        body = "# A\n\nbody"
        self.assertEqual(extract_section(body, "z"), body)


if __name__ == "__main__":
    unittest.main()
