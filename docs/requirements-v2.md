# 情報整理ツール 要件定義書 v2

## 1. 概要

### 1.1 目的

本システムは、手順書、備忘録、Todoリスト、ルーティーンチェックリスト、日次メモなどを、テキストと画像を組み合わせて簡単に作成・蓄積・検索・編集・出力できるローカル情報整理ツールである。

Markdownファイルと画像ファイルを本文の正本データとして保持し、管理用メタデータは別ファイル `meta.json` で一元管理する。ユーザーがアプリケーション外からでも本文・画像を確認できることを重視する。検索・一覧表示・Todo抽出・関連管理用には、JSONまたはSQLiteのインデックスを段階的に整備する。

### 1.2 背景

Markdown単体で情報を管理する場合、以下の課題がある。

* 情報の分類先に迷いやすい
* 画像の挿入や管理が面倒
* ファイル数が増えると目的の情報にアクセスしづらい
* Todo、手順書、備忘録、作業ログなどが混在しやすい
* 必要な情報だけを抽出してまとめる作業が手間
* 一度作成した情報を後から修正・再利用しづらい

本システムでは、入力専用のシンプルなUIと、蓄積した情報を検索・表示・編集するリッチなビューワー兼エディタを分けることで、情報の入力しやすさと整理しやすさを両立する。

### 1.3 v1 からの主な設計変更

| 項目 | v1 | v2 |
| --- | --- | --- |
| メタデータ保存形式 | Markdown Frontmatter | `meta.json`（独立ファイル） |
| `notes/` フォルダ階層 | type 別サブフォルダ | フラット |
| ノート保存形式 | フォルダ方式 + 単体 .md 併用 | フォルダ方式に統一 |
| Todo 種別 | `todo` 一種 | `todo` / `routine` / `checklist` / `log` に分割 |
| キャンバス保存先 | `outputs/canvas/` | `canvases/`（正本扱い） |
| Obsidian 互換出力 | 未定義 | `outputs/exports/obsidian/` に新規追加 |
| GUI 技術 | 未決 | .NET Framework 4.6.1 / C# / WinForms に確定 |
| 依存方針 | 未決 | **標準ライブラリのみ使用**（NuGet 不使用） |

---

## 2. 基本方針

### 2.1 基本コンセプト

ノートはフォルダ単位で扱う。

```text
1ノートフォルダ = 1レコード
├─ index.md      … 本文（純粋な Markdown）
├─ meta.json     … 管理データの正本
└─ images/       … 添付画像
```

正本と生成物を明確に分離する。

```text
正本データ:
  notes/<ID>/index.md       Markdown 本文
  notes/<ID>/meta.json      JSON メタデータ
  notes/<ID>/images/        添付画像
  canvases/<name>.json      キャンバス配置

生成物・インデックス（再生成可）:
  indexes/                  検索高速化用 JSON / SQLite
  outputs/                  日次 Todo / レポート / Obsidian エクスポート
```

### 2.2 設計原則

* 本文は純粋な Markdown として保存する（Frontmatter を持たない）
* 管理データは `meta.json` で一元管理する
* フォルダ階層に分類情報（type / project / status）を持たせない
* インデックスは破損しても正本から再生成できる
* メタデータの直接編集経路は GUI のみ（壊れにくくする）
* 入力 UI と検索・編集 UI は分離する
* 出力ファイルは正本と分けて管理する
* 生成物は元データと混在させない
* **外部 NuGet パッケージに依存せず、.NET Framework 標準ライブラリのみで実装する**

---

## 3. 想定ユーザー

### 3.1 主な利用者

* 個人で作業メモ、手順書、Todo、備忘録を管理したいユーザー
* 画像付きの作業手順を簡単に記録したいユーザー
* 後から情報を検索・抽出・再整理したいユーザー
* ローカルファイルベースで情報を長期保存したいユーザー

### 3.2 利用シーン

* 作業中に気づいたことをすばやくメモする
* スクリーンショットを貼り付けながら手順書を作る
* 毎日の Todo リストを生成する
* ルーティーンチェックリストを日次 Todo に反映する
* 特定タグ・プロジェクトに関するメモを抽出する
* 複数のノートをキャンバス上に自由配置して整理する
* 既存のノート群を Obsidian 用にエクスポートする

