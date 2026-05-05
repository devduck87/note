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
        // 同じファイル URL への Navigate はフラグメントのみ変化だと再読み込みが起きないため、
        // クエリ文字列でキャッシュバスターを付けて URL 自体を変える。
        private int _previewVersion;
        private string _previewBaseUrl;
        private static readonly UTF8Encoding Utf8NoBom = new UTF8Encoding(false);
        private readonly Stack<string> _navHistory = new Stack<string>();
        private bool _navigatingBack;

        // ホバープレビュー
        private NotePreviewPopup _hoverPopup;
        private Timer _hoverShowTimer;
        private Timer _hoverHideTimer;
        private string _hoveredNoteId;
        private string _hoveredAnchor;
        private const int HoverShowDelayMs = 500;
        private const int HoverHideDelayMs = 250;

        // 別ノート遷移後に該当アンカー位置までスクロールするための保留 ID
        private string _pendingAnchor;

        public MainForm()
        {
            InitializeComponent();

            _paths = AppPaths.Default();
            _paths.EnsureLayout();
            _trash = new TrashService(_paths);
            _repo = new NoteRepository(_paths, _trash);
            _previewTempPath = Path.Combine(Path.GetTempPath(), "notebase_preview.html");

            InitPropertyControls();
            InitHoverPopup();

            webPreview.Navigating += WebPreview_Navigating;
            webPreview.DocumentCompleted += WebPreview_DocumentCompleted;
        }

        private void InitHoverPopup()
        {
            _hoverPopup = new NotePreviewPopup();
            _hoverShowTimer = new Timer { Interval = HoverShowDelayMs };
            _hoverShowTimer.Tick += HoverShowTimer_Tick;
            _hoverHideTimer = new Timer { Interval = HoverHideDelayMs };
            _hoverHideTimer.Tick += HoverHideTimer_Tick;
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

            // ベース URL を毎回変えないと、フラグメントだけ違う Navigate と判定されて
            // ドキュメントが再読み込みされず、書き換え前の内容が表示されたままになる。
            _previewVersion++;
            _previewBaseUrl = new Uri(_previewTempPath).AbsoluteUri + "?v=" + _previewVersion;

            // _pendingAnchor があれば URL フラグメントに含めてブラウザに自動スクロールさせる。
            // (GetElementById/ScrollIntoView より確実)
            string navigateUrl = _previewBaseUrl;
            if (!string.IsNullOrEmpty(_pendingAnchor))
            {
                navigateUrl += "#" + Uri.EscapeDataString(_pendingAnchor);
            }
            webPreview.Navigate(navigateUrl);
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
                LoadNote(prevId);
                foreach (ListViewItem item in lvNotes.Items)
                {
                    if ((string)item.Tag == prevId)
                    {
                        item.Selected = true;
                        item.EnsureVisible();
                        break;
                    }
                }
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
                if (picker.ShowDialog(this) != DialogResult.OK || picker.SelectedMeta == null)
                    return;

                var snippet = BuildLinkSnippetFromPicker(picker);
                if (string.IsNullOrEmpty(snippet)) return;

                int pos = txtBody.SelectionStart;
                txtBody.Text = txtBody.Text.Insert(pos, snippet);
                txtBody.SelectionStart = pos + snippet.Length;
                txtBody.SelectionLength = 0;
                txtBody.Focus();

                // 対象ノートが書き換わった可能性があるのでキャッシュ無効化
                _summaryCache = null;
                _titleToIdCache = null;
            }
        }

        /// <summary>
        /// ピッカーで選択された対象から、本文に挿入する Markdown スニペットを生成する。
        /// 段落／リスト項目の場合は EnsureBlockId で ^id を確保する (必要なら対象ノートを書き換える)。
        /// </summary>
        private string BuildLinkSnippetFromPicker(NotePickerDialog picker)
        {
            var m = picker.SelectedMeta;
            var title = m.Title ?? "";

            // ノート全体
            if (string.IsNullOrEmpty(picker.SelectedAnchor)
                && picker.SelectedBlockKind == null)
            {
                return "[" + title + "](../" + m.Id + "/index.md)";
            }

            // 見出し
            if (picker.SelectedBlockKind == BlockKind.Heading)
            {
                var display = title + " > " + (picker.SelectedHeadingText ?? picker.SelectedAnchor);
                return "[" + display + "](../" + m.Id + "/index.md#" + picker.SelectedAnchor + ")";
            }

            // 段落 / リスト項目: ^id を確保
            string anchor = picker.SelectedAnchor; // 既存があればそれ
            if (string.IsNullOrEmpty(anchor) && picker.SelectedBlockLineEnd >= 0)
            {
                try
                {
                    anchor = _repo.EnsureBlockId(m.Id, picker.SelectedBlockLineEnd);
                }
                catch (Exception ex)
                {
                    MessageBox.Show(this, "ブロック ID の付与に失敗しました: " + ex.Message,
                        "エラー", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return null;
                }
            }
            if (string.IsNullOrEmpty(anchor))
            {
                // 失敗 → ノート全体リンクにフォールバック
                return "[" + title + "](../" + m.Id + "/index.md)";
            }

            // 表示テキスト: ブロックの先頭抜粋を alias として使う
            var snippetText = picker.SelectedHeadingText ?? "";
            if (snippetText.Length > 60) snippetText = snippetText.Substring(0, 60) + "…";
            var displayBlock = title + " > " + snippetText;
            return "[" + displayBlock + "](../" + m.Id + "/index.md#" + anchor + ")";
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
                // 念のため: 万一 path 内に '#' が混入していたら除去
                if (path != null)
                {
                    var hashIdx = path.IndexOf('#');
                    if (hashIdx >= 0) path = path.Substring(0, hashIdx);
                }
                // .md なら他ノートに遷移
                if (path != null && path.EndsWith(".md", StringComparison.OrdinalIgnoreCase))
                {
                    e.Cancel = true;
                    var dir = Path.GetDirectoryName(path);
                    if (!string.IsNullOrEmpty(dir))
                    {
                        var id = Path.GetFileName(dir);
                        var anchor = uri.Fragment ?? "";
                        if (anchor.StartsWith("#")) anchor = anchor.Substring(1);
                        if (!string.IsNullOrEmpty(anchor))
                        {
                            try { anchor = Uri.UnescapeDataString(anchor); }
                            catch { /* デコード失敗は raw のまま */ }
                        }
                        BeginInvoke((Action)(() => OpenNoteFromLink(id, anchor)));
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

        private void OpenNoteFromLink(string id, string anchor)
        {
            if (string.IsNullOrEmpty(id)) return;
            // 該当ノートが存在するか確認
            if (!Directory.Exists(_paths.NoteDir(id)))
            {
                MessageBox.Show(this, "リンク先のノートが見つかりません: " + id,
                    "情報", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            // 同じノート内のアンカーリンクは現在のドキュメントでスクロールするだけ
            if (id == _currentNoteId)
            {
                ScrollToAnchor(anchor);
                return;
            }

            if (!ConfirmDiscardIfDirty()) return;
            _editMode = false;
            _pendingAnchor = string.IsNullOrEmpty(anchor) ? null : anchor;
            UpdateToolStripState();
            // LoadNote を先に呼んで _currentNoteId を更新する。
            // その後で一覧の選択を同期すると、SelectedIndexChanged は newId == _currentNoteId で抜けるため
            // 二重ロードによる _pendingAnchor の消失を防げる。
            LoadNote(id);
            foreach (ListViewItem item in lvNotes.Items)
            {
                if ((string)item.Tag == id)
                {
                    item.Selected = true;
                    item.EnsureVisible();
                    break;
                }
            }
        }

        private void ScrollToAnchor(string anchor)
        {
            if (string.IsNullOrEmpty(anchor)) return;
            try
            {
                // URL フラグメントを変えて Navigate するとブラウザが自動でスクロールする
                // (ベース URL が同じ = file 内容も同じ なので reload は走らずスクロールだけ)
                var baseUrl = _previewBaseUrl ?? new Uri(_previewTempPath).AbsoluteUri;
                webPreview.Navigate(baseUrl + "#" + Uri.EscapeDataString(anchor));
            }
            catch
            {
                // フォールバック: GetElementById/ScrollIntoView
                try
                {
                    if (webPreview.Document != null)
                    {
                        var elem = webPreview.Document.GetElementById(anchor);
                        if (elem != null) elem.ScrollIntoView(true);
                    }
                }
                catch { /* スクロール失敗は無視 */ }
            }
        }

        private void MainForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (_dirty && !ConfirmDiscardIfDirty())
                e.Cancel = true;
        }

        // ============================================================
        // リンクのホバープレビュー (B)
        // ============================================================

        private void WebPreview_DocumentCompleted(object sender, WebBrowserDocumentCompletedEventArgs e)
        {
            // ドキュメントが切り替わったら hover 関連のリスナを張り直す
            if (webPreview.Document != null)
            {
                webPreview.Document.MouseMove -= Document_MouseMove;
                webPreview.Document.MouseMove += Document_MouseMove;
            }

            // 直前の遷移にアンカーが指定されていたらその位置までスクロール
            if (!string.IsNullOrEmpty(_pendingAnchor))
            {
                var anchor = _pendingAnchor;
                _pendingAnchor = null;
                ScrollToAnchor(anchor);
            }
        }

        private void Document_MouseMove(object sender, HtmlElementEventArgs e)
        {
            var elem = webPreview.Document != null
                ? webPreview.Document.GetElementFromPoint(e.MousePosition) : null;
            // 親方向にたどって <a> を探す
            while (elem != null && !string.Equals(elem.TagName, "A", StringComparison.OrdinalIgnoreCase))
                elem = elem.Parent;

            if (elem != null)
            {
                var href = elem.GetAttribute("href");
                var id = ExtractNoteIdFromHref(href);
                var anchor = ExtractAnchorFromHref(href);
                if (!string.IsNullOrEmpty(id) && id != _currentNoteId)
                {
                    // 自ノート以外のノートリンク上をホバー中
                    _hoverHideTimer.Stop();
                    if (id != _hoveredNoteId || anchor != _hoveredAnchor)
                    {
                        _hoveredNoteId = id;
                        _hoveredAnchor = anchor;
                        if (_hoverPopup.Visible)
                        {
                            // 既に表示中なら即座に内容を差し替える
                            ShowHoverPopupFor(id, anchor);
                        }
                        else
                        {
                            _hoverShowTimer.Stop();
                            _hoverShowTimer.Start();
                        }
                    }
                    return;
                }
            }

            // ノートリンク上ではない
            _hoverShowTimer.Stop();
            _hoveredNoteId = null;
            _hoveredAnchor = null;
            if (_hoverPopup.Visible)
            {
                _hoverHideTimer.Stop();
                _hoverHideTimer.Start();
            }
        }

        private void HoverShowTimer_Tick(object sender, EventArgs e)
        {
            _hoverShowTimer.Stop();
            if (string.IsNullOrEmpty(_hoveredNoteId)) return;
            ShowHoverPopupFor(_hoveredNoteId, _hoveredAnchor);
        }

        private void HoverHideTimer_Tick(object sender, EventArgs e)
        {
            _hoverHideTimer.Stop();
            if (!_hoverPopup.Visible) return;
            // カーソルがポップアップの上にあれば閉じない
            if (_hoverPopup.Bounds.Contains(Cursor.Position))
            {
                _hoverHideTimer.Start();
                return;
            }
            _hoverPopup.Hide();
        }

        private void ShowHoverPopupFor(string id, string anchor)
        {
            if (!Directory.Exists(_paths.NoteDir(id))) return;

            try
            {
                string body;
                _repo.Load(id, out body);
                // アンカーが指定されていれば該当セクション / ブロックだけに絞る
                var contentBody = string.IsNullOrEmpty(anchor)
                    ? body : MarkdownIndex.ExtractSection(body, anchor);
                var noteDir = _paths.NoteDir(id);
                var baseUrl = "file:///" + noteDir.Replace('\\', '/').TrimEnd('/') + "/";
                var html = MarkdownToHtml.Convert(contentBody, ResolveTitleToId, baseUrl, ResolveNoteSummary);
                // セクション抽出後はアンカーが先頭に来ているのでスクロール不要だが、
                // 抽出が一致せず全文フォールバックされた場合に備えて anchor は渡しておく。
                _hoverPopup.SetContent(id, html, anchor);

                if (!_hoverPopup.Visible)
                {
                    var pos = Cursor.Position;
                    pos.Offset(16, 16);
                    // 画面端で見切れないように調整
                    var screen = Screen.FromPoint(pos).WorkingArea;
                    if (pos.X + _hoverPopup.Width > screen.Right)
                        pos.X = screen.Right - _hoverPopup.Width;
                    if (pos.Y + _hoverPopup.Height > screen.Bottom)
                        pos.Y = screen.Bottom - _hoverPopup.Height;
                    _hoverPopup.Location = pos;
                    _hoverPopup.Show(this);
                }
            }
            catch
            {
                // ホバー失敗は静かに無視
            }
        }

        private static string ExtractNoteIdFromHref(string href)
        {
            if (string.IsNullOrEmpty(href)) return null;
            // file:// 絶対 / 相対両対応で /<id>/index.md パターンを抜き出す
            var lower = href.ToLowerInvariant();
            var idx = lower.LastIndexOf("/index.md");
            if (idx < 0) return null;
            var head = href.Substring(0, idx);
            var slash = head.LastIndexOf('/');
            if (slash < 0) return null;
            return head.Substring(slash + 1);
        }

        private static string ExtractAnchorFromHref(string href)
        {
            if (string.IsNullOrEmpty(href)) return null;
            var idx = href.IndexOf('#');
            if (idx < 0) return null;
            var anchor = href.Substring(idx + 1);
            if (string.IsNullOrEmpty(anchor)) return null;
            try { return Uri.UnescapeDataString(anchor); }
            catch { return anchor; }
        }
    }
}
