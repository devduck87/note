using System.Text;
using System.Text.RegularExpressions;

namespace NoteBase.Markdown
{
    /// <summary>
    /// Markdown 本文から要約用テキストを抽出する。
    /// ホバーツールチップやノートカード等での簡易表示に使う。
    /// 見出し・リンク記法・強調記法などの装飾を取り除き、本文相当の文字列のみ返す。
    /// </summary>
    public static class MarkdownSummary
    {
        private static readonly Regex ListMarkerRe =
            new Regex(@"^\s*[-*+]\s+(\[[ xX]\]\s+)?", RegexOptions.Compiled);
        private static readonly Regex OrderedListRe =
            new Regex(@"^\s*\d+\.\s+", RegexOptions.Compiled);
        private static readonly Regex ImageRe =
            new Regex(@"!\[([^\]]*)\]\([^)]+\)", RegexOptions.Compiled);
        private static readonly Regex LinkRe =
            new Regex(@"\[([^\]]+)\]\([^)]+\)", RegexOptions.Compiled);
        private static readonly Regex WikiAliasRe =
            new Regex(@"\[\[([^|\]]+)\|([^\]]+)\]\]", RegexOptions.Compiled);
        private static readonly Regex WikiRe =
            new Regex(@"\[\[([^\]]+)\]\]", RegexOptions.Compiled);
        private static readonly Regex CodeRe =
            new Regex(@"`([^`]+)`", RegexOptions.Compiled);
        private static readonly Regex BoldRe =
            new Regex(@"\*\*([^*]+)\*\*", RegexOptions.Compiled);
        private static readonly Regex ItalicRe =
            new Regex(@"\*([^*]+)\*", RegexOptions.Compiled);

        public static string Extract(string body, int maxChars)
        {
            if (string.IsNullOrEmpty(body)) return "";

            var normalized = body.Replace("\r\n", "\n").Replace("\r", "\n");
            var lines = normalized.Split('\n');
            var sb = new StringBuilder();
            bool inCodeFence = false;

            foreach (var raw in lines)
            {
                var line = raw;

                // コードフェンス内はスキップ
                if (line.TrimStart().StartsWith("```"))
                {
                    inCodeFence = !inCodeFence;
                    continue;
                }
                if (inCodeFence) continue;

                var trimmed = line.Trim();
                if (string.IsNullOrEmpty(trimmed)) continue;
                if (trimmed.StartsWith("#")) continue;       // 見出しは除外
                if (IsHorizontalRule(trimmed)) continue;     // 水平線

                var clean = StripMarkdown(trimmed);
                if (string.IsNullOrEmpty(clean)) continue;

                if (sb.Length > 0) sb.Append(' ');
                sb.Append(clean);

                if (sb.Length >= maxChars) break;
            }

            var result = sb.ToString();
            if (result.Length > maxChars)
                result = result.Substring(0, maxChars) + "…";
            return result;
        }

        private static bool IsHorizontalRule(string s)
        {
            return Regex.IsMatch(s, @"^(\-{3,}|\*{3,}|_{3,})$");
        }

        private static string StripMarkdown(string s)
        {
            s = ListMarkerRe.Replace(s, "");
            s = OrderedListRe.Replace(s, "");
            s = ImageRe.Replace(s, "$1");
            s = LinkRe.Replace(s, "$1");
            s = WikiAliasRe.Replace(s, "$2");
            s = WikiRe.Replace(s, "$1");
            s = CodeRe.Replace(s, "$1");
            s = BoldRe.Replace(s, "$1");
            s = ItalicRe.Replace(s, "$1");
            return s.Trim();
        }
    }
}
