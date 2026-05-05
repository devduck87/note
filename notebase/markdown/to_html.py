from __future__ import annotations

import re
from typing import Callable
from urllib.parse import quote, urljoin, urlparse

from .md_index import slugify_heading

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_HR_RE = re.compile(r"^(\-{3,}|\*{3,}|_{3,})$")
_TASK_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$")
_UL_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
_OL_RE = re.compile(r"^\s*\d+\.\s+(.+)$")
_IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)")
_LINK_RE = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)")
_NOTE_ID_IN_URL_RE = re.compile(r"(?:^|/)([^/]+)/index\.md$", re.IGNORECASE)
_BLOCK_ID_TAIL_RE = re.compile(r"\s+\^([a-zA-Z0-9-]+)\s*$")

TitleResolver = Callable[[str], str | None]
SummaryResolver = Callable[[str], str | None]


def convert(
    markdown: str | None,
    title_resolver: TitleResolver | None = None,
    base_url: str | None = None,
    note_summary_resolver: SummaryResolver | None = None,
) -> str:
    """Markdown を HTML に変換する。

    GFM サブセット + 独自 wiki link [[Title]] に対応。
    対応: 見出し / 段落 / 箇条書き / 番号付きリスト / タスクリスト /
    強調 / 斜体 / インラインコード / コードブロック (フェンス) /
    画像 / リンク / 水平線 / wiki link / ブロック ID (^id)。
    """
    if not markdown:
        return ""

    base_uri: str | None = None
    if base_url and urlparse(base_url).scheme:
        base_uri = base_url

    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    out: list[str] = []
    i = 0
    in_ul = False
    in_ol = False
    n = len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            in_ul, in_ol = _close_lists(out, in_ul, in_ol)
            i += 1
            continue

        if line.startswith("```"):
            in_ul, in_ol = _close_lists(out, in_ul, in_ol)
            lang = line[3:].strip()
            out.append("<pre><code")
            if lang:
                out.append(f' class="language-{_escape_html(lang)}"')
            out.append(">")
            i += 1
            while i < n and not lines[i].startswith("```"):
                out.append(_escape_html(lines[i]))
                out.append("\n")
                i += 1
            if i < n:
                i += 1
            out.append("</code></pre>\n")
            continue

        if _HR_RE.match(line.strip()):
            in_ul, in_ol = _close_lists(out, in_ul, in_ol)
            out.append("<hr/>\n")
            i += 1
            continue

        h = _HEADING_RE.match(line)
        if h:
            in_ul, in_ol = _close_lists(out, in_ul, in_ol)
            level = len(h.group(1))
            raw_text = h.group(2)
            slug = slugify_heading(raw_text)
            content = _process_inline(
                raw_text, title_resolver, base_uri, note_summary_resolver
            )
            out.append(f"<h{level}")
            if slug:
                out.append(f' id="{_escape_html(slug)}"')
            out.append(f">{content}</h{level}>\n")
            i += 1
            continue

        t = _TASK_RE.match(line)
        if t:
            if in_ol:
                out.append("</ol>\n")
                in_ol = False
            if not in_ul:
                out.append('<ul class="task-list">\n')
                in_ul = True
            checked_attr = " checked" if t.group(1).lower() == "x" else ""
            raw_text, block_id = _extract_trailing_block_id(t.group(2))
            content = _process_inline(
                raw_text, title_resolver, base_uri, note_summary_resolver
            )
            out.append("<li")
            if block_id:
                out.append(f' id="{_escape_html(block_id)}"')
            out.append(
                f'><input type="checkbox" disabled{checked_attr}/> {content}</li>\n'
            )
            i += 1
            continue

        ul = _UL_RE.match(line)
        if ul:
            if in_ol:
                out.append("</ol>\n")
                in_ol = False
            if not in_ul:
                out.append("<ul>\n")
                in_ul = True
            raw_text, block_id = _extract_trailing_block_id(ul.group(1))
            out.append("<li")
            if block_id:
                out.append(f' id="{_escape_html(block_id)}"')
            inner = _process_inline(
                raw_text, title_resolver, base_uri, note_summary_resolver
            )
            out.append(f">{inner}</li>\n")
            i += 1
            continue

        ol = _OL_RE.match(line)
        if ol:
            if in_ul:
                out.append("</ul>\n")
                in_ul = False
            if not in_ol:
                out.append("<ol>\n")
                in_ol = True
            raw_text, block_id = _extract_trailing_block_id(ol.group(1))
            out.append("<li")
            if block_id:
                out.append(f' id="{_escape_html(block_id)}"')
            inner = _process_inline(
                raw_text, title_resolver, base_uri, note_summary_resolver
            )
            out.append(f">{inner}</li>\n")
            i += 1
            continue

        # 段落
        in_ul, in_ol = _close_lists(out, in_ul, in_ol)
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
        para_lines[last_idx], para_block_id = _extract_trailing_block_id(
            para_lines[last_idx]
        )
        out.append("<p")
        if para_block_id:
            out.append(f' id="{_escape_html(para_block_id)}"')
        out.append(">")
        for k, pl in enumerate(para_lines):
            if k > 0:
                out.append("<br/>")
            out.append(
                _process_inline(pl, title_resolver, base_uri, note_summary_resolver)
            )
        out.append("</p>\n")

    _close_lists(out, in_ul, in_ol)
    return "".join(out)


