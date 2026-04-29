using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;

namespace NoteBase.Markdown
{
    /// <summary>
    /// Markdown を HTML に変換する。GFM サブセット + 独自 wiki link [[Title]] に対応:
    /// 見出し / 段落 / 箇条書き / 番号付きリスト / タスクリスト /
    /// 強調 / 斜体 / インラインコード / コードブロック (フェンス) /
    /// 画像 / リンク / 水平線 / wiki link。
    /// テーブル・引用・脚注などは Phase 2 以降で対応する。
    /// </summary>
    public static class MarkdownToHtml
    {
        private static readonly Regex HeadingRe = new Regex(@"^(#{1,6})\s+(.+)$", RegexOptions.Compiled);
        private static readonly Regex HrRe = new Regex(@"^(\-{3,}|\*{3,}|_{3,})$", RegexOptions.Compiled);
        private static readonly Regex TaskRe = new Regex(@"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$", RegexOptions.Compiled);
        private static readonly Regex UlRe = new Regex(@"^\s*[-*+]\s+(.+)$", RegexOptions.Compiled);
        private static readonly Regex OlRe = new Regex(@"^\s*\d+\.\s+(.+)$", RegexOptions.Compiled);
        private static readonly Regex ImageRe = new Regex(@"^!\[([^\]]*)\]\(([^)]+)\)", RegexOptions.Compiled);
        private static readonly Regex LinkRe = new Regex(@"^\[([^\]]+)\]\(([^)]+)\)", RegexOptions.Compiled);

        public static string Convert(string markdown)
        {
            return Convert(markdown, null, null);
        }

