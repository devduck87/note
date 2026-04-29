using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using NoteBase.Core;
using NoteBase.Markdown;
using NoteBase.Storage;

namespace NoteBase.UI
{
    /// <summary>
    /// ノート + 見出しを選択するダイアログ。
    /// 上段でノートを選び、下段で見出し（または「ノート全体」）を選ぶ。
    /// </summary>
    public partial class NotePickerDialog : Form
    {
        private static readonly UTF8Encoding Utf8NoBom = new UTF8Encoding(false);

        private readonly NoteRepository _repo;
        private readonly string _excludeId;
        private List<NoteMeta> _allNotes;

        public NoteMeta SelectedMeta { get; private set; }

        /// <summary>選択された見出しのスラグ（"ノート全体"のとき null）</summary>
        public string SelectedAnchor { get; private set; }

        /// <summary>選択された見出しの本文（表示用）。"ノート全体"のとき null</summary>
        public string SelectedHeadingText { get; private set; }

        public NotePickerDialog(NoteRepository repo, string excludeId = null)
        {
            _repo = repo;
            _excludeId = excludeId;
            InitializeComponent();
        }

        private void NotePickerDialog_Load(object sender, EventArgs e)
        {
            _allNotes = _repo.LoadAll()
                .Where(m => _excludeId == null || m.Id != _excludeId)
                .OrderByDescending(m => m.Updated)
                .ToList();
            ApplyFilter();
            txtSearch.Focus();
        }

        private void ApplyFilter()
        {
            var query = (txtSearch.Text ?? "").Trim();
            lvNotes.BeginUpdate();
            try
            {
                lvNotes.Items.Clear();
                foreach (var m in _allNotes
                    .Where(x => string.IsNullOrEmpty(query)
                        || (x.Title ?? "").IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0))
                {
                    var item = new ListViewItem(m.Title ?? "(無題)");
                    item.SubItems.Add(m.Type.DisplayName());
                    item.SubItems.Add(m.Updated.ToString("yyyy-MM-dd HH:mm"));
                    item.Tag = m;
                    lvNotes.Items.Add(item);
                }
                if (lvNotes.Items.Count > 0)
                    lvNotes.Items[0].Selected = true;
            }
            finally
            {
                lvNotes.EndUpdate();
            }
        }

        private void TxtSearch_TextChanged(object sender, EventArgs e)
        {
            ApplyFilter();
        }

        private void TxtSearch_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Down && lvNotes.Items.Count > 0)
            {
                lvNotes.Focus();
                e.Handled = true;
            }
        }

        private void LvNotes_SelectedIndexChanged(object sender, EventArgs e)
        {
            // 選択ノートの見出しを下段に表示
            lstHeadings.Items.Clear();
            // 「ノート全体」を先頭に常時用意 (Tag = null)
            lstHeadings.Items.Add(new HeadingItem(null, "ノート全体（見出しなし）"));

            if (lvNotes.SelectedItems.Count == 0)
            {
                lstHeadings.SelectedIndex = 0;
                return;
            }
            var meta = (NoteMeta)lvNotes.SelectedItems[0].Tag;
            try
            {
                var bodyPath = _repo.Paths.IndexMdPath(meta.Id);
                if (File.Exists(bodyPath))
                {
                    var body = File.ReadAllText(bodyPath, Utf8NoBom);
                    var headings = MarkdownIndex.ExtractHeadings(body);
                    foreach (var h in headings)
                    {
                        var indent = new string(' ', (h.Level - 1) * 2);
                        var marker = new string('#', h.Level);
                        var display = indent + marker + " " + h.Text;
                        lstHeadings.Items.Add(new HeadingItem(h, display));
                    }
                }
            }
            catch
            {
                // 読み込みエラーは黙って無視 (見出しなし状態)
            }
            lstHeadings.SelectedIndex = 0;
        }

        private void LvNotes_DoubleClick(object sender, EventArgs e)
        {
            // 一覧側のダブルクリックは「ノート全体」での挿入
            if (lvNotes.SelectedItems.Count == 0) return;
            lstHeadings.SelectedIndex = 0;
            Confirm();
        }

        private void LvNotes_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                Confirm();
                e.Handled = true;
            }
        }

        private void LstHeadings_DoubleClick(object sender, EventArgs e)
        {
            Confirm();
        }

        private void LstHeadings_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                Confirm();
                e.Handled = true;
            }
        }

        private void BtnOk_Click(object sender, EventArgs e)
        {
            Confirm();
        }

        private void Confirm()
        {
            if (lvNotes.SelectedItems.Count == 0)
            {
                if (lvNotes.Items.Count == 0) return;
                lvNotes.Items[0].Selected = true;
            }
            SelectedMeta = (NoteMeta)lvNotes.SelectedItems[0].Tag;

            HeadingItem h = null;
            if (lstHeadings.SelectedItem is HeadingItem)
                h = (HeadingItem)lstHeadings.SelectedItem;
            if (h != null && h.Heading != null)
            {
                SelectedAnchor = h.Heading.Slug;
                SelectedHeadingText = h.Heading.Text;
            }
            else
            {
                SelectedAnchor = null;
                SelectedHeadingText = null;
            }
            this.DialogResult = DialogResult.OK;
            Close();
        }

        private class HeadingItem
        {
            public HeadingInfo Heading { get; private set; }
            private readonly string _display;
            public HeadingItem(HeadingInfo h, string display)
            {
                Heading = h;
                _display = display;
            }
            public override string ToString() { return _display; }
        }
    }
}
