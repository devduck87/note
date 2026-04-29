using System;
using System.IO;
using System.Text.RegularExpressions;

namespace NoteBase.Core
{
    /// <summary>
    /// ノート ID 生成・slug 化のユーティリティ。
    /// 形式: yyyyMMdd-HHmmss-&lt;slug&gt; （衝突時は末尾にミリ秒や連番を付与）
    /// </summary>
    public static class NoteId
    {
        private static readonly Regex AsciiSlugChars =
            new Regex(@"[^a-z0-9]+", RegexOptions.Compiled);

        public static string Generate(string title, DateTime now)
        {
            var stamp = now.ToString("yyyyMMdd-HHmmss");
            var slug = Slugify(title);
            return stamp + "-" + slug;
        }

        public static string Slugify(string title)
        {
            if (string.IsNullOrEmpty(title)) return "untitled";
            var lower = title.ToLowerInvariant();
            var slug = AsciiSlugChars.Replace(lower, "-").Trim('-');
            if (string.IsNullOrEmpty(slug)) return "untitled";
            if (slug.Length > 60) slug = slug.Substring(0, 60).TrimEnd('-');
            if (string.IsNullOrEmpty(slug)) return "untitled";
            return slug;
        }

        /// <summary>
        /// parentDir 以下に同名フォルダが存在する場合、衝突回避した ID を返す。
        /// </summary>
        public static string EnsureUnique(string id, string parentDir, DateTime now)
        {
            if (!Directory.Exists(Path.Combine(parentDir, id))) return id;

            var ms = now.Millisecond.ToString("D3");
            var candidate = id + "-" + ms;
            if (!Directory.Exists(Path.Combine(parentDir, candidate))) return candidate;

            for (int i = 2; i < 1000; i++)
            {
                candidate = id + "-" + ms + "-" + i;
                if (!Directory.Exists(Path.Combine(parentDir, candidate)))
                    return candidate;
            }
            throw new InvalidOperationException("Failed to generate unique note id: " + id);
        }

        /// <summary>
        /// id の slug 部分を新しい slug に差し替える。
        /// 例: 20260428-090000-untitled → 20260428-090000-new-slug
        /// </summary>
        public static string ReplaceSlug(string id, string newTitle)
        {
            var parts = id.Split('-');
            if (parts.Length < 3) return id;
            return parts[0] + "-" + parts[1] + "-" + Slugify(newTitle);
        }
    }
}