---

## 4. スコープ

### 4.1 対象範囲

手順書 / 備忘録 / Todo リスト / ルーティーンチェックリスト / 日次メモ / 作業ログ / 学習メモ / プロジェクトメモ / 画像付きノート

### 4.2 初期開発範囲（Phase 1 / MVP）

* ノート作成
* ノートフォルダ自動生成
* `index.md` + `meta.json` のアトミック保存
* Ctrl + V による画像貼り付け
* ドラッグ＆ドロップによる画像追加
* ノート一覧表示
* タイトル部分一致検索
* Markdown プレビュー

### 4.3 将来拡張範囲

* SQLite インデックス
* タスク抽出（行内メタ記法解析）
* ルーティーンから日次 Todo 生成
* チェックリストインスタンス化
* 条件抽出 Markdown 出力
* Obsidian 互換エクスポート
* キャンバス表示
* ノート間リンク
* 全文検索

---

## 5. フォルダ構成要件

### 5.1 ルート構成

```text
MemoRoot/
├─ notes/                                ノート群（フラット）
│  └─ <ID>/
│     ├─ index.md
│     ├─ meta.json
│     └─ images/
│
├─ canvases/                             キャンバス配置の正本
│  └─ <canvas-name>.json
│
├─ outputs/
│  ├─ daily_todo/
│  ├─ reports/
│  └─ exports/
│     └─ obsidian/                       Frontmatter 付き .md を出力
│
├─ templates/                            テンプレート（meta.json + index.md）
│
├─ indexes/
│  ├─ note_index.json                    Phase 2
│  ├─ tag_index.json                     Phase 2
│  ├─ task_index.json                    Phase 3
│  └─ index.db                           Phase 4
│
├─ config/
│  ├─ settings.json
│  ├─ categories.json
│  ├─ tags.json
│  ├─ views.json
│  └─ export_rules.json
│
└─ trash/                                削除ノートの一時保管
```

### 5.2 ノートフォルダ構成

すべてのノートは同一構造を持つ。

```text
notes/20260428-090000-excel-tool-usage/
├─ index.md
├─ meta.json
└─ images/
   ├─ 01_file_select.png
   └─ 02_result.png
```

* `images/` は画像が無い場合でも空フォルダとして作成しておく
* `meta.json` の存在をもってノートと判定する

### 5.3 ID とフォルダ名

* フォルダ名 = ノート ID = `YYYYMMDD-HHMMSS-<slug>`
* slug: タイトルから ASCII 英数字とハイフンのみ抽出（小文字化）
* slug が空になる場合は `untitled`
* 同秒衝突時は末尾にミリ秒 3 桁を付与

例:

| タイトル | フォルダ名 |
| --- | --- |
| Excel検索ツールの使い方 | `20260428-090000-untitled` |
| LVGL Buffer Setup | `20260428-090000-lvgl-buffer-setup` |
| Excel検索ツール v2 release | `20260428-090000-excel-v2-release` |

---

## 6. データ形式要件

### 6.1 index.md

純粋な Markdown のみ。Frontmatter を持たない。

```markdown
# Excel検索ツールの使い方

## 手順

1. ファイルを選択する
2. 検索条件を指定する

![結果画面](images/02_result.png)
```

* 先頭は H1（`# タイトル`）とし、`meta.json` の `title` と同期する
* タスクリストは `- [ ]` / `- [x]`
* 行内メタ記法（§6.6）を使用可能
* 画像参照は相対パス（`images/...`）
* Markdown 仕様は GFM 互換（タスクリスト拡張を含む）

### 6.2 meta.json 構造

```json
{
  "meta_version": 1,
  "id": "20260428-090000-excel-tool-usage",
  "title": "Excel検索ツールの使い方",
  "type": "procedure",
  "status": "active",
  "tags": ["excel", "search", "tool"],
  "project": "excel-search-tool",
  "due": null,
  "schedule": null,
  "instance_of": null,
  "created": "2026-04-28T09:00:00",
  "updated": "2026-04-28T09:30:00"
}
```

### 6.3 メタデータ項目

