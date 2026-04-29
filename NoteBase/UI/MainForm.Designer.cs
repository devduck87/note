namespace NoteBase.UI
{
    partial class MainForm
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
                components.Dispose();
            base.Dispose(disposing);
        }

        private System.Windows.Forms.ToolStrip toolStrip;
        private System.Windows.Forms.ToolStripButton btnBack;
        private System.Windows.Forms.ToolStripSeparator sep0;
        private System.Windows.Forms.ToolStripLabel lblSearch;
        private System.Windows.Forms.ToolStripTextBox txtSearch;
        private System.Windows.Forms.ToolStripSeparator sep1;
        private System.Windows.Forms.ToolStripButton btnNew;
        private System.Windows.Forms.ToolStripButton btnEdit;
        private System.Windows.Forms.ToolStripButton btnSave;
        private System.Windows.Forms.ToolStripButton btnCancel;

        private System.Windows.Forms.SplitContainer splitOuter;
        private System.Windows.Forms.SplitContainer splitInner;

        private System.Windows.Forms.ListView lvNotes;
        private System.Windows.Forms.ColumnHeader colTitle;
        private System.Windows.Forms.ColumnHeader colType;
        private System.Windows.Forms.ColumnHeader colUpdated;

        private System.Windows.Forms.WebBrowser webPreview;
        private NoteBase.UI.Controls.MarkdownTextBox txtBody;

        // プロパティパネル
        private System.Windows.Forms.Panel pnlProperty;
        private System.Windows.Forms.Label lblPropTitle;
        private System.Windows.Forms.TextBox txtPropTitle;
        private System.Windows.Forms.Label lblPropType;
        private System.Windows.Forms.ComboBox cmbPropType;
        private System.Windows.Forms.Label lblPropStatus;
        private System.Windows.Forms.ComboBox cmbPropStatus;
        private System.Windows.Forms.Label lblPropTags;
        private System.Windows.Forms.TextBox txtPropTags;
        private System.Windows.Forms.Label lblPropProject;
        private System.Windows.Forms.TextBox txtPropProject;
        private System.Windows.Forms.Label lblPropDue;
        private System.Windows.Forms.CheckBox chkPropDue;
        private System.Windows.Forms.DateTimePicker dtPropDue;
        private System.Windows.Forms.Label lblPropCreated;
        private System.Windows.Forms.Label lblPropCreatedValue;
        private System.Windows.Forms.Label lblPropUpdated;
        private System.Windows.Forms.Label lblPropUpdatedValue;
        private System.Windows.Forms.Label lblPropSchedule;
        private System.Windows.Forms.Label lblPropScheduleValue;
        private System.Windows.Forms.Label lblPropInstanceOf;
        private System.Windows.Forms.Label lblPropInstanceOfValue;

        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();

            this.toolStrip = new System.Windows.Forms.ToolStrip();
            this.btnBack = new System.Windows.Forms.ToolStripButton();
            this.sep0 = new System.Windows.Forms.ToolStripSeparator();
            this.lblSearch = new System.Windows.Forms.ToolStripLabel();
            this.txtSearch = new System.Windows.Forms.ToolStripTextBox();
            this.sep1 = new System.Windows.Forms.ToolStripSeparator();
            this.btnNew = new System.Windows.Forms.ToolStripButton();
            this.btnEdit = new System.Windows.Forms.ToolStripButton();
            this.btnSave = new System.Windows.Forms.ToolStripButton();
            this.btnCancel = new System.Windows.Forms.ToolStripButton();

            this.splitOuter = new System.Windows.Forms.SplitContainer();
            this.splitInner = new System.Windows.Forms.SplitContainer();

            this.lvNotes = new System.Windows.Forms.ListView();
            this.colTitle = new System.Windows.Forms.ColumnHeader();
            this.colType = new System.Windows.Forms.ColumnHeader();
            this.colUpdated = new System.Windows.Forms.ColumnHeader();

            this.webPreview = new System.Windows.Forms.WebBrowser();
            this.txtBody = new NoteBase.UI.Controls.MarkdownTextBox();

            this.pnlProperty = new System.Windows.Forms.Panel();
            this.lblPropTitle = new System.Windows.Forms.Label();
            this.txtPropTitle = new System.Windows.Forms.TextBox();
            this.lblPropType = new System.Windows.Forms.Label();
            this.cmbPropType = new System.Windows.Forms.ComboBox();
            this.lblPropStatus = new System.Windows.Forms.Label();
            this.cmbPropStatus = new System.Windows.Forms.ComboBox();
            this.lblPropTags = new System.Windows.Forms.Label();
            this.txtPropTags = new System.Windows.Forms.TextBox();
            this.lblPropProject = new System.Windows.Forms.Label();
            this.txtPropProject = new System.Windows.Forms.TextBox();
            this.lblPropDue = new System.Windows.Forms.Label();
            this.chkPropDue = new System.Windows.Forms.CheckBox();
            this.dtPropDue = new System.Windows.Forms.DateTimePicker();
            this.lblPropSchedule = new System.Windows.Forms.Label();
            this.lblPropScheduleValue = new System.Windows.Forms.Label();
            this.lblPropInstanceOf = new System.Windows.Forms.Label();
            this.lblPropInstanceOfValue = new System.Windows.Forms.Label();
            this.lblPropCreated = new System.Windows.Forms.Label();
            this.lblPropCreatedValue = new System.Windows.Forms.Label();
            this.lblPropUpdated = new System.Windows.Forms.Label();
            this.lblPropUpdatedValue = new System.Windows.Forms.Label();

            this.toolStrip.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.splitOuter)).BeginInit();
            this.splitOuter.Panel1.SuspendLayout();
            this.splitOuter.Panel2.SuspendLayout();
            this.splitOuter.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.splitInner)).BeginInit();
            this.splitInner.Panel1.SuspendLayout();
            this.splitInner.Panel2.SuspendLayout();
            this.splitInner.SuspendLayout();
            this.pnlProperty.SuspendLayout();
            this.SuspendLayout();

            // ---------------- toolStrip ----------------
            this.toolStrip.GripStyle = System.Windows.Forms.ToolStripGripStyle.Hidden;
            this.toolStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[]
            {
                this.btnBack, this.sep0,
                this.lblSearch, this.txtSearch, this.sep1,
                this.btnNew, this.btnEdit, this.btnSave, this.btnCancel
            });
            this.toolStrip.Location = new System.Drawing.Point(0, 0);
            this.toolStrip.Size = new System.Drawing.Size(1200, 25);

            this.btnBack.Text = "← 戻る (Alt+←)";
            this.btnBack.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
            this.btnBack.Enabled = false;
            this.btnBack.Click += new System.EventHandler(this.BtnBack_Click);

            this.lblSearch.Text = "検索:";

            this.txtSearch.Size = new System.Drawing.Size(220, 25);
            this.txtSearch.TextChanged += new System.EventHandler(this.TxtSearch_TextChanged);

            this.btnNew.Text = "新規ノート (Ctrl+N)";
            this.btnNew.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
            this.btnNew.Click += new System.EventHandler(this.BtnNew_Click);

            this.btnEdit.Text = "編集モード (Ctrl+E)";
            this.btnEdit.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
            this.btnEdit.Click += new System.EventHandler(this.BtnEdit_Click);

            this.btnSave.Text = "保存 (Ctrl+S)";
            this.btnSave.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
            this.btnSave.Visible = false;
            this.btnSave.Click += new System.EventHandler(this.BtnSave_Click);

            this.btnCancel.Text = "取消";
            this.btnCancel.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
            this.btnCancel.Visible = false;
            this.btnCancel.Click += new System.EventHandler(this.BtnCancel_Click);

            // ---------------- splitOuter (中央 | プロパティ) ----------------
            this.splitOuter.Dock = System.Windows.Forms.DockStyle.Fill;
            this.splitOuter.Location = new System.Drawing.Point(0, 25);
            this.splitOuter.Size = new System.Drawing.Size(1200, 575);
            this.splitOuter.SplitterDistance = 950;
            this.splitOuter.FixedPanel = System.Windows.Forms.FixedPanel.Panel2;
            this.splitOuter.Panel1.Controls.Add(this.splitInner);
            this.splitOuter.Panel2.Controls.Add(this.pnlProperty);

            // ---------------- splitInner (一覧 | 中央) ----------------
            this.splitInner.Dock = System.Windows.Forms.DockStyle.Fill;
            this.splitInner.SplitterDistance = 350;
            this.splitInner.Panel1.Controls.Add(this.lvNotes);
            this.splitInner.Panel2.Controls.Add(this.txtBody);
            this.splitInner.Panel2.Controls.Add(this.webPreview);

            // ---------------- lvNotes ----------------
            this.lvNotes.Dock = System.Windows.Forms.DockStyle.Fill;
            this.lvNotes.Columns.AddRange(new System.Windows.Forms.ColumnHeader[]
            {
                this.colTitle, this.colType, this.colUpdated
            });
            this.lvNotes.View = System.Windows.Forms.View.Details;
            this.lvNotes.FullRowSelect = true;
            this.lvNotes.HideSelection = false;
            this.lvNotes.MultiSelect = false;
            this.lvNotes.SelectedIndexChanged += new System.EventHandler(this.LvNotes_SelectedIndexChanged);

            this.colTitle.Text = "タイトル"; this.colTitle.Width = 200;
            this.colType.Text = "種別"; this.colType.Width = 80;
            this.colUpdated.Text = "更新日時"; this.colUpdated.Width = 130;

            // ---------------- webPreview ----------------
            this.webPreview.Dock = System.Windows.Forms.DockStyle.Fill;
            this.webPreview.MinimumSize = new System.Drawing.Size(20, 20);
            this.webPreview.AllowWebBrowserDrop = false;
            this.webPreview.IsWebBrowserContextMenuEnabled = false;
            this.webPreview.WebBrowserShortcutsEnabled = false;

            // ---------------- txtBody (MarkdownTextBox) ----------------
            this.txtBody.Dock = System.Windows.Forms.DockStyle.Fill;
            this.txtBody.Visible = false;
            this.txtBody.TextChanged += new System.EventHandler(this.TxtBody_TextChanged);

            // ---------------- pnlProperty ----------------
            this.pnlProperty.Dock = System.Windows.Forms.DockStyle.Fill;
            this.pnlProperty.AutoScroll = true;
            this.pnlProperty.Padding = new System.Windows.Forms.Padding(8);

            int y = 8;
            int labelW = 70;
            int ctrlX = labelW + 16;
            int ctrlW = 170;

            // タイトル
            this.lblPropTitle.Text = "タイトル:";
            this.lblPropTitle.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropTitle.Size = new System.Drawing.Size(labelW, 20);

            this.txtPropTitle.Location = new System.Drawing.Point(ctrlX, y);
            this.txtPropTitle.Size = new System.Drawing.Size(ctrlW, 22);
            this.txtPropTitle.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            this.txtPropTitle.TextChanged += new System.EventHandler(this.PropertyValueChanged);
            y += 30;

            // 種類
            this.lblPropType.Text = "種類:";
            this.lblPropType.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropType.Size = new System.Drawing.Size(labelW, 20);

            this.cmbPropType.Location = new System.Drawing.Point(ctrlX, y);
            this.cmbPropType.Size = new System.Drawing.Size(ctrlW, 22);
            this.cmbPropType.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbPropType.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            this.cmbPropType.SelectedIndexChanged += new System.EventHandler(this.PropertyValueChanged);
            y += 30;

            // ステータス
            this.lblPropStatus.Text = "ステータス:";
            this.lblPropStatus.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropStatus.Size = new System.Drawing.Size(labelW, 20);

            this.cmbPropStatus.Location = new System.Drawing.Point(ctrlX, y);
            this.cmbPropStatus.Size = new System.Drawing.Size(ctrlW, 22);
            this.cmbPropStatus.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbPropStatus.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            this.cmbPropStatus.SelectedIndexChanged += new System.EventHandler(this.PropertyValueChanged);
            y += 30;

            // タグ
            this.lblPropTags.Text = "タグ:";
            this.lblPropTags.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropTags.Size = new System.Drawing.Size(labelW, 20);

            this.txtPropTags.Location = new System.Drawing.Point(ctrlX, y);
            this.txtPropTags.Size = new System.Drawing.Size(ctrlW, 22);
            this.txtPropTags.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            this.txtPropTags.TextChanged += new System.EventHandler(this.PropertyValueChanged);
            y += 30;

            // プロジェクト
            this.lblPropProject.Text = "プロジェクト:";
            this.lblPropProject.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropProject.Size = new System.Drawing.Size(labelW, 20);

            this.txtPropProject.Location = new System.Drawing.Point(ctrlX, y);
            this.txtPropProject.Size = new System.Drawing.Size(ctrlW, 22);
            this.txtPropProject.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            this.txtPropProject.TextChanged += new System.EventHandler(this.PropertyValueChanged);
            y += 30;

            // 期限
            this.lblPropDue.Text = "期限:";
            this.lblPropDue.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropDue.Size = new System.Drawing.Size(labelW, 20);

            this.chkPropDue.Text = "設定";
            this.chkPropDue.Location = new System.Drawing.Point(ctrlX, y + 2);
            this.chkPropDue.Size = new System.Drawing.Size(50, 20);
            this.chkPropDue.CheckedChanged += new System.EventHandler(this.ChkPropDue_CheckedChanged);

            this.dtPropDue.Location = new System.Drawing.Point(ctrlX + 56, y);
            this.dtPropDue.Size = new System.Drawing.Size(ctrlW - 56, 22);
            this.dtPropDue.Format = System.Windows.Forms.DateTimePickerFormat.Short;
            this.dtPropDue.Enabled = false;
            this.dtPropDue.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            this.dtPropDue.ValueChanged += new System.EventHandler(this.PropertyValueChanged);
            y += 30;

            // schedule (read-only 表示)
            this.lblPropSchedule.Text = "schedule:";
            this.lblPropSchedule.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropSchedule.Size = new System.Drawing.Size(labelW, 20);

            this.lblPropScheduleValue.Location = new System.Drawing.Point(ctrlX, y + 3);
            this.lblPropScheduleValue.Size = new System.Drawing.Size(ctrlW, 20);
            this.lblPropScheduleValue.AutoSize = false;
            this.lblPropScheduleValue.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            y += 26;

            // instance_of (read-only 表示)
            this.lblPropInstanceOf.Text = "instance_of:";
            this.lblPropInstanceOf.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropInstanceOf.Size = new System.Drawing.Size(labelW, 20);

            this.lblPropInstanceOfValue.Location = new System.Drawing.Point(ctrlX, y + 3);
            this.lblPropInstanceOfValue.Size = new System.Drawing.Size(ctrlW, 20);
            this.lblPropInstanceOfValue.AutoSize = false;
            this.lblPropInstanceOfValue.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            y += 26;

            // 作成日
            this.lblPropCreated.Text = "作成:";
            this.lblPropCreated.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropCreated.Size = new System.Drawing.Size(labelW, 20);

            this.lblPropCreatedValue.Location = new System.Drawing.Point(ctrlX, y + 3);
            this.lblPropCreatedValue.Size = new System.Drawing.Size(ctrlW, 20);
            this.lblPropCreatedValue.AutoSize = false;
            this.lblPropCreatedValue.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            y += 26;

            // 更新日
            this.lblPropUpdated.Text = "更新:";
            this.lblPropUpdated.Location = new System.Drawing.Point(8, y + 3);
            this.lblPropUpdated.Size = new System.Drawing.Size(labelW, 20);

            this.lblPropUpdatedValue.Location = new System.Drawing.Point(ctrlX, y + 3);
            this.lblPropUpdatedValue.Size = new System.Drawing.Size(ctrlW, 20);
            this.lblPropUpdatedValue.AutoSize = false;
            this.lblPropUpdatedValue.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;

            this.pnlProperty.Controls.Add(this.lblPropTitle);
            this.pnlProperty.Controls.Add(this.txtPropTitle);
            this.pnlProperty.Controls.Add(this.lblPropType);
            this.pnlProperty.Controls.Add(this.cmbPropType);
            this.pnlProperty.Controls.Add(this.lblPropStatus);
            this.pnlProperty.Controls.Add(this.cmbPropStatus);
            this.pnlProperty.Controls.Add(this.lblPropTags);
            this.pnlProperty.Controls.Add(this.txtPropTags);
            this.pnlProperty.Controls.Add(this.lblPropProject);
            this.pnlProperty.Controls.Add(this.txtPropProject);
            this.pnlProperty.Controls.Add(this.lblPropDue);
            this.pnlProperty.Controls.Add(this.chkPropDue);
            this.pnlProperty.Controls.Add(this.dtPropDue);
            this.pnlProperty.Controls.Add(this.lblPropSchedule);
            this.pnlProperty.Controls.Add(this.lblPropScheduleValue);
            this.pnlProperty.Controls.Add(this.lblPropInstanceOf);
            this.pnlProperty.Controls.Add(this.lblPropInstanceOfValue);
            this.pnlProperty.Controls.Add(this.lblPropCreated);
            this.pnlProperty.Controls.Add(this.lblPropCreatedValue);
            this.pnlProperty.Controls.Add(this.lblPropUpdated);
            this.pnlProperty.Controls.Add(this.lblPropUpdatedValue);

            // ---------------- MainForm ----------------
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1200, 600);
            this.Controls.Add(this.splitOuter);
            this.Controls.Add(this.toolStrip);
            this.KeyPreview = true;
            this.Text = "NoteBase";
            this.KeyDown += new System.Windows.Forms.KeyEventHandler(this.MainForm_KeyDown);
            this.Load += new System.EventHandler(this.MainForm_Load);
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.MainForm_FormClosing);

            this.toolStrip.ResumeLayout(false);
            this.toolStrip.PerformLayout();
            this.splitInner.Panel1.ResumeLayout(false);
            this.splitInner.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)(this.splitInner)).EndInit();
            this.splitInner.ResumeLayout(false);
            this.splitOuter.Panel1.ResumeLayout(false);
            this.splitOuter.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)(this.splitOuter)).EndInit();
            this.splitOuter.ResumeLayout(false);
            this.pnlProperty.ResumeLayout(false);
            this.pnlProperty.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();
        }
    }
}
