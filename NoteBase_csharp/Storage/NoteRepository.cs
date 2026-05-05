using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
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

        // ============================================================
        // ブロック ID 自動付与 (Phase 3b)
        // ============================================================

        private static readonly Regex BlockIdRe =
            new Regex(@"\s+\^([a-zA-Z0-9-]+)\s*$", RegexOptions.Compiled);
        private static readonly Regex AnyBlockIdRe =
            new Regex(@"\s\^([a-zA-Z0-9-]+)", RegexOptions.Compiled);
        private static readonly Random _idRandom = new Random();
        private static readonly object _idLock = new object();
        private const string IdAlphabet = "abcdefghijklmnopqrstuvwxyz0123456789";

        /// <summary>
        /// 指定行末にブロック ID (^xxxxxx) を確保する。既に ID が付いていればそれを返す。
        /// 付いていなければ生成して該当行末に追記し、上書き保存する。
        /// </summary>
        /// <param name="noteId">対象ノート ID</param>
        /// <param name="lineEnd">ID を付与する行 (0 始まり)</param>
        /// <returns>確保された ID</returns>
        public string EnsureBlockId(string noteId, int lineEnd)
        {
            string body;
            var meta = Load(noteId, out body);

            var normalized = (body ?? "").Replace("\r\n", "\n").Replace("\r", "\n");
            var lines = normalized.Split('\n');
            if (lineEnd < 0 || lineEnd >= lines.Length) return null;

            // 既存 ID のチェック
            var existing = BlockIdRe.Match(lines[lineEnd]);
            if (existing.Success) return existing.Groups[1].Value;

            // 重複しない新規 ID を生成
            var allIds = ExtractAllBlockIds(body);
            string newId;
            for (int attempt = 0; ; attempt++)
            {
                newId = GenerateBlockId();
                if (!allIds.Contains(newId)) break;
                if (attempt > 100) return null; // 念のため
            }

            // 行末へ追記 (前後の空白整理)
            var rebuilt = new string[lines.Length];
            for (int i = 0; i < lines.Length; i++) rebuilt[i] = lines[i];
            var trimmed = rebuilt[lineEnd].TrimEnd();
            if (trimmed.Length == 0) return null; // 空行には付けない
            rebuilt[lineEnd] = trimmed + " ^" + newId;

            var newBody = string.Join("\r\n", rebuilt);
            SaveExisting(meta, newBody);
            return newId;
        }

        private static HashSet<string> ExtractAllBlockIds(string body)
        {
            var set = new HashSet<string>(StringComparer.Ordinal);
            if (string.IsNullOrEmpty(body)) return set;
            foreach (Match m in AnyBlockIdRe.Matches(body))
                set.Add(m.Groups[1].Value);
            return set;
        }

        private static string GenerateBlockId()
        {
            var sb = new StringBuilder(6);
            lock (_idLock)
            {
                for (int i = 0; i < 6; i++)
                    sb.Append(IdAlphabet[_idRandom.Next(IdAlphabet.Length)]);
            }
            return sb.ToString();
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
