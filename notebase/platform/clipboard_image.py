"""Windows クリップボードから画像を取得し PNG バイト列を返すモジュール。

標準ライブラリのみで実装する制約から、Win32 API は ctypes 経由で叩き、
DIB → PNG 変換は zlib + struct で手書きする。

対応する DIB:
- 24bpp BI_RGB     (BGR ボトムアップ／トップダウン)
- 32bpp BI_RGB     (BGRX → RGB に変換、X は破棄)
- 32bpp BI_BITFIELDS (RGBA 標準マスクを想定)

それ以外 (1/4/8/16bpp や RLE 圧縮) は None を返す。
"""

from __future__ import annotations

import struct
import sys
import zlib

if sys.platform != "win32":
    # 非 Windows では何もできない
    def get_clipboard_png() -> bytes | None:  # type: ignore[no-redef]
        return None
else:
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32

    _user32.OpenClipboard.argtypes = [wintypes.HWND]
    _user32.OpenClipboard.restype = wintypes.BOOL
    _user32.CloseClipboard.argtypes = []
    _user32.CloseClipboard.restype = wintypes.BOOL
    _user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    _user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
    _user32.GetClipboardData.argtypes = [wintypes.UINT]
    _user32.GetClipboardData.restype = wintypes.HANDLE

    _kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    _kernel32.GlobalLock.restype = ctypes.c_void_p
    _kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    _kernel32.GlobalUnlock.restype = wintypes.BOOL
    _kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
    _kernel32.GlobalSize.restype = ctypes.c_size_t

    CF_DIB = 8
    CF_DIBV5 = 17

    def _get_clipboard_dib() -> bytes | None:
        if not _user32.OpenClipboard(None):
            return None
        try:
            for fmt in (CF_DIBV5, CF_DIB):
                if not _user32.IsClipboardFormatAvailable(fmt):
                    continue
                handle = _user32.GetClipboardData(fmt)
                if not handle:
                    continue
                size = _kernel32.GlobalSize(handle)
                if not size:
                    continue
                ptr = _kernel32.GlobalLock(handle)
                if not ptr:
                    continue
                try:
                    return ctypes.string_at(ptr, size)
                finally:
                    _kernel32.GlobalUnlock(handle)
            return None
        finally:
            _user32.CloseClipboard()

    def get_clipboard_png() -> bytes | None:
        """クリップボードに画像があれば PNG バイト列を返す。無ければ None。"""
        dib = _get_clipboard_dib()
        if dib is None:
            return None
        return dib_to_png(dib)


# ----------------------------------------------------------------
# pure DIB → PNG (テスト容易性のため OS 非依存)
# ----------------------------------------------------------------


_BI_RGB = 0
_BI_BITFIELDS = 3


