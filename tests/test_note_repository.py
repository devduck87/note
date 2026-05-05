from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from notebase.core.note_type import NoteType
from notebase.storage.app_paths import AppPaths
from notebase.storage.note_repository import NoteRepository, _sync_title_h1
from notebase.storage.trash_service import TrashService


def _make_repo(td: str) -> NoteRepository:
    paths = AppPaths(td)
    paths.ensure_layout()
    return NoteRepository(paths, TrashService(paths))


class CreateDraftTests(unittest.TestCase):
    def test_creates_folders(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.MEMO)
            self.assertTrue(repo.paths.note_dir(meta.id).exists())
            self.assertTrue(repo.paths.images_dir(meta.id).exists())
            self.assertEqual(meta.type, NoteType.MEMO)


class SaveLoadTests(unittest.TestCase):
    def test_save_new_renames_dir(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.MEMO)
            old_id = meta.id
            meta.title = "New Title"
            saved = repo.save_new(meta, "body")
            self.assertNotEqual(saved.id, old_id)
            self.assertTrue(saved.id.endswith("-new-title"))
            self.assertTrue(repo.paths.meta_path(saved.id).exists())
            self.assertTrue(repo.paths.index_md_path(saved.id).exists())

    def test_save_existing_keeps_id(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.MEMO)
            meta.title = "Hi"
            saved = repo.save_new(meta, "body")
            saved.title = "Hi (updated)"
            saved2 = repo.save_existing(saved, "body")
            self.assertEqual(saved2.id, saved.id)

    def test_round_trip(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.TODO)
            meta.title = "Task A"
            meta.tags = ["x"]
            saved = repo.save_new(meta, "body")
            loaded_meta, loaded_body = repo.load(saved.id)
            self.assertEqual(loaded_meta.title, "Task A")
            self.assertEqual(loaded_meta.type, NoteType.TODO)
            self.assertEqual(loaded_meta.tags, ["x"])
            self.assertIn("# Task A", loaded_body)


class LoadAllTests(unittest.TestCase):
    def test_skips_broken_meta(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.MEMO)
            meta.title = "ok"
            repo.save_new(meta, "x")
            broken_dir = repo.paths.notes / "broken"
            broken_dir.mkdir()
            (broken_dir / "meta.json").write_text("not json", encoding="utf-8")
            metas = list(repo.load_all())
            self.assertEqual(len(metas), 1)
            self.assertEqual(metas[0].title, "ok")


class EnsureBlockIdTests(unittest.TestCase):
    def test_returns_existing_id(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.MEMO)
            meta.title = "t"
            saved = repo.save_new(meta, "para1\npara2 ^abc123")
            # 4 行目 (0-based) = "para2 ^abc123"... but sync_title_h1 prepends "# t\n\n"
            # so lines: ["# t", "", "para1", "para2 ^abc123"]
            block_id = repo.ensure_block_id(saved.id, 3)
            self.assertEqual(block_id, "abc123")

    def test_generates_new_id(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.MEMO)
            meta.title = "t"
            saved = repo.save_new(meta, "para1")
            # lines after save: ["# t", "", "para1"]
            new_id = repo.ensure_block_id(saved.id, 2)
            self.assertIsNotNone(new_id)
            self.assertEqual(len(new_id), 6)
            _, body = repo.load(saved.id)
            self.assertIn(f" ^{new_id}", body)

    def test_empty_line_returns_none(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            meta = repo.create_draft(NoteType.MEMO)
            meta.title = "t"
            saved = repo.save_new(meta, "para")
            self.assertIsNone(repo.ensure_block_id(saved.id, 1))  # empty line


class SyncTitleH1Tests(unittest.TestCase):
    def test_replaces_existing_h1(self) -> None:
        body = "# Old\n\nbody"
        result = _sync_title_h1(body, "New")
        self.assertEqual(result, "# New\r\n\r\nbody")

    def test_inserts_when_missing(self) -> None:
        body = "no h1 here"
        result = _sync_title_h1(body, "New")
        self.assertEqual(result, "# New\r\n\r\nno h1 here")

    def test_skips_leading_empty_lines(self) -> None:
        body = "\n\n# Old\n\nbody"
        result = _sync_title_h1(body, "New")
        self.assertEqual(result, "\r\n\r\n# New\r\n\r\nbody")


if __name__ == "__main__":
    unittest.main()