        /// <summary>
        /// Markdown を HTML に変換する。
        /// </summary>
        /// <param name="markdown">変換対象</param>
        /// <param name="titleResolver">[[Title]] 用のタイトル→ノートID解決関数 (null 可)</param>
        /// <param name="baseUrl">画像・リンクの相対パス解決用のベース URL (例: "file:///c:/.../notes/&lt;id&gt;/", null 可)</param>
        public static string Convert(string markdown, Func<string, string> titleResolver, string baseUrl = null)
        {
            if (string.IsNullOrEmpty(markdown)) return "";

            Uri baseUri = null;
            if (!string.IsNullOrEmpty(baseUrl))
                Uri.TryCreate(baseUrl, UriKind.Absolute, out baseUri);

            var normalized = markdown.Replace("\r\n", "\n").Replace("\r", "\n");
            var lines = normalized.Split('\n');

            var sb = new StringBuilder();
            int i = 0;
            bool inUl = false;
            bool inOl = false;

            while (i < lines.Length)
            {
                var line = lines[i];

                // 空行
                if (string.IsNullOrWhiteSpace(line))
                {
                    CloseLists(sb, ref inUl, ref inOl);
                    i++;
                    continue;
                }

                // コードフェンス ```
                if (line.StartsWith("```"))
                {
                    CloseLists(sb, ref inUl, ref inOl);
                    var lang = line.Substring(3).Trim();
                    sb.Append("<pre><code");
                    if (!string.IsNullOrEmpty(lang))
                        sb.Append(" class=\"language-").Append(EscapeHtml(lang)).Append("\"");
                    sb.Append(">");
                    i++;
                    while (i < lines.Length && !lines[i].StartsWith("```"))
                    {
                        sb.Append(EscapeHtml(lines[i])).Append("\n");
                        i++;
                    }
                    if (i < lines.Length) i++; // 終端 ``` を消費
                    sb.Append("</code></pre>\n");
                    continue;
                }

                // 水平線
                if (HrRe.IsMatch(line.Trim()))
                {
                    CloseLists(sb, ref inUl, ref inOl);
                    sb.Append("<hr/>\n");
                    i++;
                    continue;
                }

                // 見出し
                var hMatch = HeadingRe.Match(line);
                if (hMatch.Success)
                {
                    CloseLists(sb, ref inUl, ref inOl);
                    var level = hMatch.Groups[1].Value.Length;
                    var content = ProcessInline(hMatch.Groups[2].Value, titleResolver, baseUri);
                    sb.Append("<h").Append(level).Append(">")
                      .Append(content)
                      .Append("</h").Append(level).Append(">\n");
                    i++;
                    continue;
                }

                // タスクリスト
                var taskMatch = TaskRe.Match(line);
                if (taskMatch.Success)
                {
                    if (inOl) { sb.Append("</ol>\n"); inOl = false; }
                    if (!inUl) { sb.Append("<ul class=\"task-list\">\n"); inUl = true; }
                    var checkedAttr = (taskMatch.Groups[1].Value.ToLowerInvariant() == "x")
                        ? " checked" : "";
                    var content = ProcessInline(taskMatch.Groups[2].Value, titleResolver, baseUri);
                    sb.Append("<li><input type=\"checkbox\" disabled")
                      .Append(checkedAttr)
                      .Append("/> ")
                      .Append(content)
                      .Append("</li>\n");
                    i++;
                    continue;
                }

                // 順不同リスト
                var ulMatch = UlRe.Match(line);
                if (ulMatch.Success)
                {
                    if (inOl) { sb.Append("</ol>\n"); inOl = false; }
                    if (!inUl) { sb.Append("<ul>\n"); inUl = true; }
                    sb.Append("<li>")
                      .Append(ProcessInline(ulMatch.Groups[1].Value, titleResolver, baseUri))
                      .Append("</li>\n");
                    i++;
                    continue;
                }

                // 順序付きリスト
                var olMatch = OlRe.Match(line);
                if (olMatch.Success)
                {
                    if (inUl) { sb.Append("</ul>\n"); inUl = false; }
                    if (!inOl) { sb.Append("<ol>\n"); inOl = true; }
                    sb.Append("<li>")
                      .Append(ProcessInline(olMatch.Groups[1].Value, titleResolver, baseUri))
                      .Append("</li>\n");
                    i++;
                    continue;
                }

                // 段落（連続する非空行は <br/> で結合）
                CloseLists(sb, ref inUl, ref inOl);
                sb.Append("<p>");
                sb.Append(ProcessInline(line, titleResolver, baseUri));
                i++;
                while (i < lines.Length && !string.IsNullOrWhiteSpace(lines[i])
                    && !lines[i].StartsWith("#")
                    && !lines[i].StartsWith("```")
                    && !UlRe.IsMatch(lines[i])
                    && !OlRe.IsMatch(lines[i])
                    && !TaskRe.IsMatch(lines[i])
                    && !HrRe.IsMatch(lines[i].Trim()))
                {
                    sb.Append("<br/>");
                    sb.Append(ProcessInline(lines[i], titleResolver, baseUri));
                    i++;
                }
                sb.Append("</p>\n");
            }

            CloseLists(sb, ref inUl, ref inOl);
            return sb.ToString();
        }

        private static void CloseLists(StringBuilder sb, ref bool inUl, ref bool inOl)
        {
            if (inUl) { sb.Append("</ul>\n"); inUl = false; }
            if (inOl) { sb.Append("</ol>\n"); inOl = false; }
        }

        private static string ResolveUrl(string url, Uri baseUri)
        {
            if (baseUri == null || string.IsNullOrEmpty(url)) return url;
            // 既に絶対 URI ならそのまま (http(s)://, file://, mailto: など)
            Uri abs;
            if (Uri.TryCreate(url, UriKind.Absolute, out abs)) return url;
            // 相対 URI を baseUri の下で解決
            Uri resolved;
            if (Uri.TryCreate(baseUri, url, out resolved)) return resolved.AbsoluteUri;
            return url;
        }

