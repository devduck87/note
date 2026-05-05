from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path

from notebase.core.note_meta import NoteMeta
from notebase.core.note_status import NoteStatus
from notebase.core.note_type import NoteType
from notebase.core.schedule import Schedule, ScheduleFrequency
from notebase.storage import meta_json

_LEGACY_NOTES_DIR = (
    Path(__file__).resolve().parent.parent
    / "NoteBase_csharp"
    / "bin"
    / "Debug"
    / "MemoRoot"
    / "notes"
)


class SerializeTests(unittest.TestCase):
    def test_minimal_memo_matches_expected_format(self) -> None:
        m = NoteMeta(
            id="20260101-120000-foo",
            title="Foo",
            type=NoteType.MEMO,
            status=NoteStatus.ACTIVE,
            tags=["a", "b"],
            created=datetime(2026, 1, 1, 12, 0, 0),
            updated=datetime(2026, 1, 1, 12, 0, 0),
        )
        expected = (
            "{\n"
            '  "meta_version": 1,\n'
            '  "id": "20260101-120000-foo",\n'
            '  "title": "Foo",\n'
            '  "type": "memo",\n'
            '  "status": "active",\n'
            '  "tags": ["a", "b"],\n'
            '  "created": "2026-01-01T12:00:00",\n'
            '  "updated": "2026-01-01T12:00:00"\n'
            "}\n"
        )
        self.assertEqual(meta_json.serialize(m), expected)

    def test_with_schedule(self) -> None:
        m = NoteMeta(
            id="20260415-080000-morning-routine",
            title="朝の作業開始ルーティーン",
            type=NoteType.ROUTINE,
            status=NoteStatus.ACTIVE,
            tags=["routine", "daily"],
            schedule=Schedule(
                frequency=ScheduleFrequency.WEEKLY,
                days=["mon", "tue", "wed", "thu", "fri"],
                enabled=True,
            ),
            created=datetime(2026, 4, 15, 8, 0, 0),
            updated=datetime(2026, 4, 15, 8, 15, 0),
        )
        result = meta_json.serialize(m)
        self.assertIn('  "schedule": {\n', result)
        self.assertIn('    "frequency": "weekly",\n', result)
        self.assertIn(
            '    "days": ["mon", "tue", "wed", "thu", "fri"],\n',
            result,
        )
        self.assertIn('    "enabled": true\n', result)
        self.assertTrue(result.endswith("}\n"))

    def test_optional_fields_omitted_when_empty(self) -> None:
        m = NoteMeta(
            id="x",
            title="t",
            type=NoteType.MEMO,
            tags=[],
            created=datetime(2026, 1, 1),
            updated=datetime(2026, 1, 1),
        )
        result = meta_json.serialize(m)
        self.assertNotIn("status", result)
        self.assertNotIn("project", result)
        self.assertNotIn("due", result)
        self.assertNotIn("schedule", result)
        self.assertNotIn("instance_of", result)
        self.assertIn('"tags": []', result)

    def test_string_escapes(self) -> None:
        m = NoteMeta(
            id="x",
            title='He said "hi"\nand left',
            type=NoteType.MEMO,
            tags=[],
            created=datetime(2026, 1, 1),
            updated=datetime(2026, 1, 1),
        )
        result = meta_json.serialize(m)
        self.assertIn(r'"title": "He said \"hi\"\nand left"', result)


class DeserializeTests(unittest.TestCase):
    def test_round_trip_minimal(self) -> None:
        m = NoteMeta(
            id="x",
            title="t",
            type=NoteType.MEMO,
            tags=[],
            created=datetime(2026, 1, 1),
            updated=datetime(2026, 1, 1),
        )
        text = meta_json.serialize(m)
        m2 = meta_json.deserialize(text)
        self.assertEqual(m2.id, "x")
        self.assertEqual(m2.title, "t")
        self.assertEqual(m2.type, NoteType.MEMO)
        self.assertEqual(m2.tags, [])

    def test_round_trip_with_schedule(self) -> None:
        m = NoteMeta(
            id="x",
            title="t",
            type=NoteType.ROUTINE,
            status=NoteStatus.ACTIVE,
            tags=["a"],
            schedule=Schedule(
                frequency=ScheduleFrequency.MONTHLY,
                day_of_month=15,
                enabled=False,
            ),
            created=datetime(2026, 1, 1),
            updated=datetime(2026, 1, 2),
        )
        text = meta_json.serialize(m)
        m2 = meta_json.deserialize(text)
        self.assertEqual(m2.schedule.frequency, ScheduleFrequency.MONTHLY)
        self.assertEqual(m2.schedule.day_of_month, 15)
        self.assertFalse(m2.schedule.enabled)

    def test_unknown_type_falls_back_to_memo(self) -> None:
        text = (
            "{\n"
            '  "meta_version": 1,\n'
            '  "id": "x",\n'
            '  "title": "t",\n'
            '  "type": "weird",\n'
            '  "tags": [],\n'
            '  "created": "2026-01-01T00:00:00",\n'
            '  "updated": "2026-01-01T00:00:00"\n'
            "}\n"
        )
        m = meta_json.deserialize(text)
        self.assertEqual(m.type, NoteType.MEMO)


@unittest.skipUnless(
    _LEGACY_NOTES_DIR.exists(),
    f"legacy notes dir not found: {_LEGACY_NOTES_DIR}",
)
class LegacyRoundTripTests(unittest.TestCase):
    """C# 版が書いた meta.json を読み → 書き戻したらバイト一致することを検証する。"""

    def test_all_legacy_meta_round_trip(self) -> None:
        for note_dir in sorted(_LEGACY_NOTES_DIR.iterdir()):
            meta_path = note_dir / "meta.json"
            if not meta_path.exists():
                continue
            with self.subTest(note=note_dir.name):
                original = meta_path.read_text(encoding="utf-8")
                m = meta_json.deserialize(original)
                rewritten = meta_json.serialize(m)
                self.assertEqual(
                    rewritten,
                    original,
                    f"round-trip mismatch for {meta_path}",
                )


if __name__ == "__main__":
    unittest.main()
