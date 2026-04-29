using System;
using System.Linq;
using System.Windows.Forms;
using NoteBase.Core;
using NoteBase.Markdown;
using NoteBase.Storage;

namespace NoteBase.UI
{
    /// <summary>
    /// メイン画面: ノート一覧 + プレビュー + 検索 + 新規作成。
    /// </summary>
    public partial class MainForm : Form
    {
        private readonly AppPaths _paths;
        private readonly NoteRepository _repo;
        private readonly TrashService _trash;

        public MainForm()
        {
            InitializeComponent();

            _paths = AppPaths.Default();
            _paths.EnsureLayout();
            _trash = new TrashService(_paths);
            _repo = new NoteRepository(_paths, _trash);
        }

        private void MainForm_Load(object sender, EventArgs e)
        {
            RefreshNoteList();
        }

        private void RefreshNoteList()
        {
            lvNotes.BeginUpdate();
            try
            {
                lvNotes.Items.Clear();
                var query = (txtSearch.Text ?? "").Trim();

                var notes = _repo.LoadAll()
                    .Where(m => string.IsNullOrEmpty(query)
                        || (m.Title ?? "").IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0)
                    .OrderByDescending(m => m.Updated);

                foreach (var meta in notes)
                {
                    var item = new ListViewItem(meta.Title ?? "(無題)");
                    item.SubItems.Add(meta.Type.DisplayName());
                    item.SubItems.Add(meta.Updated.ToString("yyyy-MM-dd HH:mm"));
                    item.Tag = meta.Id;
                    lvNotes.Items.Add(item);
                }
            }
            finally
            {
                lvNotes.EndUpdate();
            }
        }

        private void TxtSearch_TextChanged(object sender, EventArgs e)
        {
            RefreshNoteList();
        }

        private void LvNotes_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (lvNotes.SelectedItems.Count == 0)
            {
                webPreview.DocumentText = "";
                return;
            }

            var id = (string)lvNotes.SelectedItems[0].Tag;
            try
            {
                string body;
                _repo.Load(id, out body);
                ShowPreview(id, body);
            }
            catch (Exception ex)
            {
                var safe = (ex.Message ?? "")
                    .Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;");
                webPreview.DocumentText =
                    "<html><body><pre>読み込みエラー: " + safe + "</pre></body></html>";
            }
        }

        private void ShowPreview(string id, string body)
        {
            var html = MarkdownToHtml.Convert(body);
            var noteDir = _paths.NoteDir(id);
            var baseUrl = "file:///" + noteDir.Replace('\\', '/').TrimEnd('/') + "/";

            var doc = "<!DOCTYPE html><html><head>"
                + "<base href=\"" + baseUrl + "\"/>"
                + "<meta charset=\"utf-8\"/>"
                + "<style>"
                + "body{font-family:'Segoe UI','Yu Gothic UI','Meiryo',sans-serif;font-size:11pt;padding:12px;color:#222;}"
                + "h1{border-bottom:1px solid #ccc;padding-bottom:4px;}"
                + "h2{border-bottom:1px solid #eee;padding-bottom:2px;}"
                + "code{background:#f4f4f4;padding:1px 4px;border-radius:3px;font-family:Consolas,monospace;}"
                + "pre{background:#f4f4f4;padding:8px;overflow:auto;border-radius:3px;}"
                + "pre code{background:none;padding:0;}"
                + "img{max-width:100%;border:1px solid #ddd;}"
                + "ul.task-list{list-style:none;padding-left:1em;}"
                + "ul.task-list li input{margin-right:6px;}"
                + "</style></head><body>"
                + html
                + "</body></html>";
            webPreview.DocumentText = doc;
        }

        private void BtnNew_Click(object sender, EventArgs e)
        {
            using (var form = new NoteEditForm(_repo))
            {
                if (form.ShowDialog(this) == DialogResult.OK)
                {
                    RefreshNoteList();
                }
            }
        }

        private void MainForm_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Control && e.KeyCode == Keys.N)
            {
                BtnNew_Click(this, EventArgs.Empty);
                e.Handled = true;
            }
        }
    }
}
