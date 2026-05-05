# NoteBase (Python)

Markdown ノートアプリ。C# WinForms 版を Python 3.12+ / Tkinter / 標準ライブラリのみへ移植したもの。

## 起動

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
python -m notebase
```

データは既定で `<repo>/MemoRoot/` 配下に保存します。場所を変えるには:

```powershell
python -m notebase --memo-root C:\path\to\my\notes
# あるいは
$env:NOTEBASE_ROOT = "C:\path\to\my\notes"
python -m notebase
```

旧 C# 版 (`NoteBase_csharp/bin/Debug/MemoRoot/`) のデータがあれば初回起動時に自動コピーされます。

## 操作

| 操作 | キー / UI |
|---|---|
| 新規ノート | Ctrl+N または「新規」ボタン |
| 編集 | Ctrl+E または「編集」ボタン (一覧から選択中のノート) |
| 保存 | 編集ウィンドウの「保存」ボタン / Ctrl+S |
| 戻る | 「◀ 戻る」ボタン / Alt+← |
| 検索 | ツールバーの検索ボックス |
| ノートピッカー | 編集中に Ctrl+L (`[[Title#anchor]]` を挿入) |
| 画像貼付 | 編集中に Ctrl+V (クリップボードに画像があれば PNG として保存) |
| 画像 DnD | Explorer 等から画像ファイルを編集領域へドロップ |
| 画像追加 | 編集ウィンドウの「画像を追加…」ボタン (DnD のフォールバック) |
| ゴミ箱へ | ツールバーの「ゴミ箱へ」ボタン |

## テスト

```powershell
python -m unittest discover -s tests -t .
```

## 制約

- Windows 専用機能 (クリップボード画像取得、OLE DnD) は Win32 API を `ctypes` で直接叩く実装。非 Windows では DnD/画像貼付は no-op になり、その他の機能は動く。
- プレビューの画像表示は **PNG / GIF のみ**。Tk PhotoImage の制約で JPEG/BMP は `[image: <name>]` プレースホルダで代替。
- クリップボード画像は **24bpp BI_RGB / 32bpp BI_RGB / 32bpp BI_BITFIELDS (BITMAPV5HEADER)** に対応。8bpp 以下のパレット形式や RLE 圧縮は未対応。

## ライセンス / 由来

C# 版 (`NoteBase_csharp/`) は Python 版完成後に削除予定。Python 移植版は元の WinForms 実装と仕様互換 (meta.json バイト一致、フォルダ構造完全互換)。
