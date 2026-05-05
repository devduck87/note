"""Markdown を Tk Text ウィジェットにタグ付きで描画するレンダラ。

C# 版は WebBrowser コントロールに HTML を流し込んでいたが、
Python 版は標準ライブラリのみという制約から Tk Text 上に直接描画する。
"""

from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import font as tkfont
from typing import Callable

from ..markdown.md_index import slugify_heading

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_HR_RE = re.compile(r"^(\-{3,}|\*{3,}|_{3,})$")
_TASK_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$")
_UL_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
_OL_RE = re.compile(r"^\s*\d+\.\s+(.+)$")
_IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)")
_LINK_RE = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)")
_NOTE_ID_IN_URL_RE = re.compile(r"(?:^|/)([^/]+)/index\.md$", re.IGNORECASE)
_BLOCK_ID_TAIL_RE = re.compile(r"\s+\^([a-zA-Z0-9-]+)\s*$")


@dataclass
class LinkInfo:
    """クリック/ホバーハンドラに渡すリンク情報。"""

    raw_url: str
    """元の Markdown 上の URL ([text](url) の url や [[Title#anchor]] から組み立てた相対パス)。"""

    target_note_id: str | None
    """リンク先がノートなら ID、それ以外は None。"""

    anchor: str | None
    """フラグメント (見出しスラグまたはブロック ID)。"""

    text: str
    """リンクとして表示されているテキスト。"""


