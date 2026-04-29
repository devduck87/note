using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using NoteBase.Core;

namespace NoteBase.Storage
{
    /// <summary>
    /// ノートの保存・読み込み・ドラフト作成・ゴミ箱移動を担当する。
    /// </summary>
    public class NoteRepository
    {
        private static readonly UTF8Encoding Utf8NoBom = new UTF8Encoding(false);

        private readonly AppPaths _paths;
        private readonly TrashService _trash;

        public NoteRepository(AppPaths paths, TrashService trash)
        {
            _paths = paths;
            _trash = trash;
        }

        public AppPaths Paths { get { return _paths; } }
        public string GetNoteDir(string id) { return _paths.NoteDir(id); }

        /// <summary>
        /// 入力 UI で type 選択時に呼ばれる。仮 ID でフォルダを作成する。
        /// 確定保存時 (Save) でタイトルから slug を再計算してフォルダ名を rename する。
        /// </summary>
        public NoteMeta CreateDraft(NoteType type)
        {
            var now = DateTime.Now;
            var id = NoteId.Generate("untitled", now);
            id = NoteId.EnsureUnique(id, _paths.Notes, now);

            var dir = _paths.NoteDir(id);
            Directory.CreateDirectory(dir);
            Directory.CreateDirectory(_paths.ImagesDir(id));

            var meta = new NoteMeta
            {
                Id = id,
                Title = "",
                Type = type,
                Status = NoteStatus.Active,
                Tags = new List<string>(),
                Created = now,
                Updated = now,
            };
            return meta;
        }

        /// <summary>
        /// 新規ノートの初回確定保存。タイトルから slug を計算してフォルダ名を確定する。
        /// 戻り値: 確定後の NoteMeta（Id が変わっている場合あり）。
        /// </summary>
        public NoteMeta SaveNew(NoteMeta meta, string body)
        {
            if (meta == null) throw new ArgumentNullException("meta");

            var newId = NoteId.ReplaceSlug(meta.Id, meta.Title);
            if (newId != meta.Id)
            {
                if (Directory.Exists(_paths.NoteDir(newId)))
                {
                    newId = NoteId.EnsureUnique(newId, _paths.Notes, DateTime.Now);
                }
                Directory.Move(_paths.NoteDir(meta.Id), _paths.NoteDir(newId));
                meta.Id = newId;
            }
            return WriteCommon(meta, body);
        }

        /// <summary>
        /// 既存ノートの上書き保存。フォルダ名（ID）は変更しない。
        /// </summary>
        public NoteMeta SaveExisting(NoteMeta meta, string body)
        {
            if (meta == null) throw new ArgumentNullException("meta");
            return WriteCommon(meta, body);
        }

        private NoteMeta WriteCommon(NoteMeta meta, string body)
        {
            meta.Updated = DateTime.Now;
            body = SyncTitleH1(body, meta.Title);

            // アトミック書き込み: meta.json → index.md の順
            AtomicWriter.WriteTextAtomic(_paths.MetaPath(meta.Id), MetaJson.Serialize(meta));
            AtomicWriter.WriteTextAtomic(_paths.IndexMdPath(meta.Id), body);

            return meta;
        }

        public NoteMeta Load(string id, out string body)
        {
            var meta = MetaJson.Deserialize(File.ReadAllText(_paths.MetaPath(id), Utf8NoBom));
            var indexMd = _paths.IndexMdPath(id);
            body = File.Exists(indexMd) ? File.ReadAllText(indexMd, Utf8NoBom) : "";
            return meta;
        }

        /// <summary>
        /// notes/ 配下を走査して全ノートのメタを返す。壊れた meta.json はスキップ。
        /// </summary>
        public IEnumerable<NoteMeta> LoadAll()
        {
            if (!Directory.Exists(_paths.Notes)) yield break;

            foreach (var dir in Directory.EnumerateDirectories(_paths.Notes))
            {
                var metaPath = Path.Combine(dir, "meta.json");
                if (!File.Exists(metaPath)) continue;

                NoteMeta meta = null;
                try
                {
                    meta = MetaJson.Deserialize(File.ReadAllText(metaPath, Utf8NoBom));
                }
                catch
                {
                    // 壊れた meta.json は無視 (Phase 2 で警告 UI を追加予定)
                }
                if (meta != null) yield return meta;
            }
        }

        public void MoveToTrash(string id)
        {
            _trash.MoveNote(id);
        }

        /// <summary>
        /// 本文先頭の H1 をタイトルに同期する。
        /// 既に H1 があればそれを差し替え、無ければ先頭に追加する。
        /// 改行は Windows 規約の \r\n に統一して書き出す（外部エディタ・TextBox との親和性のため）。
        /// </summary>
        private static string SyncTitleH1(string body, string title)
        {
            var safeTitle = title ?? "";
            var src = (body ?? "").Replace("\r\n", "\n").Replace("\r", "\n");
            var lines = src.Split('\n');

            int i = 0;
            while (i < lines.Length && string.IsNullOrWhiteSpace(lines[i])) i++;

            if (i < lines.Length && lines[i].StartsWith("# "))
            {
                lines[i] = "# " + safeTitle;
                return string.Join("\r\n", lines);
            }

            // 先頭に挿入
            return "# " + safeTitle + "\r\n\r\n" + string.Join("\r\n", lines);
        }
    }
}