| 項目 | 内容 | 必須 | 備考 |
| --- | --- | --- | --- |
| meta_version | スキーマバージョン | 必須 | 初期値 1 |
| id | ノート ID | 必須 | フォルダ名と一致 |
| title | タイトル | 必須 | 本文先頭 H1 と同期 |
| type | ノート種別 | 必須 | §6.4 |
| status | 状態 | 任意 | active / done / pending / archived |
| tags | タグ一覧 | 任意 | 文字列配列 |
| project | プロジェクト識別子 | 任意 | type=todo の既定値は `inbox` |
| due | ノート単位の期限 | 任意 | type=todo 以外で使用 |
| schedule | ルーティーンスケジュール | 任意 | type=routine 専用 |
| instance_of | 元 checklist の ID | 任意 | type=log で checklist インスタンス時 |
| created | 作成日時 | 必須 | ISO8601 |
| updated | 更新日時 | 必須 | ISO8601 |

### 6.4 ノート種別 (type)

| type | 意味 | 主な特徴 |
| --- | --- | --- |
| procedure | 手順書 | 静的内容 |
| memo | 備忘録 | 静的内容 |
| todo | one-time タスクリスト | 本文の `- [ ]` を tasks として抽出 |
| routine | 定期ルーティーンテンプレート | schedule を持つ。本文はテンプレ |
| checklist | 作業時チェックリストテンプレート | インスタンス化される |
| log | 作業記録 / checklist インスタンス | instance_of を持ちうる |
| daily | 日次メモ | |
| project | プロジェクトメモ | |

### 6.5 schedule オブジェクト (type=routine)

```json
{
  "frequency": "daily",
  "days": ["mon", "tue", "wed", "thu", "fri"],
  "day_of_month": null,
  "enabled": true
}
```

* `frequency`: `daily` / `weekly` / `monthly`
* `days`: weekly の対象曜日（mon〜sun）
* `day_of_month`: monthly の対象日（1〜31）
* `enabled`: false で日次 Todo 生成対象から除外

### 6.6 行内メタ記法

タスク行に期限・タグを埋め込む記法。

```markdown
- [ ] 仕様書をレビューする @2026-05-10 #high
- [x] サンプルデータ準備 @2026-04-25
- [ ] テスト項目作成 @2026-05-15 #excel
```

抽出ルール:

* `@YYYY-MM-DD` → タスクの `due_date`
* `#word` → タスクのタグ（複数可、重複は無視）
* 出現順序は不問
* タスク本文は記法を除いた残り文字列

---

## 7. 機能要件

### 7.1 ノート作成機能

#### 7.1.1 概要

入力専用 UI から、種類・タイトル・タグ・本文を入力してノートを作成する。

#### 7.1.2 要件

* ノート種別を選択できること
* タイトルを入力できること
* タグを入力できること
* Markdown 本文を入力できること
* type 選択時にノートフォルダを正規パスに即作成すること
* 保存時に `index.md` と `meta.json` をアトミックに書き出すこと
* 保存時に title を `index.md` 先頭 H1 へ同期すること
* 作成日時・更新日時を自動設定すること
* 入力をキャンセルした場合、ノートフォルダを `trash/` へ移動すること

### 7.2 画像貼り付け機能

#### 7.2.1 対応操作

* Ctrl + V によるクリップボード画像貼り付け
* 画像ファイルのドラッグ＆ドロップ
* 画像選択ボタンによる追加

#### 7.2.2 要件

* 画像は当該ノートの `images/` へ保存すること
* `images/` が存在しない場合は自動作成
* Markdown 本文のカーソル位置に相対パスで画像リンクを挿入
* ファイル名はミリ秒精度で自動生成（例: `20260428_091500_123.png`）
* 同名衝突時は連番付与
* 画像以外のファイルは無視または警告

#### 7.2.3 Markdown 挿入例

```markdown
![画像](images/20260428_091500_123.png)
```

#### 7.2.4 対応形式

PNG / JPEG / JPG / GIF / BMP / WebP

### 7.3 ノート一覧表示機能

#### 7.3.1 要件

* ノートタイトル / 種別 / タグ / 作成日時 / 更新日時を表示
* ノート選択で本文表示
* 既定: 更新日時降順
* Phase 2 以降でソートを切替可能（タイトル / 種別 / 作成日 / 期限）

