namespace NoteBase.UI
{
    partial class NotePickerDialog
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
                components.Dispose();
            base.Dispose(disposing);
        }

        private System.Windows.Forms.Label lblSearch;
        private System.Windows.Forms.TextBox txtSearch;
        private System.Windows.Forms.ListView lvNotes;
        private System.Windows.Forms.ColumnHeader colTitle;
        private System.Windows.Forms.ColumnHeader colType;
        private System.Windows.Forms.ColumnHeader colUpdated;
        private System.Windows.Forms.Button btnOk;
        private System.Windows.Forms.Button btnCancel;

        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();

            this.lblSearch = new System.Windows.Forms.Label();
            this.txtSearch = new System.Windows.Forms.TextBox();
            this.lvNotes = new System.Windows.Forms.ListView();
            this.colTitle = new System.Windows.Forms.ColumnHeader();
            this.colType = new System.Windows.Forms.ColumnHeader();
            this.colUpdated = new System.Windows.Forms.ColumnHeader();
            this.btnOk = new System.Windows.Forms.Button();
            this.btnCancel = new System.Windows.Forms.Button();
            this.SuspendLayout();

            // lblSearch
            this.lblSearch.Text = "検索:";
            this.lblSearch.Location = new System.Drawing.Point(12, 14);
            this.lblSearch.Size = new System.Drawing.Size(40, 20);

            // txtSearch
            this.txtSearch.Location = new System.Drawing.Point(56, 11);
            this.txtSearch.Size = new System.Drawing.Size(440, 22);
            this.txtSearch.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;
            this.txtSearch.TextChanged += new System.EventHandler(this.TxtSearch_TextChanged);
            this.txtSearch.KeyDown += new System.Windows.Forms.KeyEventHandler(this.TxtSearch_KeyDown);

            // lvNotes
            this.lvNotes.Location = new System.Drawing.Point(12, 42);
            this.lvNotes.Size = new System.Drawing.Size(484, 320);
            this.lvNotes.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right
                | System.Windows.Forms.AnchorStyles.Bottom;
            this.lvNotes.View = System.Windows.Forms.View.Details;
            this.lvNotes.FullRowSelect = true;
            this.lvNotes.HideSelection = false;
            this.lvNotes.MultiSelect = false;
            this.lvNotes.Columns.AddRange(new System.Windows.Forms.ColumnHeader[]
            {
                this.colTitle, this.colType, this.colUpdated
            });
            this.lvNotes.DoubleClick += new System.EventHandler(this.LvNotes_DoubleClick);
            this.lvNotes.KeyDown += new System.Windows.Forms.KeyEventHandler(this.LvNotes_KeyDown);

            this.colTitle.Text = "タイトル"; this.colTitle.Width = 250;
            this.colType.Text = "種別"; this.colType.Width = 80;
            this.colUpdated.Text = "更新日時"; this.colUpdated.Width = 130;

            // btnOk
            this.btnOk.Text = "挿入";
            this.btnOk.Location = new System.Drawing.Point(326, 374);
            this.btnOk.Size = new System.Drawing.Size(80, 28);
            this.btnOk.Anchor = System.Windows.Forms.AnchorStyles.Bottom
                | System.Windows.Forms.AnchorStyles.Right;
            this.btnOk.Click += new System.EventHandler(this.BtnOk_Click);

            // btnCancel
            this.btnCancel.Text = "取消";
            this.btnCancel.Location = new System.Drawing.Point(416, 374);
            this.btnCancel.Size = new System.Drawing.Size(80, 28);
            this.btnCancel.Anchor = System.Windows.Forms.AnchorStyles.Bottom
                | System.Windows.Forms.AnchorStyles.Right;
            this.btnCancel.DialogResult = System.Windows.Forms.DialogResult.Cancel;

            // NotePickerDialog
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(508, 414);
            this.MinimumSize = new System.Drawing.Size(400, 300);
            this.Controls.Add(this.lblSearch);
            this.Controls.Add(this.txtSearch);
            this.Controls.Add(this.lvNotes);
            this.Controls.Add(this.btnOk);
            this.Controls.Add(this.btnCancel);
            this.AcceptButton = this.btnOk;
            this.CancelButton = this.btnCancel;
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.Sizable;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent;
            this.Text = "ノートリンクを挿入";
            this.Load += new System.EventHandler(this.NotePickerDialog_Load);
            this.ResumeLayout(false);
            this.PerformLayout();
        }
    }
}
