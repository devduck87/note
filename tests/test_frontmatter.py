"""frontmatter parser / serializer / NoteMeta ブリッジのテスト。"""
from __future__ import annotations

import unittest
from datetime import datetime

from notebase.core.note_meta import NoteMeta
from notebase.core.note_status import NoteStatus
from notebase.core.note_type import NoteType
from notebase.core.schedule import Schedule, ScheduleFrequency
from notebase.markdown import frontmatter as fm


class SplitTests(unittest.TestCase):
    def test_no_frontmatter(self) -> None:
        text = "# Hello\nbody\n"
        self.assertEqual(fm.split_frontmatter(text), (None, text))

    def test_simple(self) -> None:
        text = "---\ntitle: T\n---\n# body\n"
        head, body = fm.split_frontmatter(text)
        self.assertEqual(head, "title: T")
        self.assertEqual(body, "# body\n")

    def test_unclosed_fence(self) -> None:
        text = "---\ntitle: T\n# body\n"
        self.assertEqual(fm.split_frontmatter(text), (None, text))

    def test_empty_body(self) -> None:
        text = "---\ntitle: T\n---\n"
        head, body = fm.split_frontmatter(text)
        self.assertEqual(head, "title: T")
        self.assertEqual(body, "")


class ParseTests(unittest.TestCase):
    def test_scalars(self) -> None:
        d = fm.parse_frontmatter(
            "title: hello\ncount: 3\nactive: true\nempty:\nx: null"
        )
        self.assertEqual(d, {
            "title": "hello",
            "count": 3,
            "active": True,
            "empty": None,
            "x": None,
        })

    def test_quoted_string(self) -> None:
        d = fm.parse_frontmatter('note: "with, comma"')
        self.assertEqual(d, {"note": "with, comma"})

    def test_inline_array(self) -> None:
        d = fm.parse_frontmatter("tags: [a, b, c]")
        self.assertEqual(d, {"tags": ["a", "b", "c"]})

    def test_inline_object(self) -> None:
        d = fm.parse_frontmatter("schedule: {frequency: weekly, enabled: true}")
        self.assertEqual(d, {"schedule": {"frequency": "weekly", "enabled": True}})

    def test_nested_object_with_array(self) -> None:
        d = fm.parse_frontmatter("schedule: {days: [mon, tue], enabled: false}")
        self.assertEqual(d, {"schedule": {"days": ["mon", "tue"], "enabled": False}})

    def test_skip_invalid_lines(self) -> None:
        d = fm.parse_frontmatter("title: ok\nbroken line without colon\n# comment\nother: yes")
        self.assertEqual(d, {"title": "ok", "other": "yes"})


class SerializeTests(unittest.TestCase):
    def test_roundtrip_simple(self) -> None:
        d = {"title": "hello", "tags": ["a", "b"], "count": 3}
        s = fm.serialize_frontmatter(d)
        head, _ = fm.split_frontmatter(s + "\nbody")
        self.assertIsNotNone(head)
        parsed = fm.parse_frontmatter(head)  # type: ignore[arg-type]
        self.assertEqual(parsed, d)

    def test_quote_when_needed(self) -> None:
        d = {"note": "has, comma"}
        s = fm.serialize_frontmatter(d)
        self.assertIn('"has, comma"', s)
        head, _ = fm.split_frontmatter(s + "\nbody")
        parsed = fm.parse_frontmatter(head)  # type: ignore[arg-type]
        self.assertEqual(parsed, d)


