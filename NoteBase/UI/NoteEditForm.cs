using System;
using System.Linq;
using System.Windows.Forms;
using NoteBase.Core;
using NoteBase.Storage;

namespace NoteBase.UI
{
    /// <summary>
    /// 新規ノート入力 UI。
    /// type 選択直後にドラフトフォルダを作成し、保存時にタイトル確定でフォルダを rename する。
    /// キャンセル時はフォルダごと trash へ移動する。
    /// 画像貼り付け / DnD は MarkdownTextBox が担当する。
    /// </summary>
    public partial class NoteEditForm : Form
    {
        private readonly NoteRepository _repo;
        private readonly ImageStore _imageStore;
        private NoteMeta _draft;
        private bool _saved;

        public NoteEditForm(NoteRepository repo)
        {
            _repo = repo;
            _imageStore = new ImageStore();
            InitializeComponent();

            cmbType.Items.AddRange(new object[]
            {
                NoteType.Memo,
                NoteType.Procedure,
                NoteType.Todo,
                NoteType.Routine,
                NoteType.Checklist,
                NoteType.Daily,
                NoteType.Project,
                NoteType.Log,
            });
            cmbType.Format += CmbType_Format;
            cmbType.SelectedIndex = 0;
        }

        private void CmbType_Format(object sender, ListControlConvertEventArgs e)
        {
            if (e.ListItem is NoteType)
                e.Value = ((NoteType)e.ListItem).DisplayName();
        }

        private void CmbType_SelectedIndexChanged(object sender, EventArgs e)
        {
            // 既存ドラフトがあれば破棄
            if (_draft != null && !_saved)
            {
                _repo.MoveToTrash(_draft.Id);
            }
            _saved = false;
            var type = (NoteType)cmbType.SelectedItem;
            _draft = _repo.CreateDraft(type);
            txtBody.NoteDir = _repo.GetNoteDir(_draft.Id);
        }

        private void BtnAddImage_Click(object sender, EventArgs e)
        {
            using (var dialog = new OpenFileDialog())
            {
                dialog.Filter = "画像 (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp)|"
                              + "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp";
                dialog.Multiselect = true;
                if (dialog.ShowDialog(this) == DialogResult.OK)
                {
                    foreach (var f in dialog.FileNames.Where(ImageStore.IsImageFile))
                    {
                        var rel = _imageStore.SaveDroppedImage(_repo.GetNoteDir(_draft.Id), f);
                        InsertAtCursor("![](" + rel + ")\n");
                    }
                }
            }
        }

        private void InsertAtCursor(string text)
        {
            int pos = txtBody.SelectionStart;
            txtBody.Text = txtBody.Text.Insert(pos, text);
            txtBody.SelectionStart = pos + text.Length;
            txtBody.SelectionLength = 0;
            txtBody.Focus();
        }

        private void BtnSave_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(txtTitle.Text))
            {
                MessageBox.Show(this, "タイトルを入力してください。", "確認",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                txtTitle.Focus();
                return;
            }
            _draft.Title = txtTitle.Text.Trim();
            _draft.Tags = txtTags.Text
                .Split(new[] { ',', '、' })
                .Select(t => t.Trim())
                .Where(t => t.Length > 0)
                .ToList();

            try
            {
                _draft = _repo.SaveNew(_draft, txtBody.Text);
                _saved = true;
                this.DialogResult = DialogResult.OK;
                Close();
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, "保存に失敗しました: " + ex.Message, "エラー",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void BtnCancel_Click(object sender, EventArgs e)
        {
            this.DialogResult = DialogResult.Cancel;
            Close();
        }

        private void NoteEditForm_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Control && e.KeyCode == Keys.L)
            {
                InsertNoteLinkAtCursor();
                e.Handled = true;
            }
        }

        private void InsertNoteLinkAtCursor()
        {
            if (_draft == null) return;
            using (var picker = new NotePickerDialog(_repo, _draft.Id))
            {
                if (picker.ShowDialog(this) == DialogResult.OK && picker.SelectedMeta != null)
                {
                    var m = picker.SelectedMeta;
                    string snippet;
                    if (string.IsNullOrEmpty(picker.SelectedAnchor))
                    {
                        snippet = "[" + (m.Title ?? "") + "](../" + m.Id + "/index.md)";
                    }
                    else
                    {
                        var display = (m.Title ?? "") + " > " + (picker.SelectedHeadingText ?? picker.SelectedAnchor);
                        snippet = "[" + display + "](../" + m.Id + "/index.md#" + picker.SelectedAnchor + ")";
                    }
                    InsertAtCursor(snippet);
                }
            }
        }

        private void NoteEditForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (!_saved && _draft != null)
            {
                try
                {
                    _repo.MoveToTrash(_draft.Id);
                }
                catch
                {
                    // クローズ中の例外は飲む
                }
            }
        }
    }
}