class MarkdownRenderer:
    """Markdown 文字列を Tk Text ウィジェットに描画する。

    - 見出し / 段落 / リスト / タスクリスト / コードフェンス / 水平線 / 強調 / 斜体 /
      インラインコード / リンク / Wiki リンク / 画像 / ブロック ID をサポート。
    - 画像は PNG/GIF のみインライン表示 (Tk PhotoImage の制約)。それ以外は
      "[image: <path>]" のプレースホルダ。
    - リンクには tag_bind で <Button-1>/<Enter>/<Leave> を結びつけ、外部ハンドラへ転送する。
    """

    def __init__(
        self,
        text: tk.Text,
        *,
        on_link_click: Callable[[LinkInfo], None] | None = None,
        on_link_hover: Callable[[LinkInfo, tk.Event], None] | None = None,
        on_link_leave: Callable[[LinkInfo, tk.Event], None] | None = None,
        title_resolver: Callable[[str], str | None] | None = None,
        base_dir: str | Path | None = None,
        readonly: bool = True,
    ) -> None:
        self._text = text
        self._on_link_click = on_link_click
        self._on_link_hover = on_link_hover
        self._on_link_leave = on_link_leave
        self._title_resolver = title_resolver
        self._base_dir = Path(base_dir) if base_dir else None
        self._readonly = readonly

        self._link_tags: list[str] = []
        self._link_counter = 0
        self._images: list[tk.PhotoImage] = []
        self._configure_tags()

    # ------------------------------------------------------------
    # public
    # ------------------------------------------------------------

    def render(self, markdown: str | None) -> None:
        """ウィジェットの内容を markdown のレンダリング結果で置き換える。"""
        text = self._text
        # 既存のリンク用タグを破棄 (画像 PhotoImage への参照も解放)
        for tag in self._link_tags:
            try:
                text.tag_delete(tag)
            except tk.TclError:
                pass
        self._link_tags.clear()
        self._images.clear()
        self._link_counter = 0

        text.config(state="normal")
        text.delete("1.0", "end")

        if markdown:
            normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
            self._render_blocks(normalized.split("\n"))

        if self._readonly:
            text.config(state="disabled")

    def scroll_to_anchor(self, anchor: str) -> bool:
        """指定アンカー (見出しスラグ または ブロック ID) の位置までスクロールする。

        該当が無ければ False、見つかれば True。
        """
        ranges = self._text.tag_ranges(f"anchor:{anchor}")
        if not ranges:
            return False
        self._text.see(ranges[0])
        return True

    # ------------------------------------------------------------
    # tags
    # ------------------------------------------------------------

    def _configure_tags(self) -> None:
        text = self._text
        # 既定フォントから派生サイズを決める
        try:
            base_family = tkfont.Font(font=text.cget("font")).cget("family")
        except tk.TclError:
            base_family = "Helvetica"

        text.tag_configure("h1", font=(base_family, 18, "bold"), spacing1=8, spacing3=4)
        text.tag_configure("h2", font=(base_family, 15, "bold"), spacing1=6, spacing3=3)
        text.tag_configure("h3", font=(base_family, 13, "bold"), spacing1=5, spacing3=3)
        text.tag_configure("h4", font=(base_family, 11, "bold"), spacing1=4, spacing3=2)
        text.tag_configure("h5", font=(base_family, 11, "bold"), spacing1=3, spacing3=2)
        text.tag_configure("h6", font=(base_family, 10, "bold italic"), spacing1=2, spacing3=2)

        text.tag_configure("para", spacing3=6, lmargin1=2, lmargin2=2)
        text.tag_configure("strong", font=(base_family, 10, "bold"))
        text.tag_configure("em", font=(base_family, 10, "italic"))
        text.tag_configure(
            "code",
            font=("Consolas", 10),
            background="#f0f0f0",
        )
        text.tag_configure(
            "code_block",
            font=("Consolas", 10),
            background="#f7f7f7",
            lmargin1=12,
            lmargin2=12,
            spacing1=4,
            spacing3=4,
        )
        text.tag_configure("hr", justify="center", foreground="#888888")
        text.tag_configure(
            "list_item", lmargin1=12, lmargin2=28, spacing3=2
        )
        text.tag_configure("list_marker", foreground="#666666")

        text.tag_configure("link", foreground="#0050d0", underline=True)
        text.tag_configure(
            "unresolved_link", foreground="#cc4040", underline=True
        )
        text.tag_configure("image_placeholder", foreground="#666666")

    # ------------------------------------------------------------
    # block-level
    # ------------------------------------------------------------

    def _render_blocks(self, lines: list[str]) -> None:
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]

            if not line.strip():
                i += 1
                continue

            if line.startswith("```"):
                lang = line[3:].strip()
                code_lines: list[str] = []
                i += 1
                while i < n and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                if i < n:
                    i += 1
                self._insert_code_block(code_lines, lang)
                continue

            if _HR_RE.match(line.strip()):
                self._insert_text("─" * 40 + "\n", ("hr",))
                i += 1
                continue

            h = _HEADING_RE.match(line)
            if h:
                level = len(h.group(1))
                raw_text = h.group(2)
                slug = slugify_heading(raw_text)
                anchor_tag = f"anchor:{slug}" if slug else None
                tag_name = f"h{level}"
                self._render_heading(raw_text, tag_name, anchor_tag)
                i += 1
                continue

            t = _TASK_RE.match(line)
            if t:
                checked = t.group(1).lower() == "x"
                content, block_id = _strip_block_id(t.group(2))
                marker = "☑ " if checked else "☐ "
                self._render_list_item(marker, content, block_id)
                i += 1
                continue

            ul = _UL_RE.match(line)
            if ul:
                content, block_id = _strip_block_id(ul.group(1))
                self._render_list_item("• ", content, block_id)
                i += 1
                continue

            ol = _OL_RE.match(line)
            if ol:
                content, block_id = _strip_block_id(ol.group(1))
                # 番号は元のリテラルを保持
                marker = line.lstrip()[: line.lstrip().find(".") + 2]
                self._render_list_item(marker, content, block_id)
                i += 1
                continue

            # 段落
            para_lines = [line]
            i += 1
            while i < n:
                lj = lines[i]
                if not lj.strip():
                    break
                if (
                    lj.startswith("#")
                    or lj.startswith("```")
                    or _UL_RE.match(lj)
                    or _OL_RE.match(lj)
                    or _TASK_RE.match(lj)
                    or _HR_RE.match(lj.strip())
                ):
                    break
                para_lines.append(lj)
                i += 1
            last_idx = len(para_lines) - 1
            stripped, block_id = _strip_block_id(para_lines[last_idx])
            para_lines[last_idx] = stripped
            self._render_paragraph(para_lines, block_id)

    def _insert_code_block(self, code_lines: list[str], lang: str) -> None:
        body = "\n".join(code_lines)
        if not body.endswith("\n"):
            body += "\n"
        self._insert_text(body, ("code_block",))

    def _render_heading(
        self,
        raw_text: str,
        tag: str,
        anchor_tag: str | None,
    ) -> None:
        start = self._text.index("end-1c")
        self._render_inline(raw_text, base_tags=(tag,))
        self._insert_text("\n", (tag,))
        if anchor_tag:
            end = self._text.index("end-1c")
            self._text.tag_add(anchor_tag, start, end)

    def _render_list_item(
        self, marker: str, content: str, block_id: str | None
    ) -> None:
        start = self._text.index("end-1c")
        self._insert_text(marker, ("list_item", "list_marker"))
        self._render_inline(content, base_tags=("list_item",))
        self._insert_text("\n", ("list_item",))
        if block_id:
            end = self._text.index("end-1c")
            self._text.tag_add(f"anchor:{block_id}", start, end)

    def _render_paragraph(
        self, para_lines: list[str], block_id: str | None
    ) -> None:
        start = self._text.index("end-1c")
        for k, pl in enumerate(para_lines):
            if k > 0:
                self._insert_text("\n", ("para",))
            self._render_inline(pl, base_tags=("para",))
        self._insert_text("\n\n", ("para",))
        if block_id:
            end = self._text.index("end-1c")
            self._text.tag_add(f"anchor:{block_id}", start, end)

    # ------------------------------------------------------------
    # inline
    # ------------------------------------------------------------

    def _render_inline(self, text: str, *, base_tags: tuple[str, ...]) -> None:
        if not text:
            return
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]

            # インラインコード
            if ch == "`":
                end = text.find("`", i + 1)
                if end > i:
                    self._insert_text(text[i + 1 : end], base_tags + ("code",))
                    i = end + 1
                    continue

            # 画像 ![alt](src)
            if ch == "!" and i + 1 < n and text[i + 1] == "[":
                m = _IMAGE_RE.match(text[i:])
                if m:
                    self._insert_image(m.group(1), m.group(2), base_tags)
                    i += m.end()
                    continue

            # Wiki link [[...]]
            if ch == "[" and i + 1 < n and text[i + 1] == "[":
                end = text.find("]]", i + 2)
                if end > i + 1:
                    inner = text[i + 2 : end]
                    self._insert_wiki_link(inner, base_tags)
                    i = end + 2
                    continue

            # リンク [text](url)
            if ch == "[":
                m = _LINK_RE.match(text[i:])
                if m:
                    self._insert_link(m.group(1), m.group(2), base_tags)
                    i += m.end()
                    continue

            # **bold**
            if i + 1 < n and ch == "*" and text[i + 1] == "*":
                end = text.find("**", i + 2)
                if end > i:
                    self._render_inline(text[i + 2 : end], base_tags=base_tags + ("strong",))
                    i = end + 2
                    continue

            # *italic*
            if ch == "*":
                end = text.find("*", i + 1)
                if end > i:
                    self._render_inline(text[i + 1 : end], base_tags=base_tags + ("em",))
                    i = end + 1
                    continue

            self._insert_text(ch, base_tags)
            i += 1

    def _insert_text(self, s: str, tags: tuple[str, ...]) -> None:
        if s:
            self._text.insert("end", s, tags)

    def _insert_link(
        self, label: str, url: str, base_tags: tuple[str, ...]
    ) -> None:
        target_id = _extract_note_id_from_url(url)
        anchor = _extract_anchor(url)
        info = LinkInfo(
            raw_url=url, target_note_id=target_id, anchor=anchor, text=label
        )
        tag = self._make_link_tag(info)
        # ラベル内のインライン要素も処理する
        start = self._text.index("end-1c")
        self._render_inline(label, base_tags=base_tags + ("link", tag))
        end = self._text.index("end-1c")
        # ラベル全体に link タグが乗るように再付与
        self._text.tag_add("link", start, end)
        self._text.tag_add(tag, start, end)

    def _insert_wiki_link(
        self, inner: str, base_tags: tuple[str, ...]
    ) -> None:
        pipe_idx = inner.find("|")
        if pipe_idx >= 0:
            main = inner[:pipe_idx].strip()
            alias: str | None = inner[pipe_idx + 1 :].strip()
        else:
            main = inner.strip()
            alias = None

        hash_idx = main.find("#")
        if hash_idx >= 0:
            title = main[:hash_idx].strip()
            anchor: str | None = main[hash_idx + 1 :].strip()
            if anchor.startswith("^"):
                anchor = anchor[1:]
        else:
            title = main
            anchor = None

        if not title:
            # 同一ノート内アンカー
            if anchor:
                display = alias or anchor
                info = LinkInfo(
                    raw_url=f"#{anchor}",
                    target_note_id=None,
                    anchor=anchor,
                    text=display,
                )
                tag = self._make_link_tag(info)
                self._insert_text(display, base_tags + ("link", tag))
            return

        resolved = self._title_resolver(title) if self._title_resolver else None
        if resolved:
            display = alias if alias else (f"{title} > {anchor}" if anchor else title)
            raw = f"../{resolved}/index.md" + (f"#{anchor}" if anchor else "")
            info = LinkInfo(
                raw_url=raw, target_note_id=resolved, anchor=anchor, text=display
            )
            tag = self._make_link_tag(info)
            self._insert_text(display, base_tags + ("link", tag))
        else:
            self._insert_text(f"[[{inner}]]", base_tags + ("unresolved_link",))

    def _make_link_tag(self, info: LinkInfo) -> str:
        self._link_counter += 1
        tag = f"link_{self._link_counter}"
        self._link_tags.append(tag)
        text = self._text

        text.tag_configure(tag)  # 個別装飾なし。共通スタイルは "link" タグが提供
        text.tag_bind(tag, "<Enter>", lambda e, i=info: self._handle_enter(e, i))
        text.tag_bind(tag, "<Leave>", lambda e, i=info: self._handle_leave(e, i))
        text.tag_bind(tag, "<Button-1>", lambda e, i=info: self._handle_click(e, i))
        return tag

    def _handle_click(self, event: tk.Event, info: LinkInfo) -> None:
        if self._on_link_click:
            self._on_link_click(info)

    def _handle_enter(self, event: tk.Event, info: LinkInfo) -> None:
        try:
            self._text.config(cursor="hand2")
        except tk.TclError:
            pass
        if self._on_link_hover:
            self._on_link_hover(info, event)

    def _handle_leave(self, event: tk.Event, info: LinkInfo) -> None:
        try:
            self._text.config(cursor="")
        except tk.TclError:
            pass
        if self._on_link_leave:
            self._on_link_leave(info, event)

    def _insert_image(
        self, alt: str, src: str, base_tags: tuple[str, ...]
    ) -> None:
        path: Path | None = None
        if self._base_dir is not None:
            candidate = (self._base_dir / src).resolve()
            if candidate.exists():
                path = candidate
        ext = Path(src).suffix.lower()
        # Tk PhotoImage は PNG/GIF (Python 3.12 以降) のみ確実に対応
        if path and ext in (".png", ".gif"):
            try:
                img = tk.PhotoImage(file=str(path))
                self._images.append(img)
                self._text.image_create("end", image=img)
                self._text.insert("end", "\n", base_tags)
                return
            except tk.TclError:
                pass
        self._insert_text(
            f"[image: {alt or src}]\n", base_tags + ("image_placeholder",)
        )


# ----------------------------------------------------------------
# helpers (module-level)
# ----------------------------------------------------------------


def _strip_block_id(s: str | None) -> tuple[str, str | None]:
    if s is None:
        return "", None
    m = _BLOCK_ID_TAIL_RE.search(s)
    if m:
        return s[: m.start()], m.group(1)
    return s, None


def _extract_note_id_from_url(url: str) -> str | None:
    if not url:
        return None
    base = url.split("#", 1)[0]
    m = _NOTE_ID_IN_URL_RE.search(base)
    return m.group(1) if m else None


def _extract_anchor(url: str) -> str | None:
    if not url or "#" not in url:
        return None
    return url.split("#", 1)[1] or None
