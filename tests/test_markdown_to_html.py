from __future__ import annotations

import unittest

from notebase.markdown.to_html import convert


class HeadingTests(unittest.TestCase):
    def test_h1_with_slug_id(self) -> None:
        self.assertEqual(convert("# Hello World"), '<h1 id="hello-world">Hello World</h1>\n')

    def test_h2(self) -> None:
        self.assertEqual(convert("## Sub"), '<h2 id="sub">Sub</h2>\n')


class ParagraphTests(unittest.TestCase):
    def test_simple(self) -> None:
        self.assertEqual(convert("hello"), "<p>hello</p>\n")

    def test_multi_line_uses_br(self) -> None:
        self.assertEqual(convert("a\nb"), "<p>a<br/>b</p>\n")

    def test_block_id_on_paragraph(self) -> None:
        self.assertEqual(convert("hello ^abc"), '<p id="abc">hello</p>\n')


class ListTests(unittest.TestCase):
    def test_ul(self) -> None:
        self.assertEqual(convert("- a\n- b"), "<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n")

    def test_ol(self) -> None:
        self.assertEqual(convert("1. a\n2. b"), "<ol>\n<li>a</li>\n<li>b</li>\n</ol>\n")

    def test_task(self) -> None:
        result = convert("- [ ] open\n- [x] done")
        self.assertIn('<ul class="task-list">', result)
        self.assertIn('<input type="checkbox" disabled/> open', result)
        self.assertIn('<input type="checkbox" disabled checked/> done', result)


class InlineTests(unittest.TestCase):
    def test_bold(self) -> None:
        self.assertEqual(convert("**a**"), "<p><strong>a</strong></p>\n")

    def test_italic(self) -> None:
        self.assertEqual(convert("*a*"), "<p><em>a</em></p>\n")

    def test_code(self) -> None:
        self.assertEqual(convert("`x`"), "<p><code>x</code></p>\n")

    def test_link(self) -> None:
        self.assertEqual(
            convert("[t](http://e.x)"),
            '<p><a href="http://e.x">t</a></p>\n',
        )

    def test_image(self) -> None:
        self.assertEqual(
            convert("![alt](img.png)"),
            '<p><img src="img.png" alt="alt"/></p>\n',
        )

    def test_html_escape_in_text(self) -> None:
        self.assertEqual(
            convert("<script>"),
            "<p>&lt;script&gt;</p>\n",
        )


class WikiLinkTests(unittest.TestCase):
    def test_unresolved(self) -> None:
        self.assertEqual(
            convert("[[Foo]]"),
            '<p><span class="unresolved-link">[[Foo]]</span></p>\n',
        )

    def test_resolved(self) -> None:
        result = convert("[[Foo]]", title_resolver=lambda t: "20260101-120000-foo")
        self.assertEqual(
            result,
            '<p><a href="../20260101-120000-foo/index.md">Foo</a></p>\n',
        )

    def test_resolved_with_alias(self) -> None:
        result = convert("[[Foo|see this]]", title_resolver=lambda t: "20260101-120000-foo")
        self.assertEqual(
            result,
            '<p><a href="../20260101-120000-foo/index.md">see this</a></p>\n',
        )

    def test_resolved_with_anchor(self) -> None:
        result = convert("[[Foo#sec1]]", title_resolver=lambda t: "20260101-120000-foo")
        self.assertEqual(
            result,
            '<p><a href="../20260101-120000-foo/index.md#sec1">Foo &gt; sec1</a></p>\n',
        )

    def test_same_note_anchor(self) -> None:
        self.assertEqual(
            convert("[[#sec1]]"),
            '<p><a href="#sec1">sec1</a></p>\n',
        )


class CodeFenceTests(unittest.TestCase):
    def test_no_lang(self) -> None:
        result = convert("```\nx\n```")
        self.assertEqual(result, "<pre><code>x\n</code></pre>\n")

    def test_with_lang(self) -> None:
        result = convert("```python\nprint(1)\n```")
        self.assertEqual(
            result,
            '<pre><code class="language-python">print(1)\n</code></pre>\n',
        )


class HrTests(unittest.TestCase):
    def test_hr(self) -> None:
        self.assertEqual(convert("---"), "<hr/>\n")


if __name__ == "__main__":
    unittest.main()
