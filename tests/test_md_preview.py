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

    def _embedded_canvases(self) -> list:
        from notebase.ui.timebox_canvas import TimeboxCanvas

        return [
            w for w in self.renderer._embedded_widgets
            if isinstance(w, TimeboxCanvas)
        ]

    def test_timebox_line_embeds_canvas(self) -> None:
        self.renderer.render("- 09:00–09:15 朝のルーティン (15m)")
        canvases = self._embedded_canvases()
        self.assertEqual(len(canvases), 1)
        items = canvases[0].items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].label, "朝のルーティン")
        self.assertEqual(items[0].duration_min, 15)

    def test_normal_list_item_does_not_embed_canvas(self) -> None:
        self.renderer.render("- ふつうのリスト項目")
        self.assertEqual(self._embedded_canvases(), [])

    def test_timebox_with_hyphen_separator(self) -> None:
        self.renderer.render("- 09:00-09:30 タスク (30m)")
        self.assertEqual(len(self._embedded_canvases()), 1)

    def test_short_form_timebox(self) -> None:
        self.renderer.render("- 9:00–9:30 早朝 (30m)")
        self.assertEqual(len(self._embedded_canvases()), 1)

    def test_consecutive_lines_grouped_into_one_canvas(self) -> None:
        body = (
            "## タイムボックス\n\n"
            "- 09:00–09:15 朝のルーティン (15m)\n"
            "- 09:15–10:15 仕様書レビュー (60m)\n"
            "- 10:15–10:45 テスト追加 (30m)\n"
        )
        self.renderer.render(body)
        canvases = self._embedded_canvases()
        self.assertEqual(len(canvases), 1)
        items = canvases[0].items()
        self.assertEqual([it.duration_min for it in items], [15, 60, 30])
        self.assertEqual(
            [it.label for it in items],
            ["朝のルーティン", "仕様書レビュー", "テスト追加"],
        )


@unittest.skipUnless(_ROOT_AVAILABLE, "Tk root unavailable")
class IndentTagTests(unittest.TestCase):
    """インデント付きリスト/タスクが list_indent_<n> タグを取得することを確認する。"""

    def setUp(self) -> None:
        from notebase.ui.md_preview import MarkdownRenderer

        self.text = tk.Text(_root)
        self.renderer = MarkdownRenderer(self.text, readonly=False)

    def tearDown(self) -> None:
        self.text.destroy()

    def test_top_level_uses_indent_0(self) -> None:
        self.renderer.render("- top item")
        self.assertTrue(self.text.tag_ranges("list_indent_0"))
        self.assertEqual(self.text.tag_ranges("list_indent_1"), ())

    def test_two_space_indent_uses_level_1(self) -> None:
        self.renderer.render("- parent\n  - child")
        self.assertTrue(self.text.tag_ranges("list_indent_0"))
        self.assertTrue(self.text.tag_ranges("list_indent_1"))

    def test_four_space_indent_uses_level_2(self) -> None:
        self.renderer.render("- a\n  - b\n    - c")
        self.assertTrue(self.text.tag_ranges("list_indent_2"))

    def test_task_inherits_indent(self) -> None:
        body = "- [ ] parent\n  - [ ] child A\n  - [x] child B"
        self.renderer.render(body)
        self.assertTrue(self.text.tag_ranges("list_indent_0"))
        self.assertTrue(self.text.tag_ranges("list_indent_1"))

    def test_ordered_list_indent(self) -> None:
        self.renderer.render("1. first\n   2. nested")
        # 3 スペース = 1 レベル (整数化で 1)
        self.assertTrue(self.text.tag_ranges("list_indent_0"))
        self.assertTrue(self.text.tag_ranges("list_indent_1"))


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


@unittest.skipUnless(_ROOT_AVAILABLE, "Tk root unavailable")
class TimeboxCanvasInteractionTests(unittest.TestCase):
    """TimeboxCanvas のドラッグハンドラを直接呼び、状態遷移を検証する。"""

    def setUp(self) -> None:
        from notebase.planning.timebox_format import TimeboxItem
        from notebase.ui.timebox_canvas import TimeboxCanvas

        self._items_seen: list[list] = []
        self.canvas = TimeboxCanvas(
            _root,
            items=[
                TimeboxItem("A", 30),
                TimeboxItem("B", 60),
                TimeboxItem("C", 30),
            ],
            start_time="09:00",
            on_change=lambda items: self._items_seen.append(list(items)),
        )

    def tearDown(self) -> None:
        self.canvas.destroy()

    def _make_event(self, x: int, y: int):
        ev = type("Event", (), {})()
        ev.x = x
        ev.y = y
        return ev

    def test_hit_test_distinguishes_edge_and_body(self) -> None:
        # 0 番目は y=0..60 (30m * 2)。edge は y=54..60、body は y=0..54
        self.assertEqual(self.canvas._hit(10, 5), (0, "body"))
        self.assertEqual(self.canvas._hit(10, 56), (0, "edge"))
        # 1 番目は y=60..180 (60m * 2)。edge は 174..180
        self.assertEqual(self.canvas._hit(10, 100), (1, "body"))
        self.assertEqual(self.canvas._hit(10, 176), (1, "edge"))

    def test_resize_drag_increases_duration(self) -> None:
        # 0 番目の edge を 60px (= +30 分) 下に
        self.canvas._on_press(self._make_event(10, 56))
        self.canvas._on_drag(self._make_event(10, 116))
        self.canvas._on_release(self._make_event(10, 116))
        items = self.canvas.items()
        self.assertEqual(items[0].duration_min, 60)  # 30 + 30
        # コールバックが呼ばれている
        self.assertEqual(len(self._items_seen), 1)

    def test_resize_drag_clamps_to_min_duration(self) -> None:
        # 0 番目の edge を上に大きく動かして minimum (5m) に
        self.canvas._on_press(self._make_event(10, 56))
        self.canvas._on_drag(self._make_event(10, -200))
        self.canvas._on_release(self._make_event(10, -200))
        self.assertEqual(self.canvas.items()[0].duration_min, 5)

    def test_reorder_swap_first_and_third(self) -> None:
        # 0 番目 (A, body) を握り、3 番目の下まで持っていって離す
        self.canvas._on_press(self._make_event(10, 10))
        self.canvas._on_drag(self._make_event(10, 250))  # canvas 末尾より下
        self.canvas._on_release(self._make_event(10, 250))
        items = self.canvas.items()
        # A が末尾に動く
        self.assertEqual([it.label for it in items], ["B", "C", "A"])
        self.assertEqual(len(self._items_seen), 1)

    def test_reorder_no_move_no_callback(self) -> None:
        # body をクリックして同じ位置でリリース
        self.canvas._on_press(self._make_event(10, 10))
        self.canvas._on_release(self._make_event(10, 10))
        self.assertEqual(self._items_seen, [])


def tearDownModule() -> None:
    if _root is not None:
        try:
            _root.destroy()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    unittest.main()