class MetaBridgeTests(unittest.TestCase):
    def test_meta_to_dict_includes_optional_fields(self) -> None:
        meta = NoteMeta(
            id="x",
            title="T",
            type=NoteType.LOG,
            status=NoteStatus.ACTIVE,
            tags=["a", "b"],
            project="p",
            due=datetime(2026, 5, 15),
            estimated_minutes=30,
            actual_minutes=25,
            created=datetime(2026, 1, 1),
            updated=datetime(2026, 1, 1),
        )
        d = fm.meta_to_dict(meta)
        self.assertEqual(d["title"], "T")
        self.assertEqual(d["type"], "log")
        self.assertEqual(d["status"], "active")
        self.assertEqual(d["tags"], ["a", "b"])
        self.assertEqual(d["project"], "p")
        self.assertEqual(d["due"], "2026-05-15")
        self.assertEqual(d["estimated_minutes"], 30)
        self.assertEqual(d["actual_minutes"], 25)
        # id / created / updated は出力しない
        self.assertNotIn("id", d)
        self.assertNotIn("created", d)

    def test_meta_to_dict_with_schedule(self) -> None:
        meta = NoteMeta(
            id="r",
            title="R",
            type=NoteType.ROUTINE,
            schedule=Schedule(
                frequency=ScheduleFrequency.WEEKLY,
                days=["mon", "tue"],
                enabled=True,
            ),
        )
        d = fm.meta_to_dict(meta)
        self.assertEqual(
            d["schedule"],
            {"frequency": "weekly", "days": ["mon", "tue"], "enabled": True},
        )

    def test_apply_dict_overwrites_known_fields(self) -> None:
        meta = NoteMeta(id="x", title="old", type=NoteType.MEMO)
        fm.apply_dict_to_meta(
            {
                "title": "new",
                "type": "todo",
                "status": "done",
                "tags": ["x"],
                "due": "2026-06-01",
                "estimated_minutes": 15,
            },
            meta,
        )
        self.assertEqual(meta.title, "new")
        self.assertEqual(meta.type, NoteType.TODO)
        self.assertEqual(meta.status, NoteStatus.DONE)
        self.assertEqual(meta.tags, ["x"])
        self.assertEqual(meta.due, datetime(2026, 6, 1))
        self.assertEqual(meta.estimated_minutes, 15)

    def test_apply_dict_with_schedule(self) -> None:
        meta = NoteMeta(id="x", title="r", type=NoteType.ROUTINE)
        fm.apply_dict_to_meta(
            {"schedule": {"frequency": "monthly", "day_of_month": 5, "enabled": True}},
            meta,
        )
        self.assertIsNotNone(meta.schedule)
        assert meta.schedule is not None  # for type checker
        self.assertEqual(meta.schedule.frequency, ScheduleFrequency.MONTHLY)
        self.assertEqual(meta.schedule.day_of_month, 5)
        self.assertTrue(meta.schedule.enabled)

    def test_legacy_checklist_type_via_apply(self) -> None:
        meta = NoteMeta(id="x", title="t", type=NoteType.MEMO)
        fm.apply_dict_to_meta({"type": "checklist"}, meta)
        self.assertEqual(meta.type, NoteType.PROCEDURE)

    def test_full_roundtrip_via_combine_split(self) -> None:
        meta = NoteMeta(
            id="x",
            title="検索ツール",
            type=NoteType.LOG,
            status=NoteStatus.ACTIVE,
            tags=["excel", "search"],
            project="excel-search-tool",
            estimated_minutes=45,
        )
        body = "# 検索ツール\n\n## 詳細\n本文\n"
        text = fm.combine(fm.meta_to_dict(meta), body)
        head, body2 = fm.split_frontmatter(text)
        self.assertEqual(body2, body)
        d = fm.parse_frontmatter(head)  # type: ignore[arg-type]
        meta2 = NoteMeta(id="x", title="", type=NoteType.MEMO)
        fm.apply_dict_to_meta(d, meta2)
        self.assertEqual(meta2.title, meta.title)
        self.assertEqual(meta2.type, meta.type)
        self.assertEqual(meta2.tags, meta.tags)
        self.assertEqual(meta2.project, meta.project)
        self.assertEqual(meta2.estimated_minutes, meta.estimated_minutes)


if __name__ == "__main__":
    unittest.main()
