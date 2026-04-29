using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;

namespace NoteBase.Markdown
{
    /// <summary>
    /// Markdown 本文から見出し情報を抽出する。
    /// アンカーリンク (#見出し) のスラグ生成と、リンクピッカー UI 用の見出し一覧を提供する。
    /// </summary>
    public class HeadingInfo
    {
        public int Level { get; set; }
        public string Text { get; set; }
        public string Slug { get; set; }
        public int LineNumber { get; set; }
    }

    public static class MarkdownIndex
    {
        private static readonly Regex HeadingRe = new Regex(
            @"^(#{1,6})\s+(.+?)\s*$", RegexOptions.Compiled);

        /// <summary>
        /// 本文から見出しを抽出する。コードフェンス内は除外する。
        /// </summary>
        public static List<HeadingInfo> ExtractHeadings(string body)
        {
            var result = new List<HeadingInfo>();
            if (string.IsNullOrEmpty(body)) return result;

            var normalized = body.Replace("\r\n", "\n").Replace("\r", "\n");
            var lines = normalized.Split('\n');
            bool inFence = false;

            for (int i = 0; i < lines.Length; i++)
            {
                var line = lines[i];
                if (line.TrimStart().StartsWith("```"))
                {
                    inFence = !inFence;
                    continue;
                }
                if (inFence) continue;

                var m = HeadingRe.Match(line);
                if (m.Success)
                {
                    var text = m.Groups[2].Value;
                    result.Add(new HeadingInfo
                    {
                        Level = m.Groups[1].Value.Length,
                        Text = text,
                        Slug = SlugifyHeading(text),
                        LineNumber = i + 1,
                    });
                }
            }
            return result;
        }

        /// <summary>
        /// 見出しテキストから HTML id 用のスラグを生成する。
        /// 規則: 空白 → '-'、ASCII 英大文字 → 小文字、その他はそのまま。両端の '-' をトリム。
        /// </summary>
        public static string SlugifyHeading(string text)
        {
            if (string.IsNullOrEmpty(text)) return "";
            var sb = new StringBuilder();
            bool lastDash = false;
            foreach (var c in text)
            {
                if (char.IsWhiteSpace(c))
                {
                    if (!lastDash && sb.Length > 0)
                    {
                        sb.Append('-');
                        lastDash = true;
                    }
                }
                else if (c >= 'A' && c <= 'Z')
                {
                    sb.Append((char)(c + 32));
                    lastDash = false;
                }
                else
                {
                    sb.Append(c);
                    lastDash = false;
                }
            }
            var s = sb.ToString();
            if (s.EndsWith("-")) s = s.TrimEnd('-');
            return s;
        }
    }
}
