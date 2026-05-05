"""file_dnd モジュールの軽量スモーク。

実際の OLE DnD はマウス操作が必要なので統合テストできない。
ここでは「import できる」「initialize_ole が True を返す」「無効 HWND で
DropTarget を作っても例外で死なない」を確認する。
"""

from __future__ import annotations

import sys
import unittest


@unittest.skipUnless(sys.platform == "win32", "Windows 専用")
class FileDndSmokeTests(unittest.TestCase):
    def test_imports(self) -> None:
        from notebase.platform import file_dnd

        self.assertTrue(hasattr(file_dnd, "DropTarget"))
        self.assertTrue(hasattr(file_dnd, "initialize_ole"))
        self.assertTrue(hasattr(file_dnd, "uninitialize_ole"))

    def test_initialize_idempotent(self) -> None:
        from notebase.platform.file_dnd import initialize_ole

        # 二度目以降も True を返す (キャッシュ)
        self.assertTrue(initialize_ole())
        self.assertTrue(initialize_ole())

    def test_drop_target_invalid_hwnd_does_not_crash(self) -> None:
        from notebase.platform.file_dnd import DropTarget

        target = DropTarget(0, lambda files: None)  # 0 = 無効な HWND
        # 登録は失敗するはずだが、例外で死なない
        self.assertFalse(target.registered)
        target.revoke()  # no-op


@unittest.skipIf(sys.platform == "win32", "非 Windows のフォールバック")
class FileDndNoOpTests(unittest.TestCase):
    def test_noop_module_loads(self) -> None:
        from notebase.platform import file_dnd

        self.assertFalse(file_dnd.initialize_ole())
        target = file_dnd.DropTarget(0, lambda files: None)
        self.assertFalse(target.registered)
        target.revoke()


if __name__ == "__main__":
    unittest.main()