### 7.4 検索機能

#### 7.4.1 検索条件

キーワード / タイトル / 本文 / タグ / 種別 / ステータス / プロジェクト / 作成日 / 更新日 / 画像有無 / 未完了 Todo

#### 7.4.2 Phase 1 / MVP

タイトル部分一致検索（`meta.json` 群を逐次走査）

#### 7.4.3 Phase 2

タグ検索 / 種別フィルタ / 本文検索（JSON インデックス利用）

#### 7.4.4 Phase 5

SQLite + 全文検索（FTS5）

### 7.5 Markdown 表示機能

#### 7.5.1 要件

* Markdig で HTML 化し WebView2 で表示
* 相対パス画像を解決
* 編集モードと切替可能
* GFM タスクリストのチェックボックスを表示

### 7.6 Markdown 編集機能

#### 7.6.1 要件

* 本文を編集できること
* 保存時に `meta.json` の `updated` を更新
* 画像リンクを保持
* `meta.json` 直接編集の経路は提供しない（GUI のみ）
* 外部エディタによる `index.md` 編集は許容（OS mtime で検知）

### 7.7 メタデータ編集機能（プロパティパネル）

#### 7.7.1 概要

ビューワー画面の右サイドバーで `meta.json` のフィールドを GUI 編集する。

#### 7.7.2 要件

* title / type / status / tags / project / due / schedule を GUI フォームで編集
* JSON 直接編集の UI は提供しない
* 編集時に `meta.json` をアトミック更新
* title 変更時は `index.md` 先頭 H1 を同期
* type 変更時は schedule / instance_of の有効性を検証

### 7.8 Todo 管理機能 (type=todo)

#### 7.8.1 概要

`type=todo` ノートに複数タスクを行単位でまとめる。

#### 7.8.2 要件

* 1 ノート = 複数タスク（行ごとに `- [ ]`）
* プロジェクト別に複数の todo ノート作成可（既定 `project=inbox`）
* 行内メタ記法で期限・タグを記述
* 完了状態は本文の `[x]` を正本とする
* 未完了タスク・期限切れタスクの抽出が可能

#### 7.8.3 タスク行ステータス

| 表記 | 意味 |
| --- | --- |
| `- [ ]` | 未完了 |
| `- [x]` | 完了 |

#### 7.8.4 ノート単位ステータス

| status | 意味 |
| --- | --- |
| active | 有効 |
| done | 全タスク完了 |
| pending | 保留 |
| archived | アーカイブ |

### 7.9 ルーティーン管理機能 (type=routine)

#### 7.9.1 概要

日次・週次・月次の繰り返しチェックリストを定義する。

#### 7.9.2 要件

* `meta.json` の `schedule` で頻度を定義
* `enabled` で有効・無効を切替
* 本文のチェック項目はテンプレ（チェック状態を変更しない）
* 日次 Todo 生成時に該当 routine の本文を取り込む

### 7.10 チェックリスト管理機能 (type=checklist)

#### 7.10.1 概要

作業時に使う再利用可能なチェックリストテンプレート。

#### 7.10.2 要件

* テンプレートは `type=checklist` ノートとして保存
* 「使う」操作でインスタンス（`type=log`、`instance_of=元 ID`）を新規生成
* インスタンスは `notes/<新 ID>/` 配下に作成
* 元テンプレートはチェックを変更しない
* 過去の実施記録は log として残る

### 7.11 日次 Todo 生成機能

#### 7.11.1 概要

指定日のタスクとルーティーンをまとめた Markdown を生成する。

#### 7.11.2 要件

* 指定日を入力できる
* `due_date` が指定日以前の `type=todo` の未完了タスク行を抽出
* `enabled=true` かつ指定日に該当する `type=routine` の本文を取り込む
* `type=checklist` / `type=log` は対象外
* `outputs/daily_todo/YYYY-MM-DD.md` として出力
* 本ファイルが routine の事実上の完了履歴となる

#### 7.11.3 出力例

