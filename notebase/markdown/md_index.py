from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_HR_RE = re.compile(r"^(\-{3,}|\*{3,}|_{3,})$")
_TASK_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$")
_UL_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
_OL_RE = re.compile(r"^\s*\d+\.\s+(.+)$")
_BLOCK_ID_RE = re.compile(r"\s+\^([a-zA-Z0-9-]+)\s*$")


class BlockKind(Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TASK_ITEM = "task_item"
    ORDERED_ITEM = "ordered_item"


@dataclass
class HeadingInfo:
    level: int = 0
    text: str = ""
    slug: str = ""
    line_number: int = 0  # 1-based


@dataclass
class BlockInfo:
    kind: BlockKind = BlockKind.PARAGRAPH
    level: int = 0
    text: str = ""
    existing_id: str | None = None
    heading_slug: str = ""
    line_start: int = 0
    line_end: int = 0
    context_level: int = 0


def slugify_heading(text: str | None) -> str:
    """見出しテキストから HTML id 用のスラグを生成する。

    規則:
    - 空白 → '-' (連続空白は 1 つに圧縮)
    - 先頭の空白では '-' を出さない
    - ASCII 英大文字 → 小文字
    - その他はそのまま
    - 末尾の '-' をトリム (先頭はトリムしない)
    """
    if not text:
        return ""
    out: list[str] = []
    last_dash = False
    for c in text:
        if c.isspace():
            if not last_dash and out:
                out.append("-")
                last_dash = True
        elif "A" <= c <= "Z":
            out.append(chr(ord(c) + 32))
            last_dash = False
        else:
            out.append(c)
            last_dash = False
    s = "".join(out)
    return s.rstrip("-")


def extract_headings(body: str | None) -> list[HeadingInfo]:
    """本文から見出しを抽出する。コードフェンス内は除外する。"""
    result: list[HeadingInfo] = []
    if not body:
        return result
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if m:
            text = m.group(2)
            result.append(
                HeadingInfo(
                    level=len(m.group(1)),
                    text=text,
                    slug=slugify_heading(text),
                    line_number=i + 1,
                )
            )
    return result


def extract_blocks(body: str | None) -> list[BlockInfo]:
    """本文から見出し + 段落 + リスト項目を抽出する。リンクピッカー UI 用。"""
    result: list[BlockInfo] = []
    if not body:
        return result

    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    in_fence = False
    context_level = 0

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        if _HR_RE.match(line.strip()):
            i += 1
            continue

        h = _HEADING_RE.match(line)
        if h:
            raw, bid = _strip_trailing_block_id(h.group(2))
            level = len(h.group(1))
            context_level = level
            result.append(
                BlockInfo(
                    kind=BlockKind.HEADING,
                    level=level,
                    text=raw,
                    existing_id=bid,
                    heading_slug=slugify_heading(raw),
                    line_start=i,
                    line_end=i,
                    context_level=level,
                )
            )
            i += 1
            continue

        t = _TASK_RE.match(line)
        if t:
            content, bid = _strip_trailing_block_id(t.group(2))
            result.append(
                BlockInfo(
                    kind=BlockKind.TASK_ITEM,
                    text=content,
                    existing_id=bid,
                    line_start=i,
                    line_end=i,
                    context_level=context_level,
                )
            )
            i += 1
            continue

        ul = _UL_RE.match(line)
        if ul:
            content, bid = _strip_trailing_block_id(ul.group(1))
            result.append(
                BlockInfo(
                    kind=BlockKind.LIST_ITEM,
                    text=content,
                    existing_id=bid,
                    line_start=i,
                    line_end=i,
                    context_level=context_level,
                )
            )
            i += 1
            continue

        ol = _OL_RE.match(line)
        if ol:
            content, bid = _strip_trailing_block_id(ol.group(1))
            result.append(
                BlockInfo(
                    kind=BlockKind.ORDERED_ITEM,
                    text=content,
                    existing_id=bid,
                    line_start=i,
                    line_end=i,
                    context_level=context_level,
                )
            )
            i += 1
            continue

        # 段落 (連続非空行を集める)
        para_start = i
        para_lines = [line]
        j = i + 1
        while j < n:
            lj = lines[j]
            if not lj.strip():
                break
            if lj.startswith("#") or lj.startswith("```"):
                break
            if _UL_RE.match(lj) or _OL_RE.match(lj) or _TASK_RE.match(lj):
                break
            if _HR_RE.match(lj.strip()):
                break
            para_lines.append(lj)
            j += 1
        last_idx = len(para_lines) - 1
        para_lines[last_idx], para_id = _strip_trailing_block_id(para_lines[last_idx])
        para_text = " ".join(para_lines).strip()
        result.append(
            BlockInfo(
                kind=BlockKind.PARAGRAPH,
                text=para_text,
                existing_id=para_id,
                line_start=para_start,
                line_end=j - 1,
                context_level=context_level,
            )
        )
        i = j

    return result


def extract_section(body: str | None, anchor: str | None) -> str:
    """アンカー (見出しスラグまたはブロック ID) に対応する範囲だけを切り出す。

    見出しの場合は、その見出しから次の同位以上の見出し直前までを返す。
    ブロック ID の場合は、その段落 / リスト項目だけを返す。
    一致しない場合は body をそのまま返す。
    """
    if not body or not anchor:
        return body or ""

    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    # 1) 見出しスラグでマッチ
    in_fence = False
    heading_start = -1
    heading_level = 0
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if not m:
            continue
        text, _bid = _strip_trailing_block_id(m.group(2))
        if slugify_heading(text) == anchor:
            heading_start = i
            heading_level = len(m.group(1))
            break

    if heading_start >= 0:
        end = len(lines)
        in_fence = False
        for i in range(heading_start + 1, len(lines)):
            line = lines[i]
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = _HEADING_RE.match(line)
            if m and len(m.group(1)) <= heading_level:
                end = i
                break
        while end > heading_start + 1 and not lines[end - 1].strip():
            end -= 1
        return "\n".join(lines[heading_start:end])

    # 2) ブロック ID でマッチ
    for b in extract_blocks(body):
        if b.existing_id == anchor:
            return "\n".join(lines[b.line_start : b.line_end + 1])

    return body


def _strip_trailing_block_id(s: str | None) -> tuple[str, str | None]:
    """文字列の末尾から ^id を取り除いて (本体, id) を返す。"""
    if s is None:
        return "", None
    m = _BLOCK_ID_RE.search(s)
    if m:
        return s[: m.start()], m.group(1)
    return s, None
