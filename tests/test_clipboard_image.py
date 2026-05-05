from __future__ import annotations

import struct
import unittest
import zlib

from notebase.platform.clipboard_image import dib_to_png


def _build_dib(
    width: int,
    height: int,
    bitcount: int,
    pixel_data: bytes,
    *,
    compression: int = 0,
    top_down: bool = False,
) -> bytes:
    """40-byte BITMAPINFOHEADER の DIB を組み立てる (BI_RGB 専用)。"""
    h = -height if top_down else height
    header = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        h,
        1,
        bitcount,
        compression,
        len(pixel_data),
        2835, 2835,
        0, 0,
    )
    return header + pixel_data


def _build_v5_dib(
    width: int,
    height: int,
    pixel_data: bytes,
    masks: tuple[int, int, int, int],
    *,
    top_down: bool = True,
) -> bytes:
    """BITMAPV5HEADER (124 byte) + BI_BITFIELDS 32bpp の DIB を組み立てる。"""
    header_size = 124
    h = -height if top_down else height
    header = bytearray(
        struct.pack(
            "<IiiHHIIiiII",
            header_size,
            width,
            h,
            1,
            32,
            3,           # BI_BITFIELDS
            len(pixel_data),
            2835, 2835,
            0, 0,
        )
    )
    header += struct.pack("<IIII", *masks)
    header += b"\x00" * (header_size - len(header))
    return bytes(header) + pixel_data


def _parse_png(png: bytes) -> dict:
    """PNG をデコードして {"width","height","color_type","bit_depth","raw"} を返す。"""
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = color_type = bit_depth = 0
    idat = bytearray()
    while pos < len(png):
        length = struct.unpack(">I", png[pos : pos + 4])[0]
        pos += 4
        chunk_type = png[pos : pos + 4]
        pos += 4
        data = png[pos : pos + length]
        pos += length
        crc = struct.unpack(">I", png[pos : pos + 4])[0]
        pos += 4
        assert crc == zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        if chunk_type == b"IHDR":
            (
                width,
                height,
                bit_depth,
                color_type,
                _comp,
                _filter,
                _interlace,
            ) = struct.unpack(">IIBBBBB", data)
        elif chunk_type == b"IDAT":
            idat += data
        elif chunk_type == b"IEND":
            break

    raw = zlib.decompress(bytes(idat))
    bpp = {2: 3, 6: 4}[color_type]
    stride = width * bpp + 1  # +1 for filter byte
    rows = []
    for y in range(height):
        row_start = y * stride
        assert raw[row_start] == 0  # filter type 0 (None)
        rows.append(raw[row_start + 1 : row_start + stride])
    return {
        "width": width,
        "height": height,
        "color_type": color_type,
        "bit_depth": bit_depth,
        "rows": rows,
    }


class Dib24bppTests(unittest.TestCase):
    def test_bottom_up_bgr_to_rgb(self) -> None:
        # 2x2 BGR、bottom-up。stride = ((2*24+31)//32)*4 = 8 (2-byte padding).
        # 格納された row0 が画像最下行、row1 が画像最上行となる。
        # row0 (画像下) ピクセル: (B=0x00,G=0x00,R=0xFF) (B=0x00,G=0xFF,R=0x00)
        # row1 (画像上) ピクセル: (B=0xFF,G=0x00,R=0x00) (B=0xFF,G=0xFF,R=0xFF)
        row0 = bytes.fromhex("0000FF" "00FF00") + b"\x00\x00"
        row1 = bytes.fromhex("FF0000" "FFFFFF") + b"\x00\x00"
        dib = _build_dib(2, 2, 24, row0 + row1)
        png = dib_to_png(dib)
        self.assertIsNotNone(png)
        info = _parse_png(png)
        self.assertEqual(info["width"], 2)
        self.assertEqual(info["height"], 2)
        self.assertEqual(info["color_type"], 2)
        # PNG はトップダウン: rows[0] = 画像最上行 (row1 から変換した RGB)
        self.assertEqual(info["rows"][0], bytes.fromhex("0000FF" "FFFFFF"))
        self.assertEqual(info["rows"][1], bytes.fromhex("FF0000" "00FF00"))

    def test_top_down_bgr_to_rgb(self) -> None:
        # top-down: 格納順 = 画像のトップから
        row0 = bytes.fromhex("0000FF" "00FF00") + b"\x00\x00"
        row1 = bytes.fromhex("FF0000" "FFFFFF") + b"\x00\x00"
        dib = _build_dib(2, 2, 24, row0 + row1, top_down=True)
        png = dib_to_png(dib)
        self.assertIsNotNone(png)
        info = _parse_png(png)
        # row0 (B=00,G=00,R=FF / B=00,G=FF,R=00) → RGB = "FF0000" "00FF00"
        self.assertEqual(info["rows"][0], bytes.fromhex("FF0000" "00FF00"))
        self.assertEqual(info["rows"][1], bytes.fromhex("0000FF" "FFFFFF"))


class Dib32bppRgbTests(unittest.TestCase):
    def test_bgrx_drops_alpha(self) -> None:
        # 2x1 32bpp BI_RGB (BGRX)。1 ピクセル目 (B=0x12,G=0x34,R=0x56,X=0xFF)、2 ピクセル目 (B=0xAB,G=0xCD,R=0xEF,X=0xFF)
        pixels = bytes.fromhex("12345600" "ABCDEFFF")
        dib = _build_dib(2, 1, 32, pixels, top_down=True)
        png = dib_to_png(dib)
        self.assertIsNotNone(png)
        info = _parse_png(png)
        self.assertEqual(info["color_type"], 2)  # RGB
        self.assertEqual(info["rows"][0], bytes.fromhex("563412" "EFCDAB"))


class Dib32bppBitfieldsTests(unittest.TestCase):
    def test_rgba_with_standard_masks_v5(self) -> None:
        # BITMAPV5HEADER + BI_BITFIELDS: マスクはヘッダ内 offset 40-56
        # マスク: R=0x00FF0000 G=0x0000FF00 B=0x000000FF A=0xFF000000
        # 1 ピクセル: 0x80FF8040 → A=0x80 R=0xFF G=0x80 B=0x40
        pixel = struct.pack("<I", 0x80FF8040)
        dib = _build_v5_dib(
            1,
            1,
            pixel,
            (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000),
            top_down=True,
        )
        png = dib_to_png(dib)
        self.assertIsNotNone(png)
        info = _parse_png(png)
        self.assertEqual(info["color_type"], 6)  # RGBA
        self.assertEqual(info["rows"][0], bytes.fromhex("FF804080"))

    def test_no_alpha_mask_falls_back_to_rgb(self) -> None:
        pixel = struct.pack("<I", 0x00FF8040)
        dib = _build_v5_dib(
            1,
            1,
            pixel,
            (0x00FF0000, 0x0000FF00, 0x000000FF, 0x00000000),
            top_down=True,
        )
        png = dib_to_png(dib)
        self.assertIsNotNone(png)
        info = _parse_png(png)
        self.assertEqual(info["color_type"], 2)
        self.assertEqual(info["rows"][0], bytes.fromhex("FF8040"))


class DibInvalidTests(unittest.TestCase):
    def test_too_short(self) -> None:
        self.assertIsNone(dib_to_png(b"abc"))

    def test_bad_header_size(self) -> None:
        self.assertIsNone(dib_to_png(struct.pack("<I", 1) + b"\x00" * 40))

    def test_8bpp_not_supported(self) -> None:
        dib = _build_dib(2, 2, 8, b"\x00" * 16)
        self.assertIsNone(dib_to_png(dib))


if __name__ == "__main__":
    unittest.main()