def _close_lists(out: list[str], in_ul: bool, in_ol: bool) -> tuple[bool, bool]:
    if in_ul:
        out.append("</ul>\n")
        in_ul = False
    if in_ol:
        out.append("</ol>\n")
        in_ol = False
    return in_ul, in_ol


def _resolve_url(url: str | None, base_uri: str | None) -> str:
    if not base_uri or not url:
        return url or ""
    if urlparse(url).scheme:
        return url
    return urljoin(base_uri, url)


def _extract_trailing_block_id(line: str | None) -> tuple[str, str | None]:
    if line is None:
        return "", None
    m = _BLOCK_ID_TAIL_RE.search(line)
    if m:
        return line[: m.start()], m.group(1)
    return line, None


def _extract_note_id_from_url(url: str | None) -> str | None:
    if not url:
        return None
    m = _NOTE_ID_IN_URL_RE.search(url)
    return m.group(1) if m else None


def _build_title_attr(
    note_id: str | None, resolver: SummaryResolver | None
) -> str:
    if not note_id or resolver is None:
        return ""
    summary = resolver(note_id)
    if not summary:
        return ""
    return f' title="{_escape_html(summary)}"'


def _process_inline(
    text: str | None,
    title_resolver: TitleResolver | None,
    base_uri: str | None,
    note_summary_resolver: SummaryResolver | None,
) -> str:
    """インライン要素を処理する。

    優先順: コード → 画像 → wiki link → リンク → 強調 → 斜体 → 通常文字。
    """
    if not text:
        return ""

    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        # インラインコード `...`
        if ch == "`":
            end = text.find("`", i + 1)
            if end > i:
                code = text[i + 1 : end]
                out.append(f"<code>{_escape_html(code)}</code>")
                i = end + 1
                continue

        # 画像 ![alt](src)
        if ch == "!" and i + 1 < n and text[i + 1] == "[":
            m = _IMAGE_RE.match(text[i:])
            if m:
                alt = _escape_html(m.group(1))
                src = _escape_html(_resolve_url(m.group(2), base_uri))
                out.append(f'<img src="{src}" alt="{alt}"/>')
                i += m.end()
                continue

        # wiki link [[Title]] / [[Title#anchor]] / [[Title|alias]] / [[#anchor]]
        if ch == "[" and i + 1 < n and text[i + 1] == "[":
            end = text.find("]]", i + 2)
            if end > i + 1:
                inner = text[i + 2 : end]

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

                # [[#anchor]] / [[#^abc]] のような同一ノートアンカー
                if not title:
                    if anchor:
                        href = "#" + quote(anchor, safe="")
                        display_text = alias if alias else anchor
                        out.append(
                            f'<a href="{_escape_html(href)}">'
                            f"{_escape_html(display_text)}</a>"
                        )
                    i = end + 2
                    continue

                # 別ノートへのリンク
                resolved_id = title_resolver(title) if title_resolver else None
                if resolved_id:
                    path = "../" + resolved_id + "/index.md"
                    if anchor:
                        path += "#" + quote(anchor, safe="")
                    wiki_href = _escape_html(_resolve_url(path, base_uri))
                    title_attr = _build_title_attr(
                        resolved_id, note_summary_resolver
                    )
                    if alias:
                        display = alias
                    elif anchor:
                        display = f"{title} > {anchor}"
                    else:
                        display = title
                    out.append(
                        f'<a href="{wiki_href}"{title_attr}>'
                        f"{_escape_html(display)}</a>"
                    )
                else:
                    out.append(
                        f'<span class="unresolved-link">[[{_escape_html(inner)}]]</span>'
                    )
                i = end + 2
                continue

        # リンク [text](url)
        if ch == "[":
            m = _LINK_RE.match(text[i:])
            if m:
                label = _process_inline(
                    m.group(1), title_resolver, base_uri, note_summary_resolver
                )
                raw_url = m.group(2)
                hash_idx = raw_url.find("#")
                if hash_idx >= 0:
                    frag = raw_url[hash_idx + 1 :]
                    if frag.startswith("^"):
                        frag = frag[1:]
                    url_for_resolve = raw_url[:hash_idx] + "#" + quote(frag, safe="")
                else:
                    url_for_resolve = raw_url
                url_html = _escape_html(_resolve_url(url_for_resolve, base_uri))
                target_id = _extract_note_id_from_url(raw_url)
                title_attr = _build_title_attr(target_id, note_summary_resolver)
                out.append(f'<a href="{url_html}"{title_attr}>{label}</a>')
                i += m.end()
                continue

        # 強調 **bold**
        if i + 1 < n and ch == "*" and text[i + 1] == "*":
            end = text.find("**", i + 2)
            if end > i:
                inner = text[i + 2 : end]
                inner_html = _process_inline(
                    inner, title_resolver, base_uri, note_summary_resolver
                )
                out.append(f"<strong>{inner_html}</strong>")
                i = end + 2
                continue

        # 斜体 *italic*
        if ch == "*":
            end = text.find("*", i + 1)
            if end > i:
                inner = text[i + 1 : end]
                inner_html = _process_inline(
                    inner, title_resolver, base_uri, note_summary_resolver
                )
                out.append(f"<em>{inner_html}</em>")
                i = end + 1
                continue

        out.append(_escape_html_char(ch))
        i += 1
    return "".join(out)


def _escape_html(s: str | None) -> str:
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _escape_html_char(c: str) -> str:
    if c == "&":
        return "&amp;"
    if c == "<":
        return "&lt;"
    if c == ">":
        return "&gt;"
    if c == '"':
        return "&quot;"
    return c
