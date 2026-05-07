from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory

from notebase.core.note_status import NoteStatus
from notebase.core.note_type import NoteType
from notebase.storage.app_paths import AppPaths
from notebase.storage.note_repository import NoteRepository
from notebase.storage.trash_service import TrashService


def _make_repo(td: str) -> NoteRepository:
    paths = AppPaths(td)
    paths.ensure_layout()
    return NoteRepository(paths, TrashService(paths))


class CreateInstanceTests(unittest.TestCase):
    def test_basic_procedure_to_log(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            tmpl = repo.create_draft(NoteType.PROCEDURE)
            tmpl.title = "Excel検索ツールの使い方"
            tmpl.tags = ["excel", "tool"]
            saved_tmpl = repo.save_new(tmpl, "## 手順\n\n1. ファイルを選択する\n2. 検索条件を指定する\n")

            meta, body = repo.create_instance(saved_tmpl.id)

            self.assertEqual(meta.type, NoteType.LOG)
            self.assertEqual(meta.instance_of, saved_tmpl.id)
            self.assertEqual(meta.status, NoteStatus.ACTIVE)
            self.assertEqual(meta.tags, ["excel", "tool"])
            self.assertIn("Excel検索ツールの使い方", meta.title)
            self.assertNotEqual(meta.id, saved_tmpl.id)

            self.assertTrue(repo.paths.note_dir(meta.id).exists())
            self.assertTrue(repo.paths.images_dir(meta.id).exists())

            # 先頭にテンプレ参照、テンプレ側 H1 は除去されている
            self.assertTrue(
                body.startswith("> テンプレート: [[Excel検索ツールの使い方]]"),
                f"unexpected body head: {body[:80]!r}",
            )
            # テンプレに `# Excel検索ツールの使い方` が存在しても残っていない
            self.assertNotIn("# Excel検索ツールの使い方", body)
            # 本文の続きは保持
            self.assertIn("1. ファイルを選択する", body)

    def test_checklist_template_works_too(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            tmpl = repo.create_draft(NoteType.CHECKLIST)
            tmpl.title = "リリースチェック"
            saved_tmpl = repo.save_new(tmpl, "- [ ] バックアップ取得\n- [ ] テスト実行\n")

            meta, body = repo.create_instance(saved_tmpl.id)
            self.assertEqual(meta.type, NoteType.LOG)
            self.assertEqual(meta.instance_of, saved_tmpl.id)
            self.assertIn("- [ ] バックアップ取得", body)

    def test_save_new_persists_instance(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            tmpl = repo.create_draft(NoteType.PROCEDURE)
            tmpl.title = "tmpl"
            saved_tmpl = repo.save_new(tmpl, "step")

            meta, body = repo.create_instance(saved_tmpl.id)
            saved_inst = repo.save_new(meta, body)

            self.assertEqual(saved_inst.type, NoteType.LOG)
            self.assertEqual(saved_inst.instance_of, saved_tmpl.id)

            # ディスク確認: meta.json に instance_of がシリアライズされている
            meta_text = repo.paths.meta_path(saved_inst.id).read_text(encoding="utf-8")
            self.assertIn(f'"instance_of": "{saved_tmpl.id}"', meta_text)

    def test_template_without_h1_keeps_body(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            tmpl = repo.create_draft(NoteType.PROCEDURE)
            tmpl.title = ""  # 空タイトルだと sync_title_h1 が "# " のみ追加するが
            saved_tmpl = repo.save_new(tmpl, "no heading\nsecond line")

            _meta, body = repo.create_instance(saved_tmpl.id)
            self.assertIn("> テンプレート", body)


if __name__ == "__main__":
    unittest.main()
