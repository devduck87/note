from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

ALLOWED_EXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")


def is_image_file(path: str | Path) -> bool:
    if not path:
        return False
    return Path(path).suffix.lower() in ALLOWED_EXT


class ImageStore:
    """画像をノートの images/ フォルダに保存し、相対パスを返す。"""

    def save_pasted_png_bytes(self, note_dir: str | Path, png_bytes: bytes) -> str:
        """クリップボードからペーストされた PNG バイト列を保存する。

        platform.clipboard_image で DIB → PNG エンコードした結果を受け取る想定。
        戻り値は POSIX 区切り (例: "images/20260505_123456_789.png")。
        """
        if png_bytes is None:
            raise ValueError("png_bytes must not be None")
        images_dir = Path(note_dir) / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        name = self._generate_name(datetime.now(), ".png")
        dest = self._ensure_unique_name(images_dir, name)
        (images_dir / dest).write_bytes(png_bytes)
        return f"images/{dest}"

    def save_dropped_image(self, note_dir: str | Path, src_path: str | Path) -> str:
        """ファイルパスから画像をコピーする。形式判定は拡張子。"""
        src = Path(src_path)
        if not is_image_file(src):
            raise ValueError(f"Not an image file: {src}")

        images_dir = Path(note_dir) / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        ext = src.suffix.lower()
        name = self._generate_name(datetime.now(), ext)
        dest = self._ensure_unique_name(images_dir, name)
        shutil.copyfile(src, images_dir / dest)
        return f"images/{dest}"

    @staticmethod
    def _generate_name(now: datetime, ext: str) -> str:
        # yyyyMMdd_HHmmss_fff (fff = ms 3 桁)
        ms = now.microsecond // 1000
        return f"{now.strftime('%Y%m%d_%H%M%S')}_{ms:03d}{ext}"

    @staticmethod
    def _ensure_unique_name(directory: Path, name: str) -> str:
        if not (directory / name).exists():
            return name
        stem = Path(name).stem
        ext = Path(name).suffix
        for i in range(2, 1000):
            candidate = f"{stem}_{i}{ext}"
            if not (directory / candidate).exists():
                return candidate
        raise RuntimeError(f"Failed to generate unique image name: {name}")
