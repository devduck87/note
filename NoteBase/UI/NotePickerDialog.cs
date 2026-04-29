using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;
using NoteBase.Core;
using NoteBase.Storage;

namespace NoteBase.UI
{
    /// <summary>
    /// ノートを 1 件選択するダイアログ。
    /// 検索ボックスでタイトルを絞り込み、Enter または ダブルクリックで確定する。
    /// </summary>
    public partial class NotePickerDialog : Form
    {
        private readonly NoteRepository _repo;
        private readonly string _excludeId;
        private List<NoteMeta> _allNotes;

        public NoteMeta SelectedMeta { get; private set; }

        /// <summary>
        /// </summary>
        /// <param name="repo">ノートリポジトリ</param>
        /// <param name="excludeId">除外する ID（自分自身を選ばせない用途、null 可）</param>
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
            // 検索ボックスから矢印キーで一覧へフォーカス移動
            if (e.KeyCode == Keys.Down && lvNotes.Items.Count > 0)
            {
                lvNotes.Focus();
                e.Handled = true;
            }
        }

        private void LvNotes_DoubleClick(object sender, EventArgs e)
        {
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
            this.DialogResult = DialogResult.OK;
            Close();
        }
    }
}