def dib_to_png(dib: bytes) -> bytes | None:
    """DIB バイト列を PNG バイト列に変換する。失敗時は None。

    DIB の先頭は BITMAPINFOHEADER (40), BITMAPV4HEADER (108), または
    BITMAPV5HEADER (124)。biSize でヘッダ長を判定する。
    """
    if len(dib) < 40:
        return None
    bi_size = struct.unpack_from("<I", dib, 0)[0]
    if bi_size < 40 or bi_size > len(dib):
        return None

    width, height = struct.unpack_from("<ii", dib, 4)
    planes, bitcount = struct.unpack_from("<HH", dib, 12)
    compression, size_image = struct.unpack_from("<II", dib, 16)
    clr_used = struct.unpack_from("<I", dib, 32)[0]

    if width <= 0 or planes != 1:
        return None

    abs_height = abs(height)
    is_top_down = height < 0

    # ピクセルデータ開始位置を計算
    pixel_offset = bi_size

    # パレット (8bpp 以下)
    if bitcount <= 8:
        # 未対応
        return None

    # BI_BITFIELDS 用マスク (40-byte ヘッダの直後に DWORD x 3 or x 4)
    masks: tuple[int, int, int, int] | None = None
    if compression == _BI_BITFIELDS:
        if bi_size == 40:
            # ヘッダ直後の 12 byte (3 マスク)
            r_mask, g_mask, b_mask = struct.unpack_from("<III", dib, 40)
            a_mask = 0
            pixel_offset = 40 + 12
            # 4 番目のマスクが続いているかは見ない (V4/V5 の場合は header 内)
            masks = (r_mask, g_mask, b_mask, a_mask)
        else:
            # V4/V5 はヘッダ内 offset 40-, 44-, 48-, 52- にマスク
            r_mask, g_mask, b_mask, a_mask = struct.unpack_from("<IIII", dib, 40)
            masks = (r_mask, g_mask, b_mask, a_mask)
    elif compression != _BI_RGB:
        # RLE 圧縮等は未対応
        return None

    if bitcount not in (24, 32):
        return None

    # 行ストライドは 4 バイト境界に揃える
    src_row_size = ((width * bitcount + 31) // 32) * 4

    pixel_data = dib[pixel_offset:]
    if len(pixel_data) < src_row_size * abs_height:
        return None

    # トップダウンに揃えた行リスト
    rows: list[bytes] = []
    for y in range(abs_height):
        src_y = y if is_top_down else (abs_height - 1 - y)
        rows.append(pixel_data[src_y * src_row_size : src_y * src_row_size + src_row_size])

    # ピクセル変換
    if bitcount == 24:
        color_type = 2  # RGB
        bpp_out = 3
        out_stride = width * 3
        out_rows = bytearray()
        for row in rows:
            for x in range(width):
                b = row[x * 3]
                g = row[x * 3 + 1]
                r = row[x * 3 + 2]
                out_rows.append(r)
                out_rows.append(g)
                out_rows.append(b)
            # 余剰パディングは無視
        raw_pixels = bytes(out_rows)
    else:
        # 32bpp
        if masks is None:
            # BI_RGB 32bit: 通常 BGRX (X 不定) → RGB に落とす
            color_type = 2
            bpp_out = 3
            out_rows = bytearray()
            for row in rows:
                for x in range(width):
                    b = row[x * 4]
                    g = row[x * 4 + 1]
                    r = row[x * 4 + 2]
                    out_rows.append(r)
                    out_rows.append(g)
                    out_rows.append(b)
            raw_pixels = bytes(out_rows)
        else:
            r_mask, g_mask, b_mask, a_mask = masks
            r_shift = _mask_shift(r_mask)
            g_shift = _mask_shift(g_mask)
            b_shift = _mask_shift(b_mask)
            a_shift = _mask_shift(a_mask) if a_mask else None
            r_max = (r_mask >> r_shift) if r_mask else 0
            g_max = (g_mask >> g_shift) if g_mask else 0
            b_max = (b_mask >> b_shift) if b_mask else 0
            a_max = (a_mask >> a_shift) if a_shift is not None else 0

            has_alpha = bool(a_mask)
            color_type = 6 if has_alpha else 2
            bpp_out = 4 if has_alpha else 3
            out_rows = bytearray()
            for row in rows:
                for x in range(width):
                    px = struct.unpack_from("<I", row, x * 4)[0]
                    r = ((px & r_mask) >> r_shift) if r_max else 0
                    g = ((px & g_mask) >> g_shift) if g_max else 0
                    b = ((px & b_mask) >> b_shift) if b_max else 0
                    if r_max and r_max != 255:
                        r = (r * 255) // r_max
                    if g_max and g_max != 255:
                        g = (g * 255) // g_max
                    if b_max and b_max != 255:
                        b = (b * 255) // b_max
                    out_rows.append(r)
                    out_rows.append(g)
                    out_rows.append(b)
                    if has_alpha:
                        a = ((px & a_mask) >> a_shift) if a_max else 0
                        if a_max and a_max != 255:
                            a = (a * 255) // a_max
                        out_rows.append(a)
            raw_pixels = bytes(out_rows)
        out_stride = width * bpp_out

    return _make_png(width, abs_height, color_type, raw_pixels, out_stride)


def _mask_shift(mask: int) -> int:
    if not mask:
        return 0
    shift = 0
    while mask & 1 == 0:
        mask >>= 1
        shift += 1
    return shift


def _make_png(
    width: int,
    height: int,
    color_type: int,
    pixel_data: bytes,
    stride: int,
) -> bytes:
    """RAW ピクセル (top-down, no filter byte) から PNG を生成する。

    color_type: 2=RGB, 6=RGBA。bit depth は常に 8。
    """
    out = bytearray()
    out += b"\x89PNG\r\n\x1a\n"

    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,            # bit depth
        color_type,
        0,            # compression
        0,            # filter
        0,            # interlace
    )
    out += _png_chunk(b"IHDR", ihdr)

    # IDAT: 各行に filter type 0 (None) を 1 byte 前置 + zlib 圧縮
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += pixel_data[y * stride : (y + 1) * stride]
    compressed = zlib.compress(bytes(raw), 9)
    out += _png_chunk(b"IDAT", compressed)

    out += _png_chunk(b"IEND", b"")
    return bytes(out)


def _png_chunk(type_code: bytes, data: bytes) -> bytes:
    chunk_payload = type_code + data
    crc = zlib.crc32(chunk_payload) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_payload + struct.pack(">I", crc)
