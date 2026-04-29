using System;
using System.Collections.Generic;
using System.Diagnostics;
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
    /// メイン画面: ノート一覧 + プレビュー / 編集 + プロパティパネル。
    /// </summary>
    public partial class MainForm : Form
    {
        private readonly AppPaths _paths;
        private readonly NoteRepository _repo;
        private readonly TrashService _trash;

        private string _currentNoteId;
        private NoteMeta _currentMeta;
        private bool _editMode;
        private bool _dirty;
        private bool _suspendDirty;
        private Dictionary<string, string> _titleToIdCache;
        private Dictionary<string, string> _summaryCache;
        private readonly string _previewTempPath;
        private static readonly UTF8Encoding Utf8NoBom = new UTF8Encoding(false);
        private readonly Stack<string> _navHistory = new Stack<string>();
        private bool _navigatingBack;

        public MainForm()
        {
            InitializeComponent();

            _paths = AppPaths.Default();
            _paths.EnsureLayout();
            _trash = new TrashService(_paths);
            _repo = new NoteRepository(_paths, _trash);
            _previewTempPath = Path.Combine(Path.GetTempPath(), "notebase_preview.html");

            InitPropertyControls();

            webPreview.Navigating += WebPreview_Navigating;
        }

        private void InitPropertyControls()
        {
            cmbPropType.Items.AddRange(new object[]
            {
                NoteType.Memo, NoteType.Procedure, NoteType.Todo,
                NoteType.Routine, NoteType.Checklist, NoteType.Daily,
                NoteType.Project, NoteType.Log,
            });
            cmbPropType.Format += (s, e) =>
            {
                if (e.ListItem is NoteType)
                    e.Value = ((NoteType)e.ListItem).DisplayName();
            };

            cmbPropStatus.Items.AddRange(new object[]
            {
                "(なし)", NoteStatus.Active, NoteStatus.Done,
                NoteStatus.Pending, NoteStatus.Archived,
            });
            cmbPropStatus.Format += (s, e) =>
            {
                if (e.ListItem is NoteStatus)
                    e.Value = ((NoteStatus)e.ListItem).ToWireString();
            };

            SetPropertyEditable(false);
        }

        private void MainForm_Load(object sender, EventArgs e)
        {
            RefreshNoteList();
        }

        // ============================================================
        // ノート一覧 / 検索
        // ============================================================

        private void RefreshNoteList()
        {
            _titleToIdCache = null; // 一覧更新時に各キャッシュを無効化
            _summaryCache = null;
            var prevSelectedId = _currentNoteId;

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

                    if (meta.Id == prevSelectedId)
                        item.Selected = true;
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
            if (lvNotes.SelectedItems.Count == 0) return;
            var newId = (string)lvNotes.SelectedItems[0].Tag;
            if (newId == _currentNoteId) return;

            if (!ConfirmDiscardIfDirty()) return;

            LoadNote(newId);
        }

        // ============================================================
        // ノート読み込み・表示
        // ============================================================

        private void LoadNote(string id)
        {
            try
            {
                // 戻る用に直前のノートを履歴へ積む（戻る操作時は積まない）
                if (!_navigatingBack
                    && !string.IsNullOrEmpty(_currentNoteId)
                    && _currentNoteId != id)
                {
                    _navHistory.Push(_currentNoteId);
                }

                string body;
                _currentMeta = _repo.Load(id, out body);
                _currentNoteId = id;

                // プロパティパネルへ反映
                _suspendDirty = true;
                try
                {
                    PopulateProperties(_currentMeta);
                    // TextBox は \r\n でないと改行表示されないため正規化する
                    txtBody.Text = NormalizeForTextBox(body);
                    txtBody.NoteDir = _paths.NoteDir(id);
                }
                finally { _suspendDirty = false; }

                _dirty = false;

                // 表示モードを反映
                if (_editMode) ShowEditCenter();
                else ShowPreviewCenter(id, body);

                UpdateToolStripState();
                UpdateBackButtonState();
            }
            catch (Exception ex)
            {
                ShowErrorInPreview("読み込みエラー: " + ex.Message);
            }
        }

        private void PopulateProperties(NoteMeta m)
        {
            txtPropTitle.Text = m.Title ?? "";
            cmbPropType.SelectedItem = m.Type;
            if (m.Status.HasValue)
                cmbPropStatus.SelectedItem = m.Status.Value;
            else
                cmbPropStatus.SelectedIndex = 0;

            txtPropTags.Text = m.Tags == null ? "" : string.Join(", ", m.Tags);
            txtPropProject.Text = m.Project ?? "";

            chkPropDue.Checked = m.Due.HasValue;
            dtPropDue.Enabled = m.Due.HasValue;
            if (m.Due.HasValue) dtPropDue.Value = m.Due.Value;

            lblPropScheduleValue.Text = FormatSchedule(m.Schedule);
            lblPropInstanceOfValue.Text = m.InstanceOf ?? "";
            lblPropCreatedValue.Text = m.Created.ToString("yyyy-MM-dd HH:mm:ss");
            lblPropUpdatedValue.Text = m.Updated.ToString("yyyy-MM-dd HH:mm:ss");
        }

        private static string NormalizeForTextBox(string s)
        {
            if (string.IsNullOrEmpty(s)) return s ?? "";
            return s.Replace("\r\n", "\n").Replace("\r", "\n").Replace("\n", "\r\n");
        }

        private static string FormatSchedule(Schedule s)
        {
            if (s == null) return "";
            var parts = new List<string> { s.Frequency.ToWireString() };
            if (s.Days != null && s.Days.Count > 0)
                parts.Add("days=[" + string.Join(",", s.Days) + "]");
            if (s.DayOfMonth.HasValue)
                parts.Add("dom=" + s.DayOfMonth.Value);
            parts.Add(s.Enabled ? "enabled" : "disabled");
            return string.Join(" ", parts);
        }

        private void ShowPreviewCenter(string id, string body)
        {
            txtBody.Visible = false;
            webPreview.Visible = true;

            var noteDir = _paths.NoteDir(id);
            var baseUrl = "file:///" + noteDir.Replace('\\', '/').TrimEnd('/') + "/";
            var html = MarkdownToHtml.Convert(body, ResolveTitleToId, baseUrl, ResolveNoteSummary);

            var doc = "<!DOCTYPE html><html><head>"
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
                + ".unresolved-link{color:#c00;}"
                + "a{color:#0a58ca;}"
                + "</style></head><body>"
                + html
                + "</body></html>";

            // DocumentText (about:blank) からの file:// リンクは
            // IE のセキュリティ制約で遷移できないため、
            // 一時ファイル経由で Navigate して URL を file:// にする。
            File.WriteAllText(_previewTempPath, doc, Utf8NoBom);
            webPreview.Navigate(_previewTempPath);
        }

        /// <summary>
        /// [[Title]] の解決用。title から ID を返す。一致なしは null。
        /// </summary>
        private string ResolveTitleToId(string title)
        {
            if (string.IsNullOrEmpty(title)) return null;
            if (_titleToIdCache == null) BuildTitleToIdCache();
            string id;
            return _titleToIdCache.TryGetValue(title, out id) ? id : null;
        }

        private void BuildTitleToIdCache()
        {
            _titleToIdCache = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (var m in _repo.LoadAll())
            {
                if (string.IsNullOrEmpty(m.Title)) continue;
                if (_titleToIdCache.ContainsKey(m.Title)) continue; // 重複は最初に見つけた方を採用
                _titleToIdCache[m.Title] = m.Id;
            }
        }

        /// <summary>
        /// ノート ID → 本文要約。リンクのホバーツールチップ表示に使う。
        /// 必要時に index.md を読み込んで要約を抽出し、キャッシュする。
        /// </summary>
        private string ResolveNoteSummary(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            if (_summaryCache == null)
                _summaryCache = new Dictionary<string, string>(StringComparer.Ordinal);

            string cached;
            if (_summaryCache.TryGetValue(id, out cached)) return cached;

            string result = "";
            try
            {
                var path = _paths.IndexMdPath(id);
                if (File.Exists(path))
                {
                    var body = File.ReadAllText(path, Utf8NoBom);
                    result = MarkdownSummary.Extract(body, 200);
                }
            }
            catch
            {
                result = "";
            }
            _summaryCache[id] = result;
            return result;
        }

        private void ShowEditCenter()
        {
            webPreview.Visible = false;
            txtBody.Visible = true;
            txtBody.Focus();
        }

        private void ShowErrorInPreview(string msg)
        {
            webPreview.Visible = true;
            txtBody.Visible = false;
            var safe = (msg ?? "").Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;");
            webPreview.DocumentText = "<html><body><pre>" + safe + "</pre></body></html>";
        }

        // ============================================================
        // 編集モード切替・保存
        // ============================================================

        private void BtnEdit_Click(object sender, EventArgs e)
        {
            if (_currentMeta == null) return;
            EnterEditMode();
        }

        private void EnterEditMode()
        {
            _editMode = true;
            SetPropertyEditable(true);
            ShowEditCenter();
            UpdateToolStripState();
        }

        private void ExitEditMode()
        {
            _editMode = false;
            SetPropertyEditable(false);
            // 表示はプレビューに戻す
            if (_currentMeta != null)
            {
                ShowPreviewCenter(_currentNoteId, txtBody.Text);
            }
            UpdateToolStripState();
        }

        private void SetPropertyEditable(bool editable)
        {
            txtPropTitle.ReadOnly = !editable;
            cmbPropType.Enabled = editable;
            cmbPropStatus.Enabled = editable;
            txtPropTags.ReadOnly = !editable;
            txtPropProject.ReadOnly = !editable;
            chkPropDue.Enabled = editable;
            dtPropDue.Enabled = editable && chkPropDue.Checked;
        }

        private void UpdateToolStripState()
        {
            btnEdit.Visible = !_editMode;
            btnSave.Visible = _editMode;
            btnCancel.Visible = _editMode;
            btnSave.Text = _dirty ? "保存* (Ctrl+S)" : "保存 (Ctrl+S)";
        }

        private void UpdateBackButtonState()
        {
            btnBack.Enabled = _navHistory.Count > 0;
        }

        // ============================================================
        // 戻るナビゲーション
        // ============================================================

        private void BtnBack_Click(object sender, EventArgs e)
        {
            NavigateBack();
        }

        private void NavigateBack()
        {
            if (_navHistory.Count == 0) return;
            if (!ConfirmDiscardIfDirty()) return;

            // 削除済みのノートはスキップして次の有効な ID を探す
            string prevId = null;
            while (_navHistory.Count > 0)
            {
                var candidate = _navHistory.Pop();
                if (Directory.Exists(_paths.NoteDir(candidate)))
                {
                    prevId = candidate;
                    break;
                }
            }
            if (prevId == null)
            {
                UpdateBackButtonState();
                return;
            }

            _navigatingBack = true;
            try
            {
                _editMode = false;
                UpdateToolStripState();
                foreach (ListViewItem item in lvNotes.Items)
                {
                    if ((string)item.Tag == prevId)
                    {
                        item.Selected = true;
                        item.EnsureVisible();
                        break;
                    }
                }
                LoadNote(prevId);
            }
            finally
            {
                _navigatingBack = false;
            }
            UpdateBackButtonState();
        }

        private void BtnSave_Click(object sender, EventArgs e)
        {
            if (_currentMeta == null) return;
            if (string.IsNullOrWhiteSpace(txtPropTitle.Text))
            {
                MessageBox.Show(this, "タイトルを入力してください。", "確認",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                txtPropTitle.Focus();
                return;
            }

            ApplyPropertiesToMeta(_currentMeta);

            try
            {
                _currentMeta = _repo.SaveExisting(_currentMeta, txtBody.Text);
                _dirty = false;
                ExitEditMode();
                RefreshNoteList();
                LoadNote(_currentMeta.Id); // updated 等を再反映
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, "保存に失敗しました: " + ex.Message, "エラー",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void BtnCancel_Click(object sender, EventArgs e)
        {
            if (!ConfirmDiscardIfDirty()) return;
            // 元の内容を再読み込み
            if (_currentNoteId != null)
            {
                _editMode = false;
                LoadNote(_currentNoteId);
            }
            UpdateToolStripState();
        }

        private void ApplyPropertiesToMeta(NoteMeta m)
        {
            m.Title = txtPropTitle.Text.Trim();
            if (cmbPropType.SelectedItem is NoteType)
                m.Type = (NoteType)cmbPropType.SelectedItem;

            if (cmbPropStatus.SelectedItem is NoteStatus)
                m.Status = (NoteStatus)cmbPropStatus.SelectedItem;
            else
                m.Status = null;

            m.Tags = (txtPropTags.Text ?? "")
                .Split(new[] { ',', '、' })
                .Select(t => t.Trim())
                .Where(t => t.Length > 0)
                .ToList();

            var proj = (txtPropProject.Text ?? "").Trim();
            m.Project = string.IsNullOrEmpty(proj) ? null : proj;

            m.Due = chkPropDue.Checked ? (DateTime?)dtPropDue.Value.Date : null;
        }

        // ============================================================
        // dirty 追跡
        // ============================================================

        private void TxtBody_TextChanged(object sender, EventArgs e)
        {
            MarkDirty();
        }

        private void PropertyValueChanged(object sender, EventArgs e)
        {
            MarkDirty();
        }

        private void ChkPropDue_CheckedChanged(object sender, EventArgs e)
        {
            dtPropDue.Enabled = _editMode && chkPropDue.Checked;
            MarkDirty();
        }

        private void MarkDirty()
        {
            if (_suspendDirty) return;
            if (!_editMode) return;
            _dirty = true;
            UpdateToolStripState();
        }

        private bool ConfirmDiscardIfDirty()
        {
            if (!_dirty) return true;
            var r = MessageBox.Show(this,
                "未保存の変更があります。破棄しますか？",
                "確認", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (r == DialogResult.Yes)
            {
                _dirty = false;
                _editMode = false;
                return true;
            }
            return false;
        }

        // ============================================================
        // 新規作成
        // ============================================================

        private void BtnNew_Click(object sender, EventArgs e)
        {
            if (!ConfirmDiscardIfDirty()) return;
            using (var form = new NoteEditForm(_repo))
            {
                if (form.ShowDialog(this) == DialogResult.OK)
                {
                    RefreshNoteList();
                }
            }
        }

        // ============================================================
        // フォームレベルイベント
        // ============================================================

        private void MainForm_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Control && e.KeyCode == Keys.N)
            {
                BtnNew_Click(this, EventArgs.Empty);
                e.Handled = true;
            }
            else if (e.Control && e.KeyCode == Keys.E)
            {
                if (!_editMode && _currentMeta != null)
                {
                    EnterEditMode();
                    e.Handled = true;
                }
            }
            else if (e.Control && e.KeyCode == Keys.S)
            {
                if (_editMode)
                {
                    BtnSave_Click(this, EventArgs.Empty);
                    e.Handled = true;
                }
            }
            else if (e.Control && e.KeyCode == Keys.L)
            {
                if (_editMode)
                {
                    InsertNoteLinkAtCursor();
                    e.Handled = true;
                }
            }
            else if (e.Alt && e.KeyCode == Keys.Left)
            {
                NavigateBack();
                e.Handled = true;
            }
        }

        // ============================================================
        // ノートリンク挿入 (Ctrl+L)
        // ============================================================

        private void InsertNoteLinkAtCursor()
        {
            using (var picker = new NotePickerDialog(_repo, _currentNoteId))
            {
                if (picker.ShowDialog(this) == DialogResult.OK && picker.SelectedMeta != null)
                {
                    var m = picker.SelectedMeta;
                    var snippet = "[" + (m.Title ?? "") + "](../" + m.Id + "/index.md)";
                    int pos = txtBody.SelectionStart;
                    txtBody.Text = txtBody.Text.Insert(pos, snippet);
                    txtBody.SelectionStart = pos + snippet.Length;
                    txtBody.SelectionLength = 0;
                    txtBody.Focus();
                }
            }
        }

        // ============================================================
        // プレビューのリンクナビゲーション
        // ============================================================

        private void WebPreview_Navigating(object sender, WebBrowserNavigatingEventArgs e)
        {
            var uri = e.Url;
            if (uri == null) return;

            var url = uri.AbsoluteUri ?? "";
            // 初期 / 自前プレビューファイルへの Navigate は素通し
            if (url == "about:blank" || string.IsNullOrEmpty(url)) return;
            if (uri.IsFile && !string.IsNullOrEmpty(_previewTempPath)
                && string.Equals(uri.LocalPath, _previewTempPath, StringComparison.OrdinalIgnoreCase))
                return;

            if (uri.IsFile)
            {
                var path = uri.LocalPath;
                // .md なら他ノートに遷移
                if (path != null && path.EndsWith(".md", StringComparison.OrdinalIgnoreCase))
                {
                    e.Cancel = true;
                    var dir = Path.GetDirectoryName(path);
                    if (!string.IsNullOrEmpty(dir))
                    {
                        var id = Path.GetFileName(dir);
                        // UI スレッドへ非同期投入 (Navigating ハンドラ内で再ナビゲーションすると詰まる)
                        BeginInvoke((Action)(() => OpenNoteFromLink(id)));
                    }
                    return;
                }
                // それ以外 (画像など) は素通し
                return;
            }

            if (uri.Scheme == "http" || uri.Scheme == "https")
            {
                e.Cancel = true;
                try { Process.Start(url); } catch { /* ignore */ }
                return;
            }

            // それ以外のスキームはブロック
            e.Cancel = true;
        }

        private void OpenNoteFromLink(string id)
        {
            if (string.IsNullOrEmpty(id)) return;
            // 該当ノートが存在するか確認
            if (!Directory.Exists(_paths.NoteDir(id)))
            {
                MessageBox.Show(this, "リンク先のノートが見つかりません: " + id,
                    "情報", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            if (!ConfirmDiscardIfDirty()) return;
            _editMode = false;
            UpdateToolStripState();
            // 一覧の選択も同期
            foreach (ListViewItem item in lvNotes.Items)
            {
                if ((string)item.Tag == id)
                {
                    item.Selected = true;
                    item.EnsureVisible();
                    break;
                }
            }
            LoadNote(id);
        }

        private void MainForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (_dirty && !ConfirmDiscardIfDirty())
                e.Cancel = true;
        }
    }
}
