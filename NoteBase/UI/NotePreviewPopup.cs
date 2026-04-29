using System;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace NoteBase.UI
{
    /// <summary>
    /// リンクホバー時に表示する小型プレビューウィンドウ。
    /// メインのプレビュー用とは別の一時 HTML ファイルへ書き出して表示する。
    /// アクティブにならない (フォーカスを奪わない) 設定で表示する。
    /// </summary>
    public partial class NotePreviewPopup : Form
    {
        private static readonly UTF8Encoding Utf8NoBom = new UTF8Encoding(false);
        private readonly string _tempHtmlPath;
        private string _currentNoteId;
        private string _pendingAnchor;

        public NotePreviewPopup()
        {
            InitializeComponent();
            _tempHtmlPath = Path.Combine(Path.GetTempPath(), "notebase_hover_preview.html");
            webContent.Navigating += WebContent_Navigating;
            webContent.DocumentCompleted += WebContent_DocumentCompleted;
        }

        // フォーカスを奪わずに表示する
        protected override bool ShowWithoutActivation
        {
            get { return true; }
        }

        protected override CreateParams CreateParams
        {
            get
            {
                const int WS_EX_NOACTIVATE = 0x08000000;
                const int WS_EX_TOOLWINDOW = 0x00000080;
                var cp = base.CreateParams;
                cp.ExStyle |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW;
                return cp;
            }
        }

        /// <summary>
        /// ポップアップに表示する HTML を更新する。
        /// anchor が指定されていればドキュメント読込完了後に該当要素までスクロールする。
        /// </summary>
        public void SetContent(string noteId, string innerHtml, string anchor = null)
        {
            _currentNoteId = noteId;
            _pendingAnchor = string.IsNullOrEmpty(anchor) ? null : anchor;

            var doc = "<!DOCTYPE html><html><head>"
                + "<meta charset=\"utf-8\"/>"
                + "<style>"
                + "body{font-family:'Segoe UI','Yu Gothic UI','Meiryo',sans-serif;font-size:10pt;padding:10px;color:#222;}"
                + "h1{font-size:14pt;border-bottom:1px solid #ccc;padding-bottom:3px;margin-top:0;}"
                + "h2{font-size:12pt;border-bottom:1px solid #eee;padding-bottom:2px;}"
                + "h3{font-size:11pt;}"
                + "code{background:#f4f4f4;padding:1px 4px;border-radius:3px;font-family:Consolas,monospace;}"
                + "pre{background:#f4f4f4;padding:6px;overflow:auto;border-radius:3px;font-size:9pt;}"
                + "pre code{background:none;padding:0;}"
                + "img{max-width:100%;border:1px solid #ddd;}"
                + "ul.task-list{list-style:none;padding-left:1em;}"
                + "ul.task-list li input{margin-right:6px;}"
                + ".unresolved-link{color:#c00;}"
                + "a{color:#0a58ca;}"
                + "</style></head><body>"
                + innerHtml
                + "</body></html>";

            File.WriteAllText(_tempHtmlPath, doc, Utf8NoBom);
            webContent.Navigate(_tempHtmlPath);
        }

        public string CurrentNoteId
        {
            get { return _currentNoteId; }
        }

        private void WebContent_DocumentCompleted(object sender, WebBrowserDocumentCompletedEventArgs e)
        {
            if (string.IsNullOrEmpty(_pendingAnchor)) return;
            var anchor = _pendingAnchor;
            _pendingAnchor = null;
            try
            {
                if (webContent.Document != null)
                {
                    var elem = webContent.Document.GetElementById(anchor);
                    if (elem != null) elem.ScrollIntoView(true);
                }
            }
            catch
            {
                // スクロール失敗は無視
            }
        }

        private void WebContent_Navigating(object sender, WebBrowserNavigatingEventArgs e)
        {
            var uri = e.Url;
            if (uri == null) return;
            var url = uri.AbsoluteUri ?? "";
            // 自前 HTML への Navigate は素通し
            if (url == "about:blank" || string.IsNullOrEmpty(url)) return;
            if (uri.IsFile && string.Equals(uri.LocalPath, _tempHtmlPath,
                StringComparison.OrdinalIgnoreCase)) return;

            // ホバープレビュー内のリンク遷移はブロック
            // (本体プレビュー側で開く設計)
            e.Cancel = true;
        }
    }
}
