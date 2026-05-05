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


def tearDownModule() -> None:
    if _root is not None:
        try:
            _root.destroy()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    unittest.main()
