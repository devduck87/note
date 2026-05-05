from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_text_atomic(path: str | Path, content: str) -> None:
    """一時ファイル + os.replace でテキストファイルを書き込む。

    UTF-8 BOM なし。改行は変換しない (content をそのまま書き出す)。
    書き込み中の中断による破損を防ぐ。
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(
        prefix=p.name + ".",
        suffix=".tmp",
        dir=str(p.parent),
    )
    try:
        with os.fdopen(fd, "wb") as f:
            f.write((content or "").encode("utf-8"))
        os.replace(tmp, str(p))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