```markdown
# 2026-04-28 Todo

## 期限のタスク

- [ ] 仕様書をレビューする @2026-05-10 #high
- [ ] テスト項目作成 @2026-05-15 #excel

## 本日のルーティーン

### 朝の作業開始ルーティーン

- [ ] メールチェック
- [ ] 本日の Todo 確認
- [ ] 作業ログを開く
```

### 7.12 条件抽出 Markdown 出力機能

#### 7.12.1 要件

* タグ / プロジェクト / 種別 / ステータスで抽出
* 抽出結果を Markdown ファイルとして出力
* 出力先 `outputs/reports/`

### 7.13 Obsidian 互換エクスポート機能

#### 7.13.1 概要

`meta.json` から Frontmatter を組み立て、Frontmatter 付き Markdown を生成する。

#### 7.13.2 要件

* 単一ノートまたは全ノートを一括エクスポート可能
* 出力先 `outputs/exports/obsidian/<ID>.md`
* Frontmatter には `id` / `title` / `type` / `status` / `tags` / `project` / `created` / `updated` / `due` / `schedule` を含む
* `images/` をコピーする（相対パス維持）
* 一方向のみ。逆方向（Obsidian → 本ツール）は提供しない

#### 7.13.3 出力例

```markdown
---
id: 20260428-090000-excel-tool-usage
title: Excel検索ツールの使い方
type: procedure
tags: [excel, search, tool]
project: excel-search-tool
created: 2026-04-28 09:00
updated: 2026-04-28 09:30
---

# Excel検索ツールの使い方

(以下、本文)
```

### 7.14 キャンバス表示機能

#### 7.14.1 初期要件

* ノートをカードとして配置
* カード移動・位置保存
* カードクリックでノート展開

#### 7.14.2 将来要件

* ノート間関連線・ラベル
* 複数キャンバス対応
* `canvases/<canvas-name>.json` に正本保存

---

## 8. インデックス要件

### 8.1 基本方針

* インデックスは正本ではない（破損しても再生成可）
* 走査入力: `notes/*/meta.json` + `index.md`（必要時）
* `meta.json` の存在をもってノート判定
* `index.md` の OS mtime > `meta.json.updated` なら本文を再パース

### 8.2 初期インデックス（JSON）

```text
indexes/note_index.json
indexes/tag_index.json
indexes/task_index.json
```

### 8.3 将来インデックス（SQLite）

```text
indexes/index.db
```

格納対象: ノート基本情報 / タグ / 添付 / Todo / ルーティーン / キャンバス配置 / 全文検索データ

### 8.4 SQLite は正本にしない

* 本文・画像本体は SQLite に保存しない
* SQLite はインデックスのみ
* 破損時は `notes/` から再構築

---

## 9. SQLite テーブル（参考）

> **注:** 本システムは標準ライブラリのみで実装する制約のため、Phase 1〜3 では SQLite を導入しない。本章のテーブル定義は「将来 SQLite を導入可能にした場合の参考スキーマ」として保持する。Phase 4 までは JSON インデックス（§8.2）で代替する。

### 9.1 notes

```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT,
    project TEXT,
    path TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT,
    file_modified_at TEXT,
    summary TEXT
);
```

* `file_modified_at` は `index.md` の OS mtime。外部編集検知に使用

