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
        private System.Windows.Forms.ToolStripLabel lblSearch;
        private System.Windows.Forms.ToolStripTextBox txtSearch;
        private System.Windows.Forms.ToolStripButton btnNew;
        private System.Windows.Forms.SplitContainer splitMain;
        private System.Windows.Forms.ListView lvNotes;
        private System.Windows.Forms.ColumnHeader colTitle;
        private System.Windows.Forms.ColumnHeader colType;
        private System.Windows.Forms.ColumnHeader colUpdated;
        private System.Windows.Forms.WebBrowser webPreview;

        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();

            this.toolStrip = new System.Windows.Forms.ToolStrip();
            this.lblSearch = new System.Windows.Forms.ToolStripLabel();
            this.txtSearch = new System.Windows.Forms.ToolStripTextBox();
            this.btnNew = new System.Windows.Forms.ToolStripButton();
            this.splitMain = new System.Windows.Forms.SplitContainer();
            this.lvNotes = new System.Windows.Forms.ListView();
            this.colTitle = new System.Windows.Forms.ColumnHeader();
            this.colType = new System.Windows.Forms.ColumnHeader();
            this.colUpdated = new System.Windows.Forms.ColumnHeader();
            this.webPreview = new System.Windows.Forms.WebBrowser();

            this.toolStrip.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.splitMain)).BeginInit();
            this.splitMain.Panel1.SuspendLayout();
            this.splitMain.Panel2.SuspendLayout();
            this.splitMain.SuspendLayout();
            this.SuspendLayout();

            // toolStrip
            this.toolStrip.GripStyle = System.Windows.Forms.ToolStripGripStyle.Hidden;
            this.toolStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[]
            {
                this.lblSearch,
                this.txtSearch,
                this.btnNew
            });
            this.toolStrip.Location = new System.Drawing.Point(0, 0);
            this.toolStrip.Name = "toolStrip";
            this.toolStrip.Size = new System.Drawing.Size(1000, 25);

            // lblSearch
            this.lblSearch.Text = "検索:";

            // txtSearch
            this.txtSearch.Size = new System.Drawing.Size(250, 25);
            this.txtSearch.TextChanged += new System.EventHandler(this.TxtSearch_TextChanged);

            // btnNew
            this.btnNew.Text = "新規ノート (Ctrl+N)";
            this.btnNew.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Text;
            this.btnNew.Click += new System.EventHandler(this.BtnNew_Click);

            // splitMain
            this.splitMain.Dock = System.Windows.Forms.DockStyle.Fill;
            this.splitMain.Location = new System.Drawing.Point(0, 25);
            this.splitMain.Size = new System.Drawing.Size(1000, 575);
            this.splitMain.SplitterDistance = 350;

            // lvNotes
            this.lvNotes.Dock = System.Windows.Forms.DockStyle.Fill;
            this.lvNotes.Columns.AddRange(new System.Windows.Forms.ColumnHeader[]
            {
                this.colTitle,
                this.colType,
                this.colUpdated
            });
            this.lvNotes.View = System.Windows.Forms.View.Details;
            this.lvNotes.FullRowSelect = true;
            this.lvNotes.HideSelection = false;
            this.lvNotes.MultiSelect = false;
            this.lvNotes.SelectedIndexChanged += new System.EventHandler(this.LvNotes_SelectedIndexChanged);
            this.splitMain.Panel1.Controls.Add(this.lvNotes);

            // colTitle
            this.colTitle.Text = "タイトル";
            this.colTitle.Width = 200;

            // colType
            this.colType.Text = "種別";
            this.colType.Width = 80;

            // colUpdated
            this.colUpdated.Text = "更新日時";
            this.colUpdated.Width = 130;

            // webPreview
            this.webPreview.Dock = System.Windows.Forms.DockStyle.Fill;
            this.webPreview.MinimumSize = new System.Drawing.Size(20, 20);
            this.webPreview.AllowWebBrowserDrop = false;
            this.webPreview.IsWebBrowserContextMenuEnabled = false;
            this.webPreview.WebBrowserShortcutsEnabled = false;
            this.splitMain.Panel2.Controls.Add(this.webPreview);

            // MainForm
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1000, 600);
            this.Controls.Add(this.splitMain);
            this.Controls.Add(this.toolStrip);
            this.KeyPreview = true;
            this.Text = "NoteBase";
            this.KeyDown += new System.Windows.Forms.KeyEventHandler(this.MainForm_KeyDown);
            this.Load += new System.EventHandler(this.MainForm_Load);

            this.toolStrip.ResumeLayout(false);
            this.toolStrip.PerformLayout();
            this.splitMain.Panel1.ResumeLayout(false);
            this.splitMain.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)(this.splitMain)).EndInit();
            this.splitMain.ResumeLayout(false);
            this.ResumeLayout(false);
            this.PerformLayout();
        }
    }
}
