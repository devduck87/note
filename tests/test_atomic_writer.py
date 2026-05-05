from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from notebase.storage.atomic_writer import write_text_atomic


class AtomicWriterTests(unittest.TestCase):
    def test_creates_file_with_utf8_no_bom(self) -> None:
        with TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            write_text_atomic(p, "héllo")
            data = p.read_bytes()
            self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
            self.assertEqual(data.decode("utf-8"), "héllo")

    def test_overwrites_existing(self) -> None:
        with TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            p.write_text("old", encoding="utf-8")
            write_text_atomic(p, "new")
            self.assertEqual(p.read_text(encoding="utf-8"), "new")

    def test_creates_parent_dirs(self) -> None:
        with TemporaryDirectory() as td:
            p = Path(td) / "sub" / "deeper" / "a.txt"
            write_text_atomic(p, "x")
            self.assertEqual(p.read_text(encoding="utf-8"), "x")

    def test_no_temp_file_left_behind(self) -> None:
        with TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            write_text_atomic(p, "x")
            self.assertEqual(
                [c.name for c in Path(td).iterdir()],
                ["a.txt"],
            )


if __name__ == "__main__":
    unittest.main()