### 9.2 tags

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
```

### 9.3 note_tags

```sql
CREATE TABLE note_tags (
    note_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (note_id, tag_id),
    FOREIGN KEY (note_id) REFERENCES notes(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
```

### 9.4 attachments

```sql
CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id TEXT NOT NULL,
    type TEXT NOT NULL,
    path TEXT NOT NULL,
    original_name TEXT,
    created_at TEXT,
    FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

### 9.5 tasks

`type=todo` ノート本文の `- [ ]` 行を抽出する。

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    note_id TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    due_date TEXT,
    priority TEXT,
    FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

* `id`: `<note_id>:<line_number>` などの合成キー
* `status`: `open` / `done`（本文の `[ ]` / `[x]` から導出）
* `due_date`: 行内 `@YYYY-MM-DD` から抽出
* `priority`: 行内 `#high` / `#low` などの特別タグから抽出

### 9.6 routines

`type=routine` ノートの `schedule` から抽出する。

```sql
CREATE TABLE routines (
    note_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    frequency TEXT NOT NULL,
    days TEXT,
    day_of_month INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

* `days`: weekly のとき JSON 配列文字列（例: `["mon","wed"]`）

### 9.7 canvas_nodes

```sql
CREATE TABLE canvas_nodes (
    canvas_id TEXT NOT NULL,
    note_id TEXT NOT NULL,
    x REAL NOT NULL,
    y REAL NOT NULL,
    width REAL NOT NULL,
    height REAL NOT NULL,
    PRIMARY KEY (canvas_id, note_id),
    FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

### 9.8 canvas_edges

```sql
CREATE TABLE canvas_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canvas_id TEXT NOT NULL,
    from_note_id TEXT NOT NULL,
    to_note_id TEXT NOT NULL,
    label TEXT,
    FOREIGN KEY (from_note_id) REFERENCES notes(id),
    FOREIGN KEY (to_note_id) REFERENCES notes(id)
);
```

---

## 10. 非機能要件

### 10.1 保存性

* データはローカルフォルダに保存
* `index.md` / 画像 / `canvases/` は外部ツールで参照可能
* `meta.json` は人間可読 JSON
* アプリが無くても本文・画像は読める

### 10.2 拡張性

* `meta.json` に `meta_version` を持ち、スキーマ進化に対応
* ノート種別の追加が可能
* インデックス方式 JSON → SQLite への移行余地を残す（標準ライブラリ縛り解除時）
* 将来的にキャンバス・Todo 生成・全文検索を追加可能
* 依存ライブラリ追加の判断は明示的な制約緩和とセットで行う

### 10.3 保守性

* 保存処理 / 画像処理 / 検索処理 / インデックス処理を分離
* フォルダ構成は設定で変更可能な余地を残す
* インデックスは再生成可能

### 10.4 性能

* 数百件のノートを快適に扱える
* 将来数千件対応
* 一覧表示はインデックス利用で高速化
* 本文全文検索は段階的に強化

### 10.5 可搬性

* `MemoRoot` フォルダのコピーで別環境へ移行可能
* 画像・キャンバス参照は相対パス

### 10.6 安全性

* 削除は `trash/` へ移動
* 保存は一時ファイル + アトミック rename
* 画像ファイル名重複を回避（ミリ秒精度 + 連番）
* インデックス再構築機能を提供
* `meta.json` は GUI 経由でのみ編集（破損リスクを排除）

### 10.7 整合性

* `index.md` と `meta.json` は常に同時更新（一時ファイル + rename）
* `title` は `meta.json` を正、`index.md` 先頭 H1 へ同期
* 外部エディタによる `index.md` 変更は OS mtime で検知し再パース

---

## 11. UI 要件

### 11.1 入力専用 UI

#### 11.1.1 目的

作業中に迷わず素早く情報を入力するための画面。

#### 11.1.2 要件

* ノート種別を選択できること
* タイトルを入力できること
* タグを入力できること
* 本文を入力できること
* Ctrl + V で画像貼り付けできること
* ドラッグ＆ドロップで画像追加できること
* 保存ボタンでノートを作成できること
* キャンセルでフォルダごと `trash/` へ移動

#### 11.1.3 画面イメージ

```text
┌──────────────────────────┐
│ 種類: [備忘録 ▼]          │
│ タイトル: [              ] │
│ タグ: [                  ] │
│                          │
│ 本文:                    │
│ ┌──────────────────────┐ │
│ │                      │ │
│ │                      │ │
│ └──────────────────────┘ │
│                          │
│ [画像追加] [保存] [取消]   │
└──────────────────────────┘
```

### 11.2 ビューワー兼エディタ UI

#### 11.2.1 目的

蓄積されたノートを検索・表示・編集・整理するための画面。

#### 11.2.2 要件

* 検索欄
* ノート一覧
* 選択ノートのプレビュー / 編集ペイン
* 右サイドバー: プロパティパネル（meta.json 編集）
* タグ・種別フィルタ（Phase 2 以降）
* 編集モードへの切替

#### 11.2.3 画面イメージ

```text
┌────────────────────────────────────────────────┐
│ 検索: [ LVGL              ] [検索]              │
├───────────────┬──────────────────┬─────────────┤
│ 検索結果一覧    │ プレビュー / 編集   │ プロパティ   │
│               │                  │             │
│ □ LVGLメモ     │ # LVGL バッファ... │ type: memo  │
│ □ GUI手順書    │ ![](images/...)   │ tags: [..]  │
│ □ Todo        │                   │ status: ... │
└───────────────┴──────────────────┴─────────────┘
```

---

## 12. 処理フロー

### 12.1 ノート作成フロー

```text
入力 UI 起動
↓
type 選択
↓
ID 生成・正規パスにフォルダ作成（slug は暫定値）
↓
images/ 作成
↓
編集（画像貼り付け含む）
↓
保存ボタン
  ├─ title から slug を確定 → フォルダ rename（必要時）
  ├─ meta.json.tmp を書き込み
  ├─ index.md.tmp を書き込み（先頭 H1 同期）
  ├─ アトミック rename
  └─ インデックス更新
↓
キャンセル時
  └─ ノートフォルダを trash/ へ移動
```

### 12.2 画像貼り付けフロー

```text
Ctrl + V またはドラッグ＆ドロップ
↓
画像データ判定（ヘッダで形式識別）
↓
ファイル名生成（ミリ秒精度）
↓
images/ へ保存（重複は連番付与）
↓
本文カーソル位置に相対パス画像リンク挿入
```

### 12.3 インデックス再構築フロー

```text
notes/*/meta.json を走査
↓
JSON パースで NoteMeta を取得
↓
index.md の OS mtime をチェック
↓
mtime > updated の場合は本文を再パース
  ├─ タスク行抽出（type=todo）
  └─ meta.json.updated を更新
↓
JSON / SQLite を再生成
```

### 12.4 日次 Todo 生成フロー

```text
指定日を取得
↓
インデックスから期限が指定日以前の未完了タスクを抽出
↓
インデックスから該当日に有効な routine を抽出
↓
本文を取り込みテンプレートに反映
↓
outputs/daily_todo/YYYY-MM-DD.md として出力
```

### 12.5 Obsidian エクスポートフロー

```text
対象ノートを選択
↓
meta.json から Frontmatter を組み立て
↓
index.md 本文と結合
↓
outputs/exports/obsidian/<ID>.md として出力
↓
images/ をコピー
```

---

## 13. 優先度

### 13.1 Phase 1: 最小実用版（MVP）

* ノート作成
* type 選択
* ノートフォルダ作成
* `meta.json` + `index.md` のアトミック保存
* Ctrl + V 画像貼り付け
* ドラッグ＆ドロップ画像貼り付け
* ノート一覧表示
* タイトル部分一致検索
* Markdown プレビュー（Markdig + WebView2）

### 13.2 Phase 2: 検索・編集強化版

* タグ検索 / 種別フィルタ
* 本文検索
* Markdown 編集モード
* プロパティパネル（meta.json 編集）
* 一覧ソート切替
* JSON インデックス
* 外部編集検知

### 13.3 Phase 3: Todo・Routine 版

* 行内メタ記法解析
* タスク抽出
* routine 管理（schedule 編集）
* checklist インスタンス生成
* 日次 Todo 生成

### 13.4 Phase 4: エクスポート・抽出版

* JSON インデックス完成版（タグ・タスク・添付）
* インデックス再構築機能
* Obsidian 互換エクスポート
* 条件抽出 Markdown 出力
* SQLite 導入は標準ライブラリ縛り解除を判断した時点で別フェーズとして検討

### 13.5 Phase 5: 高度整理版

* キャンバス表示
* ノート間関連線
* 全文検索（標準実装。FTS5 は SQLite 導入時に再検討）
* テンプレート編集機能
* ノート間 wiki link

---

## 14. MVP 要件

### 14.1 MVP 機能

* ノート作成画面（type 選択 / タイトル入力 / 本文入力）
* Ctrl + V 画像貼り付け
* ドラッグ＆ドロップ画像貼り付け
* ノートフォルダ作成（`meta.json` + `index.md` + `images/`）
* アトミック保存
* ノート一覧表示
* タイトル部分一致検索
* Markdown プレビュー

### 14.2 MVP 対象外

* 高度な全文検索
* SQLite インデックス
* キャンバス表示
* Todo 自動生成
* ルーティーン管理
* チェックリストインスタンス化
* Obsidian エクスポート
* WYSIWYG 編集
* クラウド同期

---

## 15. 技術スタック

### 15.1 依存方針

**標準ライブラリのみを使用する。** NuGet パッケージ・外部 DLL に依存しない。

理由:

* 配布が単純（exe 1 つ + 設定ファイル）
* 長期保守でのライブラリ陳腐化リスクを排除
* 本システムの規模では標準ライブラリで十分実装可能と判断

### 15.2 採用技術

| 用途 | 採用 |
| --- | --- |
| ターゲットフレームワーク | .NET Framework 4.6.1 |
| GUI 基盤 | WinForms |
| Markdown パース・HTML 変換 | **自前実装**（最低限の GFM サブセット） |
| プレビュー描画 | **WebBrowser コントロール**（WinForms 標準、IE エンジン） |
| JSON シリアライズ | **自前実装**（meta.json 用、人間可読インデント付き） |
| エディタ（Phase 1） | TextBox（multiline） |
| エディタ（Phase 2 以降） | RichTextBox 拡張または自前 |
| SQLite | 採用しない。標準制約緩和時のみ再検討 |

### 15.3 自前 Markdown パーサーの対応範囲（Phase 1）

* 見出し（`#` 〜 `######`）
* 段落
* 箇条書き（`-` `*` `+`、ネスト）
* 番号付きリスト（`1.`）
* タスクリスト（`- [ ]` `- [x]`）
* 強調（`**bold**` `*italic*`）
* インラインコード（`` `code` ``）
* コードブロック（フェンス `` ``` `` のみ）
* 画像（`![alt](path)`）
* リンク（`[text](url)`）
* 水平線（`---`）

対象外（必要時に拡張）:

* テーブル
* 引用ブロック
* HTML 直書き
* 脚注
* 取り消し線

### 15.4 自前 JSON シリアライザの対応範囲

`meta.json` のスキーマに特化:

* プリミティブ: 文字列 / 数値 / bool / null
* 配列: 文字列配列（`tags`、`days`）
* オブジェクト: 1 段ネスト（`schedule`）
* 日時: ISO8601 文字列で扱う
* 出力: 2 スペースインデント、フィールド順固定、null フィールドは省略
* 入力: トークナイザ + パーサーで `Dictionary<string, object>` を生成し POCO へマッピング

---

## 16. 残未決事項（フェーズ着手前に決める）

| 項目 | 必要フェーズ |
| --- | --- |
| `outputs/reports/` と `outputs/exports/` の使い分け基準 | Phase 4 |
| `trash/` の保持期間・自動削除ポリシー | Phase 1〜2 |
| 外部編集競合時のユーザー通知方式 | Phase 2 |
| 一覧ソートの種類（タイトル / 種別 / 期限...） | Phase 2 |
| ノート間相互リンク方式（`[[wiki link]]` 採用？） | Phase 5 |
| 日本語全文検索の tokenizer | Phase 5 |
| Obsidian エクスポート時の画像処理（コピー / シンボリックリンク） | Phase 4 |
| 既存 routine 完了履歴の遡及表示方式（daily todo ファイル走査の最適化） | Phase 3 |
| 自前 Markdown パーサーの GFM 互換範囲拡張（テーブル等） | Phase 2〜 |
| WebBrowser コントロールの IE 互換モード設定（必要時のみ） | Phase 1 |
| 標準ライブラリ縛り緩和の判断（性能要件・SQLite 必要性が顕在化したとき） | Phase 4 以降 |

---

## 17. まとめ

本システムは、Markdown 本文・`meta.json`・画像ファイルを正本とし、検索・一覧・Todo 抽出・キャンバス表示などの機能を段階的に追加するローカル情報整理ツールである。

最も重要な設計方針:

```text
入力は簡単にする
本文は純粋な Markdown として保存する
管理データは meta.json で一元管理する
フォルダ階層に分類情報を持たせない
インデックスは破損しても再生成できる
正本（notes・canvases）と生成物（outputs・indexes）を明確に分ける
SQLite は正本ではなく再生成可能なインデックスとして扱う
```