        /// <summary>
        /// インライン要素を処理する。
        /// 順序: コード → 画像 → wiki link → リンク → 強調 → 斜体 → 通常文字。
        /// </summary>
        private static string ProcessInline(string text, Func<string, string> titleResolver, Uri baseUri)
        {
            if (string.IsNullOrEmpty(text)) return "";

            var sb = new StringBuilder();
            int i = 0;
            while (i < text.Length)
            {
                // インラインコード `...`
                if (text[i] == '`')
                {
                    int end = text.IndexOf('`', i + 1);
                    if (end > i)
                    {
                        var code = text.Substring(i + 1, end - i - 1);
                        sb.Append("<code>").Append(EscapeHtml(code)).Append("</code>");
                        i = end + 1;
                        continue;
                    }
                }

                // 画像 ![alt](src)
                if (text[i] == '!' && i + 1 < text.Length && text[i + 1] == '[')
                {
                    var m = ImageRe.Match(text.Substring(i));
                    if (m.Success)
                    {
                        var alt = EscapeHtml(m.Groups[1].Value);
                        var src = EscapeHtml(ResolveUrl(m.Groups[2].Value, baseUri));
                        sb.Append("<img src=\"").Append(src)
                          .Append("\" alt=\"").Append(alt).Append("\"/>");
                        i += m.Length;
                        continue;
                    }
                }

                // wiki link [[Title]] または [[Title|alias]]
                if (text[i] == '[' && i + 1 < text.Length && text[i + 1] == '[')
                {
                    int end = text.IndexOf("]]", i + 2);
                    if (end > i + 1)
                    {
                        var inner = text.Substring(i + 2, end - i - 2);
                        string title, alias;
                        var pipeIdx = inner.IndexOf('|');
                        if (pipeIdx >= 0)
                        {
                            title = inner.Substring(0, pipeIdx).Trim();
                            alias = inner.Substring(pipeIdx + 1).Trim();
                        }
                        else
                        {
                            title = inner.Trim();
                            alias = null;
                        }

                        string id = (titleResolver != null) ? titleResolver(title) : null;
                        if (!string.IsNullOrEmpty(id))
                        {
                            var wikiHref = EscapeHtml(ResolveUrl("../" + id + "/index.md", baseUri));
                            sb.Append("<a href=\"").Append(wikiHref).Append("\">")
                              .Append(EscapeHtml(alias ?? title))
                              .Append("</a>");
                        }
                        else
                        {
                            // 解決できない (リゾルバなし or タイトル未一致) → 注意喚起付きで原文表示
                            sb.Append("<span class=\"unresolved-link\">[[")
                              .Append(EscapeHtml(inner))
                              .Append("]]</span>");
                        }
                        i = end + 2;
                        continue;
                    }
                }

                // リンク [text](url)
                if (text[i] == '[')
                {
                    var m = LinkRe.Match(text.Substring(i));
                    if (m.Success)
                    {
                        var label = ProcessInline(m.Groups[1].Value, titleResolver, baseUri);
                        var url = EscapeHtml(ResolveUrl(m.Groups[2].Value, baseUri));
                        sb.Append("<a href=\"").Append(url).Append("\">")
                          .Append(label).Append("</a>");
                        i += m.Length;
                        continue;
                    }
                }

                // 強調 **bold**
                if (i + 1 < text.Length && text[i] == '*' && text[i + 1] == '*')
                {
                    int end = text.IndexOf("**", i + 2);
                    if (end > i)
                    {
                        var inner = text.Substring(i + 2, end - i - 2);
                        sb.Append("<strong>").Append(ProcessInline(inner, titleResolver, baseUri)).Append("</strong>");
                        i = end + 2;
                        continue;
                    }
                }

                // 斜体 *italic*
                if (text[i] == '*')
                {
                    int end = text.IndexOf('*', i + 1);
                    if (end > i)
                    {
                        var inner = text.Substring(i + 1, end - i - 1);
                        sb.Append("<em>").Append(ProcessInline(inner, titleResolver, baseUri)).Append("</em>");
                        i = end + 1;
                        continue;
                    }
                }

                // 通常文字
                sb.Append(EscapeHtmlChar(text[i]));
                i++;
            }
            return sb.ToString();
        }

        private static string EscapeHtml(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            return s.Replace("&", "&amp;")
                    .Replace("<", "&lt;")
                    .Replace(">", "&gt;")
                    .Replace("\"", "&quot;");
        }

        private static string EscapeHtmlChar(char c)
        {
            switch (c)
            {
                case '&': return "&amp;";
                case '<': return "&lt;";
                case '>': return "&gt;";
                case '"': return "&quot;";
                default: return c.ToString();
            }
        }
    }
}
