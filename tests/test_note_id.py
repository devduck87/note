from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from notebase.core import note_id


class SlugifyTests(unittest.TestCase):
    def test_empty_returns_untitled(self) -> None:
        self.assertEqual(note_id.slugify(""), "untitled")
        self.assertEqual(note_id.slugify(None), "untitled")

    def test_lowercase_and_dashes(self) -> None:
        self.assertEqual(note_id.slugify("Hello World"), "hello-world")

    def test_japanese_replaced_with_dash(self) -> None:
        self.assertEqual(note_id.slugify("メモ"), "untitled")

    def test_truncation_to_60(self) -> None:
        long = "a" * 70
        self.assertEqual(len(note_id.slugify(long)), 60)

    def test_truncation_trims_trailing_dash(self) -> None:
        # 60 文字目が '-' になるケースで末尾の '-' を再トリム
        title = "a" * 59 + " " + "b"
        slug = note_id.slugify(title)
        self.assertFalse(slug.endswith("-"))

    def test_consecutive_non_ascii_collapsed(self) -> None:
        self.assertEqual(note_id.slugify("foo!!!bar"), "foo-bar")


class GenerateTests(unittest.TestCase):
    def test_format(self) -> None:
        nid = note_id.generate("My Note", datetime(2026, 5, 5, 12, 34, 56))
        self.assertEqual(nid, "20260505-123456-my-note")


class EnsureUniqueTests(unittest.TestCase):
    def test_no_collision(self) -> None:
        with TemporaryDirectory() as td:
            nid = note_id.ensure_unique("abc", td, datetime(2026, 1, 1, 0, 0, 0, 123_000))
            self.assertEqual(nid, "abc")

    def test_collision_appends_ms(self) -> None:
        with TemporaryDirectory() as td:
            (Path(td) / "abc").mkdir()
            nid = note_id.ensure_unique("abc", td, datetime(2026, 1, 1, 0, 0, 0, 123_000))
            self.assertEqual(nid, "abc-123")

    def test_double_collision_appends_serial(self) -> None:
        with TemporaryDirectory() as td:
            (Path(td) / "abc").mkdir()
            (Path(td) / "abc-123").mkdir()
            nid = note_id.ensure_unique("abc", td, datetime(2026, 1, 1, 0, 0, 0, 123_000))
            self.assertEqual(nid, "abc-123-2")


class ReplaceSlugTests(unittest.TestCase):
    def test_replaces_only_slug_part(self) -> None:
        nid = note_id.replace_slug("20260505-123456-old", "New Title")
        self.assertEqual(nid, "20260505-123456-new-title")

    def test_short_id_unchanged(self) -> None:
        self.assertEqual(note_id.replace_slug("abc", "x"), "abc")


if __name__ == "__main__":
    unittest.main()
