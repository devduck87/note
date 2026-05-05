"""Windows OLE Drag&Drop ターゲット実装。

Explorer 等から Tk ウィジェットへ画像ファイルをドロップしたいので、
標準ライブラリの ctypes だけで COM の IDropTarget を実装する。

設計:
- DropTarget は IDropTarget インスタンスを 1 つだけ作り、
  RegisterDragDrop でターゲット HWND にバインドする。
- Drop コールバックで CF_HDROP を IDataObject::GetData → DragQueryFileW で
  ファイルパス一覧を取り出し、Python 側のハンドラへ渡す。
- 失敗しても起動を阻害しない (ctypes COM は脆い領域なので例外で潰す)。

非 Windows プラットフォームでは何もしない no-op として読み込めるようにしている。
"""

from __future__ import annotations

import sys
from typing import Callable

if sys.platform != "win32":  # pragma: no cover - 非 Windows では no-op
    def initialize_ole() -> bool:
        return False

    def uninitialize_ole() -> None:
        return None

    class DropTarget:  # type: ignore[no-redef]
        def __init__(self, hwnd: int, on_files: Callable[[list[str]], None]) -> None:
            self._registered = False

        @property
        def registered(self) -> bool:
            return False

        def revoke(self) -> None:
            return None
else:
    import ctypes
    from ctypes import POINTER, Structure, Union, byref, c_void_p, wintypes

    HRESULT = ctypes.HRESULT
    DWORD = wintypes.DWORD
    ULONG = wintypes.ULONG
    LONG = wintypes.LONG
    USHORT = wintypes.USHORT
    BOOL = wintypes.BOOL
    HWND = wintypes.HWND
    LPVOID = wintypes.LPVOID

    _S_OK = 0
    _S_FALSE = 1
    _E_NOINTERFACE = 0x80004002
    _E_FAIL = 0x80004005

    _DROPEFFECT_NONE = 0
    _DROPEFFECT_COPY = 1

    _CF_HDROP = 15
    _DVASPECT_CONTENT = 1
    _TYMED_HGLOBAL = 1

    _ole32 = ctypes.windll.ole32
    _shell32 = ctypes.windll.shell32

    _ole32.OleInitialize.argtypes = [LPVOID]
    _ole32.OleInitialize.restype = HRESULT
    _ole32.OleUninitialize.argtypes = []
    _ole32.OleUninitialize.restype = None
    _ole32.RegisterDragDrop.argtypes = [HWND, c_void_p]
    _ole32.RegisterDragDrop.restype = HRESULT
    _ole32.RevokeDragDrop.argtypes = [HWND]
    _ole32.RevokeDragDrop.restype = HRESULT
    _ole32.ReleaseStgMedium.argtypes = [c_void_p]
    _ole32.ReleaseStgMedium.restype = None
    _ole32.CLSIDFromString.argtypes = [wintypes.LPCWSTR, c_void_p]
    _ole32.CLSIDFromString.restype = HRESULT

    _shell32.DragQueryFileW.argtypes = [
        c_void_p,
        ctypes.c_uint,
        ctypes.c_wchar_p,
        ctypes.c_uint,
    ]
    _shell32.DragQueryFileW.restype = ctypes.c_uint

    # ----------------------------------------------------------------
    # 構造体
    # ----------------------------------------------------------------

    class GUID(Structure):
        _fields_ = [
            ("Data1", DWORD),
            ("Data2", USHORT),
            ("Data3", USHORT),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    def _guid(s: str) -> GUID:
        g = GUID()
        hr = _ole32.CLSIDFromString(s, byref(g))
        if hr != _S_OK:
            raise OSError(f"CLSIDFromString failed for {s}: 0x{hr:08X}")
        return g

    IID_IUnknown = _guid("{00000000-0000-0000-C000-000000000046}")
    IID_IDropTarget = _guid("{00000122-0000-0000-C000-000000000046}")

    def _guid_eq(a: GUID, b: GUID) -> bool:
        return (
            a.Data1 == b.Data1
            and a.Data2 == b.Data2
            and a.Data3 == b.Data3
            and bytes(a.Data4) == bytes(b.Data4)
        )

    class POINTL(Structure):
        _fields_ = [("x", LONG), ("y", LONG)]

    class FORMATETC(Structure):
        _fields_ = [
            ("cfFormat", USHORT),
            ("ptd", c_void_p),
            ("dwAspect", DWORD),
            ("lindex", LONG),
            ("tymed", DWORD),
        ]

    class _STGMEDIUM_Union(Union):
        _fields_ = [
            ("hBitmap", c_void_p),
            ("hMetaFilePict", c_void_p),
            ("hEnhMetaFile", c_void_p),
            ("hGlobal", c_void_p),
            ("lpszFileName", wintypes.LPWSTR),
            ("pstm", c_void_p),
            ("pstg", c_void_p),
        ]

    class STGMEDIUM(Structure):
        _anonymous_ = ("u",)
        _fields_ = [
            ("tymed", DWORD),
            ("u", _STGMEDIUM_Union),
            ("pUnkForRelease", c_void_p),
        ]

    # ----------------------------------------------------------------
    # IDataObject vtable (GetData だけ使うが、レイアウトは正確に)
    # ----------------------------------------------------------------

    class IDataObjectVtbl(Structure):
        _fields_ = [
            ("QueryInterface", c_void_p),
            ("AddRef", c_void_p),
            ("Release", c_void_p),
            ("GetData", c_void_p),
            ("GetDataHere", c_void_p),
            ("QueryGetData", c_void_p),
            ("GetCanonicalFormatEtc", c_void_p),
            ("SetData", c_void_p),
            ("EnumFormatEtc", c_void_p),
            ("DAdvise", c_void_p),
            ("DUnadvise", c_void_p),
            ("EnumDAdvise", c_void_p),
        ]

    class IDataObject(Structure):
        _fields_ = [("lpVtbl", POINTER(IDataObjectVtbl))]

    _GetDataFn = ctypes.WINFUNCTYPE(
        HRESULT, c_void_p, POINTER(FORMATETC), POINTER(STGMEDIUM)
    )
    _QueryGetDataFn = ctypes.WINFUNCTYPE(HRESULT, c_void_p, POINTER(FORMATETC))

    def _has_hdrop(data_obj_ptr: int) -> bool:
        if not data_obj_ptr:
            return False
        try:
            obj = ctypes.cast(data_obj_ptr, POINTER(IDataObject))
            qfn_addr = obj.contents.lpVtbl.contents.QueryGetData
            qfn = ctypes.cast(qfn_addr, _QueryGetDataFn)
            fmt = FORMATETC(
                cfFormat=_CF_HDROP,
                ptd=None,
                dwAspect=_DVASPECT_CONTENT,
                lindex=-1,
                tymed=_TYMED_HGLOBAL,
            )
            return qfn(data_obj_ptr, byref(fmt)) == _S_OK
        except OSError:
            return False

    def _extract_files(data_obj_ptr: int) -> list[str]:
        if not data_obj_ptr:
            return []
        obj = ctypes.cast(data_obj_ptr, POINTER(IDataObject))
        try:
            get_data_addr = obj.contents.lpVtbl.contents.GetData
        except OSError:
            return []
        get_data = ctypes.cast(get_data_addr, _GetDataFn)
        fmt = FORMATETC(
            cfFormat=_CF_HDROP,
            ptd=None,
            dwAspect=_DVASPECT_CONTENT,
            lindex=-1,
            tymed=_TYMED_HGLOBAL,
        )
        med = STGMEDIUM()
        hr = get_data(data_obj_ptr, byref(fmt), byref(med))
        if hr != _S_OK:
            return []
        try:
            hdrop = med.u.hGlobal
            if not hdrop:
                return []
            count = _shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
            files: list[str] = []
            for i in range(count):
                length = _shell32.DragQueryFileW(hdrop, i, None, 0)
                if length == 0:
                    continue
                buf = ctypes.create_unicode_buffer(length + 1)
                _shell32.DragQueryFileW(hdrop, i, buf, length + 1)
                files.append(buf.value)
            return files
        finally:
            _ole32.ReleaseStgMedium(byref(med))

    # ----------------------------------------------------------------
    # IDropTarget vtable
    # ----------------------------------------------------------------

    _QueryInterfaceFn = ctypes.WINFUNCTYPE(
        HRESULT, c_void_p, POINTER(GUID), POINTER(c_void_p)
    )
    _AddRefFn = ctypes.WINFUNCTYPE(ULONG, c_void_p)
    _ReleaseFn = ctypes.WINFUNCTYPE(ULONG, c_void_p)
    _DragEnterFn = ctypes.WINFUNCTYPE(
        HRESULT, c_void_p, c_void_p, DWORD, POINTL, POINTER(DWORD)
    )
    _DragOverFn = ctypes.WINFUNCTYPE(
        HRESULT, c_void_p, DWORD, POINTL, POINTER(DWORD)
    )
    _DragLeaveFn = ctypes.WINFUNCTYPE(HRESULT, c_void_p)
    _DropFn = ctypes.WINFUNCTYPE(
        HRESULT, c_void_p, c_void_p, DWORD, POINTL, POINTER(DWORD)
    )

    class _IDropTargetVtbl(Structure):
        _fields_ = [
            ("QueryInterface", _QueryInterfaceFn),
            ("AddRef", _AddRefFn),
            ("Release", _ReleaseFn),
            ("DragEnter", _DragEnterFn),
            ("DragOver", _DragOverFn),
            ("DragLeave", _DragLeaveFn),
            ("Drop", _DropFn),
        ]

    class _IDropTargetObj(Structure):
        _fields_ = [("lpVtbl", POINTER(_IDropTargetVtbl))]

    # ----------------------------------------------------------------
    # OleInitialize
    # ----------------------------------------------------------------

    _ole_initialized = False

    def initialize_ole() -> bool:
        """OleInitialize を一度だけ呼ぶ。成功・既に初期化済みなら True。"""
        global _ole_initialized
        if _ole_initialized:
            return True
        hr = _ole32.OleInitialize(None)
        # S_OK (0), S_FALSE (1, already initialized as STA), RPC_E_CHANGED_MODE (...)
        if hr in (_S_OK, _S_FALSE):
            _ole_initialized = True
            return True
        return False

    def uninitialize_ole() -> None:
        global _ole_initialized
        if _ole_initialized:
            try:
                _ole32.OleUninitialize()
            except OSError:
                pass
            _ole_initialized = False

    # ----------------------------------------------------------------
    # DropTarget
    # ----------------------------------------------------------------

    # 生存中の DropTarget を保持する (callback の WINFUNCTYPE オブジェクトと
    # vtable struct が GC されないように)
    _LIVE: dict[int, "DropTarget"] = {}

    class DropTarget:
        """ある HWND に IDropTarget を登録するヘルパー。"""

        def __init__(
            self,
            hwnd: int,
            on_files: Callable[[list[str]], None],
        ) -> None:
            self._hwnd = hwnd
            self._on_files = on_files
            self._refs = 1
            self._registered = False

            if not initialize_ole():
                return

            # vtable 用 callable を生存させる
            self._cb_qi = _QueryInterfaceFn(self._on_qi)
            self._cb_addref = _AddRefFn(self._on_addref)
            self._cb_release = _ReleaseFn(self._on_release)
            self._cb_enter = _DragEnterFn(self._on_drag_enter)
            self._cb_over = _DragOverFn(self._on_drag_over)
            self._cb_leave = _DragLeaveFn(self._on_drag_leave)
            self._cb_drop = _DropFn(self._on_drop)

            self._vtbl = _IDropTargetVtbl(
                self._cb_qi,
                self._cb_addref,
                self._cb_release,
                self._cb_enter,
                self._cb_over,
                self._cb_leave,
                self._cb_drop,
            )
            self._obj = _IDropTargetObj()
            self._obj.lpVtbl = ctypes.pointer(self._vtbl)
            self._this = ctypes.cast(ctypes.byref(self._obj), c_void_p)

            try:
                hr = _ole32.RegisterDragDrop(hwnd, self._this)
            except OSError:
                hr = _E_FAIL
            if hr == _S_OK:
                self._registered = True
                _LIVE[hwnd] = self

        # ------------------------------------------------------------
        # public
        # ------------------------------------------------------------

        @property
        def registered(self) -> bool:
            return self._registered

        def revoke(self) -> None:
            if self._registered:
                try:
                    _ole32.RevokeDragDrop(self._hwnd)
                except OSError:
                    pass
                self._registered = False
                _LIVE.pop(self._hwnd, None)

        # ------------------------------------------------------------
        # IUnknown
        # ------------------------------------------------------------

        def _on_qi(self, this, riid_ptr, ppv_ptr) -> int:
            try:
                requested = riid_ptr.contents
                if _guid_eq(requested, IID_IUnknown) or _guid_eq(
                    requested, IID_IDropTarget
                ):
                    ppv_ptr[0] = this
                    self._refs += 1
                    return _S_OK
                ppv_ptr[0] = None
                return _E_NOINTERFACE
            except OSError:
                return _E_FAIL

        def _on_addref(self, this) -> int:
            self._refs += 1
            return self._refs

        def _on_release(self, this) -> int:
            self._refs -= 1
            return max(self._refs, 0)

        # ------------------------------------------------------------
        # IDropTarget
        # ------------------------------------------------------------

        def _on_drag_enter(self, this, data_obj, key_state, pt, pdw_effect):
            try:
                if data_obj and _has_hdrop(data_obj):
                    pdw_effect[0] = _DROPEFFECT_COPY
                else:
                    pdw_effect[0] = _DROPEFFECT_NONE
                return _S_OK
            except OSError:
                pdw_effect[0] = _DROPEFFECT_NONE
                return _E_FAIL

        def _on_drag_over(self, this, key_state, pt, pdw_effect):
            try:
                pdw_effect[0] = _DROPEFFECT_COPY
                return _S_OK
            except OSError:
                pdw_effect[0] = _DROPEFFECT_NONE
                return _E_FAIL

        def _on_drag_leave(self, this):
            return _S_OK

        def _on_drop(self, this, data_obj, key_state, pt, pdw_effect):
            try:
                files = _extract_files(data_obj) if data_obj else []
                pdw_effect[0] = _DROPEFFECT_COPY
                if files:
                    try:
                        self._on_files(files)
                    except Exception:  # noqa: BLE001
                        # 受け側のエラーは握りつぶす (OLE 側に伝搬させない)
                        pass
                return _S_OK
            except OSError:
                pdw_effect[0] = _DROPEFFECT_NONE
                return _E_FAIL
