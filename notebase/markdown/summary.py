from __future__ import annotations

import re

_LIST_MARKER_RE = re.compile(r"^\s*[-*+]\s+(\[[ xX]\]\s+)?")
_ORDERED_LIST_RE = re.compile(r"^\s*\d+\.\s+")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_WIKI_ALIAS_RE = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")
_WIKI_RE = re.compile(r"\[\[([^\]]+)\]\]")
_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_RE = re.compile(r"\*([^*]+)\*")
_HR_RE = re.compile(r"^(\-{3,}|\*{3,}|_{3,})$")


def extract(body: str | None, max_chars: int) -> str:
    """Markdown 本文から要約用テキストを抽出する。

    見出し・コードフェンス内・水平線・装飾記法を取り除き、本文相当の文字列を返す。
    """
    if not body:
        return ""

    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    parts: list[str] = []
    in_fence = False

    for raw in normalized.split("\n"):
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        trimmed = raw.strip()
        if not trimmed:
            continue
        if trimmed.startswith("#"):
            continue
        if _HR_RE.match(trimmed):
            continue
        clean = _strip_markdown(trimmed)
        if not clean:
            continue
        parts.append(clean)
        if sum(len(p) + 1 for p in parts) - 1 >= max_chars:
            break

    result = " ".join(parts)
    if len(result) > max_chars:
        result = result[:max_chars] + "…"
    return result


def _strip_markdown(s: str) -> str:
    s = _LIST_MARKER_RE.sub("", s)
    s = _ORDERED_LIST_RE.sub("", s)
    s = _IMAGE_RE.sub(r"\1", s)
    s = _LINK_RE.sub(r"\1", s)
    s = _WIKI_ALIAS_RE.sub(r"\2", s)
    s = _WIKI_RE.sub(r"\1", s)
    s = _CODE_RE.sub(r"\1", s)
    s = _BOLD_RE.sub(r"\1", s)
    s = _ITALIC_RE.sub(r"\1", s)
    return s.strip()
