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

        /// <summary>選択されたアンカー（見出しのスラグ or ブロック ID）。"ノート全体"のとき null</summary>
        public string SelectedAnchor { get; private set; }

        /// <summary>表示用テキスト（見出し名 or ブロックの先頭抜粋）</summary>
        public string SelectedHeadingText { get; private set; }

        /// <summary>選択されたブロックの種別。見出しなら Heading。null なら見出しでない（または全体）</summary>
        public BlockKind? SelectedBlockKind { get; private set; }

        /// <summary>選択されたブロックの最終行番号（^id 自動付与のために使う）</summary>
        public int SelectedBlockLineEnd { get; private set; } = -1;

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
            // 選択ノートのブロック (見出し / 段落 / リスト項目) を下段に表示
            lstHeadings.Items.Clear();
            lstHeadings.Items.Add(new BlockItem(null, "ノート全体（見出しなし）"));

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
                    var blocks = MarkdownIndex.ExtractBlocks(body);
                    foreach (var b in blocks)
                    {
                        lstHeadings.Items.Add(new BlockItem(b, FormatBlock(b)));
                    }
                }
            }
            catch
            {
                // 読み込みエラーは無視
            }
            lstHeadings.SelectedIndex = 0;
        }

        private static string FormatBlock(BlockInfo b)
        {
            var ctx = b.ContextLevel;
            // 段落・リスト項目は最も近い見出しの 1 段下にインデント
            int indentLevel;
            string marker;
            switch (b.Kind)
            {
                case BlockKind.Heading:
                    indentLevel = b.Level - 1;
                    marker = new string('#', b.Level);
                    break;
                case BlockKind.TaskItem:
                    indentLevel = ctx;
                    marker = "□";
                    break;
                case BlockKind.ListItem:
                    indentLevel = ctx;
                    marker = "•";
                    break;
                case BlockKind.OrderedItem:
                    indentLevel = ctx;
                    marker = "1.";
                    break;
                case BlockKind.Paragraph:
                default:
                    indentLevel = ctx;
                    marker = "¶";
                    break;
            }
            var indent = new string(' ', indentLevel * 2);
            var text = b.Text ?? "";
            if (text.Length > 60) text = text.Substring(0, 60) + "…";
            var idTag = string.IsNullOrEmpty(b.ExistingId) ? "" : "  ^" + b.ExistingId;
            return indent + marker + " " + text + idTag;
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

            BlockItem item = null;
            if (lstHeadings.SelectedItem is BlockItem)
                item = (BlockItem)lstHeadings.SelectedItem;

            if (item == null || item.Block == null)
            {
                // ノート全体
                SelectedAnchor = null;
                SelectedHeadingText = null;
                SelectedBlockKind = null;
                SelectedBlockLineEnd = -1;
            }
            else if (item.Block.Kind == BlockKind.Heading)
            {
                SelectedAnchor = item.Block.HeadingSlug;
                SelectedHeadingText = item.Block.Text;
                SelectedBlockKind = BlockKind.Heading;
                SelectedBlockLineEnd = item.Block.LineEnd;
            }
            else
            {
                // 段落 / リスト項目: 既存の ID があればそれを返す。
                // 無ければ呼び出し側で EnsureBlockId を呼んで確保してもらう (LineEnd を使う)
                SelectedAnchor = item.Block.ExistingId; // null になりうる
                SelectedHeadingText = item.Block.Text;
                SelectedBlockKind = item.Block.Kind;
                SelectedBlockLineEnd = item.Block.LineEnd;
            }
            this.DialogResult = DialogResult.OK;
            Close();
        }

        private class BlockItem
        {
            public BlockInfo Block { get; private set; }
            private readonly string _display;
            public BlockItem(BlockInfo b, string display)
            {
                Block = b;
                _display = display;
            }
            public override string ToString() { return _display; }
        }
    }
}
