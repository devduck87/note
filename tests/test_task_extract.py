from __future__ import annotations

import unittest
from datetime import date

from notebase.planning.task_extract import extract_tasks


class ExtractTasksTests(unittest.TestCase):
    def test_extracts_open_and_done(self) -> None:
        body = "- [ ] open task\n- [x] done task"
        tasks = extract_tasks("nid", "Title", body)
        self.assertEqual(len(tasks), 2)
        self.assertFalse(tasks[0].completed)
        self.assertTrue(tasks[1].completed)
        self.assertEqual(tasks[0].text, "open task")
        self.assertEqual(tasks[1].text, "done task")

    def test_due_date_extracted(self) -> None:
        tasks = extract_tasks("nid", "T", "- [ ] レビュー @2026-05-10")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].due_date, date(2026, 5, 10))
        self.assertEqual(tasks[0].text, "レビュー")

    def test_no_due_date(self) -> None:
        tasks = extract_tasks("nid", "T", "- [ ] no date")
        self.assertEqual(tasks[0].due_date, None)

    def test_invalid_date_ignored(self) -> None:
        tasks = extract_tasks("nid", "T", "- [ ] x @2026-13-99")
        self.assertEqual(tasks[0].due_date, None)
        # 不正な日付でも記法は除去される
        self.assertNotIn("@", tasks[0].text)

    def test_strips_block_id_from_text(self) -> None:
        tasks = extract_tasks("nid", "T", "- [ ] task body ^abc123")
        self.assertEqual(tasks[0].text, "task body")

    def test_skips_inside_code_fence(self) -> None:
        body = "- [ ] real\n```\n- [ ] fake\n```\n- [ ] also"
        tasks = extract_tasks("nid", "T", body)
        self.assertEqual([t.text for t in tasks], ["real", "also"])

    def test_line_index_set(self) -> None:
        body = "intro\n\n- [ ] first\n- [ ] second"
        tasks = extract_tasks("nid", "T", body)
        self.assertEqual([t.line_index for t in tasks], [2, 3])

    def test_empty_body(self) -> None:
        self.assertEqual(extract_tasks("nid", "T", ""), [])
        self.assertEqual(extract_tasks("nid", "T", None), [])


if __name__ == "__main__":
    unittest.main()
