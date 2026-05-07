from __future__ import annotations

import os
import unittest

# Tkinter は GUI が無いと動かないので、ヘッドレス環境ではテストをスキップする。
try:
    import tkinter as tk

    _root = tk.Tk()
    _root.withdraw()
    _root.update_idletasks()
    _ROOT_AVAILABLE = True
except Exception:  # noqa: BLE001
    _root = None  # type: ignore[assignment]
    _ROOT_AVAILABLE = False


@unittest.skipUnless(_ROOT_AVAILABLE, "Tk root unavailable")
class MarkdownRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        from notebase.ui.md_preview import MarkdownRenderer

        self._renderer_cls = MarkdownRenderer
        self.text = tk.Text(_root)

    def tearDown(self) -> None:
        self.text.destroy()

    def _render(self, body: str, **kwargs):
        renderer = self._renderer_cls(self.text, readonly=False, **kwargs)
        renderer.render(body)
        return renderer

    def test_renders_heading_text(self) -> None:
        self._render("# Hello")
        content = self.text.get("1.0", "end-1c")
        self.assertIn("Hello", content)
        self.assertNotIn("#", content)  # 装飾記号は描画しない

    def test_renders_paragraph(self) -> None:
        self._render("just text")
        self.assertIn("just text", self.text.get("1.0", "end-1c"))

    def test_renders_list_with_marker(self) -> None:
        self._render("- a\n- b")
        content = self.text.get("1.0", "end-1c")
        self.assertIn("• a", content)
        self.assertIn("• b", content)

    def test_renders_task_with_marker(self) -> None:
        self._render("- [ ] open\n- [x] done")
        content = self.text.get("1.0", "end-1c")
        self.assertIn("☐ open", content)
        self.assertIn("☑ done", content)

    def test_link_creates_handler_tag(self) -> None:
        clicks: list[str] = []
        renderer = self._render(
            "[click](http://example.com)",
            on_link_click=lambda info: clicks.append(info.raw_url),
        )
        # link_1 タグが作成されているはず
        self.assertEqual(len(renderer._link_tags), 1)

    def test_resolved_wiki_link(self) -> None:
        self._render("[[Foo]]", title_resolver=lambda t: "20260101-x")
        content = self.text.get("1.0", "end-1c")
        self.assertIn("Foo", content)

    def test_unresolved_wiki_link_keeps_brackets(self) -> None:
        self._render("[[Unknown]]")
        content = self.text.get("1.0", "end-1c")
        self.assertIn("[[Unknown]]", content)

    def test_anchor_tag_for_heading(self) -> None:
        self._render("# Sub Title")
        # slugify("Sub Title") = "sub-title"
        self.assertTrue(self.text.tag_ranges("anchor:sub-title"))

    def test_anchor_tag_for_block_id(self) -> None:
        self._render("paragraph ^abc123")
        self.assertTrue(self.text.tag_ranges("anchor:abc123"))


@unittest.skipUnless(_ROOT_AVAILABLE, "Tk root unavailable")
class TimeboxRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        from notebase.ui.md_preview import MarkdownRenderer

        self.text = tk.Text(_root)
        self.renderer = MarkdownRenderer(self.text, readonly=False)

    def tearDown(self) -> None:
        self.text.destroy()

    def test_timebox_line_gets_timebox_tag(self) -> None:
        self.renderer.render("- 09:00–09:15 朝のルーティン (15m)")
        self.assertTrue(self.text.tag_ranges("timebox"))

    def test_timebox_time_tag_applied(self) -> None:
        self.renderer.render("- 09:00–09:15 朝のルーティン (15m)")
        self.assertTrue(self.text.tag_ranges("timebox_time"))
        self.assertTrue(self.text.tag_ranges("timebox_min"))

    def test_normal_list_item_has_no_timebox_tag(self) -> None:
        self.renderer.render("- ふつうのリスト項目")
        self.assertEqual(self.text.tag_ranges("timebox"), ())

    def test_timebox_with_hyphen_separator(self) -> None:
        self.renderer.render("- 09:00-09:30 タスク (30m)")
        self.assertTrue(self.text.tag_ranges("timebox"))

    def test_short_form_timebox(self) -> None:
        self.renderer.render("- 9:00–9:30 早朝 (30m)")
        self.assertTrue(self.text.tag_ranges("timebox"))

    def test_full_section_renders(self) -> None:
        body = (
            "## タイムボックス\n\n"
            "- 09:00–09:15 朝のルーティン (15m)\n"
            "- 09:15–10:15 仕様書レビュー (60m)\n"
            "- 10:15–10:45 テスト追加 (30m)\n"
        )
        self.renderer.render(body)
        content = self.text.get("1.0", "end-1c")
        self.assertIn("09:00 – 09:15", content)
        self.assertIn("09:15 – 10:15", content)
        self.assertIn("10:15 – 10:45", content)
        self.assertIn("(15m)", content)
        self.assertIn("(60m)", content)
        self.assertIn("(30m)", content)


@unittest.skipUnless(_ROOT_AVAILABLE, "Tk root unavailable")
class TaskClickableTests(unittest.TestCase):
    def setUp(self) -> None:
        from notebase.ui.md_preview import MarkdownRenderer

        self._renderer_cls = MarkdownRenderer
        self.text = tk.Text(_root)
        self.toggled: list[int] = []
        self.renderer = MarkdownRenderer(
            self.text,
            readonly=False,
            on_task_toggle=lambda line: self.toggled.append(line),
        )

    def tearDown(self) -> None:
        self.text.destroy()

    def test_task_creates_clickable_tag(self) -> None:
        self.renderer.render("- [ ] task A")
        self.assertEqual(len(self.renderer._task_tags), 1)

    def test_task_click_invokes_callback(self) -> None:
        body = "- [ ] task A\n- [x] task B"
        self.renderer.render(body)
        self.assertEqual(len(self.renderer._task_tags), 2)
        self.renderer._handle_task_click(0)
        self.renderer._handle_task_click(1)
        self.assertEqual(self.toggled, [0, 1])

    def test_no_callback_means_no_task_tag(self) -> None:
        renderer = self._renderer_cls(self.text, readonly=False)
        renderer.render("- [ ] x")
        self.assertEqual(renderer._task_tags, [])


def tearDownModule() -> None:
    if _root is not None:
        try:
            _root.destroy()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    unittest.main()
