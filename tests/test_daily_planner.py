from __future__ import annotations

import unittest
from datetime import date
from tempfile import TemporaryDirectory

from notebase.core.note_status import NoteStatus
from notebase.core.note_type import NoteType
from notebase.core.schedule import Schedule, ScheduleFrequency
from notebase.planning.daily_planner import (
    PlanItem,
    candidates_for,
    render_markdown,
)
from notebase.storage.app_paths import AppPaths
from notebase.storage.note_repository import NoteRepository
from notebase.storage.trash_service import TrashService


def _make_repo(td: str) -> NoteRepository:
    paths = AppPaths(td)
    paths.ensure_layout()
    return NoteRepository(paths, TrashService(paths))


class CandidatesForTests(unittest.TestCase):
    def test_collects_due_todos_and_active_routines(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)

            # routine: 木曜日に該当
            r = repo.create_draft(NoteType.ROUTINE)
            r.title = "朝のルーティン"
            r.schedule = Schedule(
                frequency=ScheduleFrequency.WEEKLY,
                days=["thu"],
                enabled=True,
            )
            repo.save_new(r, "- [ ] メールチェック")

            # todo: 期限が今日以前
            t = repo.create_draft(NoteType.TODO)
            t.title = "雑務"
            repo.save_new(t, "- [ ] レビュー @2026-05-07\n- [ ] 未来 @2026-06-01\n- [x] 完了 @2026-05-01")

            items = candidates_for(repo, date(2026, 5, 7))  # Thu

            kinds = [(i.kind, i.text) for i in items]
            # ルーティーン → todo の順
            self.assertEqual(kinds[0][0], "routine")
            self.assertEqual(kinds[0][1], "朝のルーティン")
            # 期限切れ + 完了は除外、未来分も除外
            task_texts = [t for k, t in kinds if k == "task"]
            self.assertIn("レビュー", task_texts)
            self.assertNotIn("未来", task_texts)
            self.assertNotIn("完了", task_texts)

    def test_routine_excluded_when_disabled(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            r = repo.create_draft(NoteType.ROUTINE)
            r.title = "停止中"
            r.schedule = Schedule(
                frequency=ScheduleFrequency.DAILY, enabled=False
            )
            repo.save_new(r, "- [ ] x")
            self.assertEqual(candidates_for(repo, date(2026, 5, 7)), [])

    def test_todo_with_no_due_is_included(self) -> None:
        with TemporaryDirectory() as td:
            repo = _make_repo(td)
            t = repo.create_draft(NoteType.TODO)
            t.title = "Inbox"
            repo.save_new(t, "- [ ] 期限なしタスク")
            items = candidates_for(repo, date(2026, 5, 7))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].text, "期限なしタスク")


class RenderMarkdownTests(unittest.TestCase):
    def test_basic_layout(self) -> None:
        items = [
            PlanItem(source_id="r1", text="朝のルーティン", duration_min=15, kind="routine", note_title="朝のルーティン"),
            PlanItem(source_id="t1", text="仕様書レビュー", duration_min=60, kind="task", note_title="仕様書レビュー"),
            PlanItem(source_id="t2", text="テスト追加", duration_min=30, kind="task", note_title="開発"),
        ]
        md = render_markdown(items, date(2026, 5, 7), start_time="09:00")
        self.assertIn("# 2026-05-07 のプラン", md)
        self.assertIn("## チェックリスト", md)
        self.assertIn("- [ ] 朝のルーティン", md)
        self.assertIn("- [ ] 仕様書レビュー", md)
        self.assertIn("- [ ] テスト追加 (開発)", md)
        self.assertIn("## タイムボックス", md)
        self.assertIn("- 09:00–09:15 朝のルーティン (15m)", md)
        self.assertIn("- 09:15–10:15 仕様書レビュー (60m)", md)
        self.assertIn("- 10:15–10:45 テスト追加 (開発) (30m)", md)

    def test_empty_items(self) -> None:
        md = render_markdown([], date(2026, 5, 7))
        self.assertIn("(候補なし)", md)
        # 2 セクション両方に "(候補なし)" が出る
        self.assertEqual(md.count("(候補なし)"), 2)

    def test_custom_start_time(self) -> None:
        items = [PlanItem(source_id="x", text="x", duration_min=30, kind="task")]
        md = render_markdown(items, date(2026, 5, 7), start_time="13:30")
        self.assertIn("13:30–14:00", md)

    def test_invalid_start_time_falls_back(self) -> None:
        items = [PlanItem(source_id="x", text="x", duration_min=30, kind="task")]
        md = render_markdown(items, date(2026, 5, 7), start_time="bad")
        self.assertIn("09:00–09:30", md)


if __name__ == "__main__":
    unittest.main()
