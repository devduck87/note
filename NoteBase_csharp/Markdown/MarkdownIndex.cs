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

    public enum BlockKind
    {
        Heading,
        Paragraph,
        ListItem,
        TaskItem,
        OrderedItem,
    }

    /// <summary>
    /// リンクピッカー用のブロック情報。
    /// 見出し / 段落 / リスト項目を共通形式で表す。
    /// </summary>
    public class BlockInfo
    {
        public BlockKind Kind { get; set; }
        public int Level { get; set; }            // 見出しのみ。それ以外は 0
        public string Text { get; set; }          // 装飾を含まない表示用テキスト
        public string ExistingId { get; set; }    // 既に ^id が付いていればその値
        public string HeadingSlug { get; set; }   // 見出し時のスラグ
        public int LineStart { get; set; }
        public int LineEnd { get; set; }          // 段落は最終行を指す
        /// <summary>下層の見出しレベル（その時点で最も深い見出し）。インデント表示用。</summary>
        public int ContextLevel { get; set; }
    }

    public static class MarkdownIndex
    {
        private static readonly Regex HeadingRe = new Regex(
            @"^(#{1,6})\s+(.+?)\s*$", RegexOptions.Compiled);
        private static readonly Regex HrRe = new Regex(
            @"^(\-{3,}|\*{3,}|_{3,})$", RegexOptions.Compiled);
        private static readonly Regex TaskRe = new Regex(
            @"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$", RegexOptions.Compiled);
        private static readonly Regex UlRe = new Regex(
            @"^\s*[-*+]\s+(.+)$", RegexOptions.Compiled);
        private static readonly Regex OlRe = new Regex(
            @"^\s*\d+\.\s+(.+)$", RegexOptions.Compiled);
        private static readonly Regex BlockIdRe = new Regex(
            @"\s+\^([a-zA-Z0-9-]+)\s*$", RegexOptions.Compiled);

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
        /// 本文から見出し + 段落 + リスト項目を抽出する。リンクピッカー UI 用。
        /// コードフェンスや水平線はスキップする。
        /// </summary>
        public static List<BlockInfo> ExtractBlocks(string body)
        {
            var result = new List<BlockInfo>();
            if (string.IsNullOrEmpty(body)) return result;

            var normalized = body.Replace("\r\n", "\n").Replace("\r", "\n");
            var lines = normalized.Split('\n');
            bool inFence = false;
            int contextLevel = 0;

            int i = 0;
            while (i < lines.Length)
            {
                var line = lines[i];

                if (line.TrimStart().StartsWith("```"))
                {
                    inFence = !inFence;
                    i++;
                    continue;
                }
                if (inFence) { i++; continue; }
                if (string.IsNullOrWhiteSpace(line)) { i++; continue; }
                if (HrRe.IsMatch(line.Trim())) { i++; continue; }

                var hMatch = HeadingRe.Match(line);
                if (hMatch.Success)
                {
                    var rawText = hMatch.Groups[2].Value;
                    string id;
                    rawText = StripTrailingBlockId(rawText, out id);
                    var level = hMatch.Groups[1].Value.Length;
                    contextLevel = level;
                    result.Add(new BlockInfo
                    {
                        Kind = BlockKind.Heading,
                        Level = level,
                        Text = rawText,
                        ExistingId = id,
                        HeadingSlug = SlugifyHeading(rawText),
                        LineStart = i,
                        LineEnd = i,
                        ContextLevel = level,
                    });
                    i++;
                    continue;
                }

                var taskMatch = TaskRe.Match(line);
                if (taskMatch.Success)
                {
                    var content = taskMatch.Groups[2].Value;
                    string id;
                    content = StripTrailingBlockId(content, out id);
                    result.Add(new BlockInfo
                    {
                        Kind = BlockKind.TaskItem,
                        Text = content,
                        ExistingId = id,
                        LineStart = i,
                        LineEnd = i,
                        ContextLevel = contextLevel,
                    });
                    i++;
                    continue;
                }

                var ulMatch = UlRe.Match(line);
                if (ulMatch.Success)
                {
                    var content = ulMatch.Groups[1].Value;
                    string id;
                    content = StripTrailingBlockId(content, out id);
                    result.Add(new BlockInfo
                    {
                        Kind = BlockKind.ListItem,
                        Text = content,
                        ExistingId = id,
                        LineStart = i,
                        LineEnd = i,
                        ContextLevel = contextLevel,
                    });
                    i++;
                    continue;
                }

                var olMatch = OlRe.Match(line);
                if (olMatch.Success)
                {
                    var content = olMatch.Groups[1].Value;
                    string id;
                    content = StripTrailingBlockId(content, out id);
                    result.Add(new BlockInfo
                    {
                        Kind = BlockKind.OrderedItem,
                        Text = content,
                        ExistingId = id,
                        LineStart = i,
                        LineEnd = i,
                        ContextLevel = contextLevel,
                    });
                    i++;
                    continue;
                }

                // 段落 (連続非空行を集める)
                var paraStart = i;
                var paraLines = new List<string> { line };
                int j = i + 1;
                while (j < lines.Length
                    && !string.IsNullOrWhiteSpace(lines[j])
                    && !lines[j].StartsWith("#")
                    && !lines[j].StartsWith("```")
                    && !UlRe.IsMatch(lines[j])
                    && !OlRe.IsMatch(lines[j])
                    && !TaskRe.IsMatch(lines[j])
                    && !HrRe.IsMatch(lines[j].Trim()))
                {
                    paraLines.Add(lines[j]);
                    j++;
                }
                var lastIdx = paraLines.Count - 1;
                string paraId;
                paraLines[lastIdx] = StripTrailingBlockId(paraLines[lastIdx], out paraId);
                var paraText = string.Join(" ", paraLines).Trim();
                result.Add(new BlockInfo
                {
                    Kind = BlockKind.Paragraph,
                    Text = paraText,
                    ExistingId = paraId,
                    LineStart = paraStart,
                    LineEnd = j - 1,
                    ContextLevel = contextLevel,
                });
                i = j;
            }

            return result;
        }

        /// <summary>
        /// アンカー (見出しスラグ または ブロック ID) に対応する範囲だけを切り出す。
        /// 見出しの場合は、その見出しから次の同位階以上の見出しの直前までを返す。
        /// ブロック ID の場合は、その段落 / リスト項目だけを返す。
        /// 一致しない場合は body をそのまま返す (フォールバック)。
        /// </summary>
        public static string ExtractSection(string body, string anchor)
        {
            if (string.IsNullOrEmpty(body) || string.IsNullOrEmpty(anchor)) return body;

            var normalized = body.Replace("\r\n", "\n").Replace("\r", "\n");
            var lines = normalized.Split('\n');

            // 1) 見出しスラグでマッチ
            bool inFence = false;
            int headingStart = -1;
            int headingLevel = 0;
            for (int i = 0; i < lines.Length; i++)
            {
                var line = lines[i];
                if (line.TrimStart().StartsWith("```")) { inFence = !inFence; continue; }
                if (inFence) continue;
                var m = HeadingRe.Match(line);
                if (!m.Success) continue;
                string id;
                var text = StripTrailingBlockId(m.Groups[2].Value, out id);
                if (SlugifyHeading(text) == anchor)
                {
                    headingStart = i;
                    headingLevel = m.Groups[1].Value.Length;
                    break;
                }
            }
            if (headingStart >= 0)
            {
                int end = lines.Length;
                inFence = false;
                for (int i = headingStart + 1; i < lines.Length; i++)
                {
                    var line = lines[i];
                    if (line.TrimStart().StartsWith("```")) { inFence = !inFence; continue; }
                    if (inFence) continue;
                    var m = HeadingRe.Match(line);
                    if (m.Success && m.Groups[1].Value.Length <= headingLevel)
                    {
                        end = i;
                        break;
                    }
                }
                // 末尾の空行を削る
                while (end > headingStart + 1 && string.IsNullOrWhiteSpace(lines[end - 1]))
                    end--;
                return string.Join("\n", lines, headingStart, end - headingStart);
            }

            // 2) ブロック ID でマッチ
            var blocks = ExtractBlocks(body);
            foreach (var b in blocks)
            {
                if (b.ExistingId == anchor)
                {
                    return string.Join("\n", lines, b.LineStart, b.LineEnd - b.LineStart + 1);
                }
            }

            // 一致なし: 全文を返す
            return body;
        }

        private static string StripTrailingBlockId(string s, out string id)
        {
            if (s == null) { id = null; return null; }
            var m = BlockIdRe.Match(s);
            if (m.Success)
            {
                id = m.Groups[1].Value;
                return s.Substring(0, m.Index);
            }
            id = null;
            return s;
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
