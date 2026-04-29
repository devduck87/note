namespace NoteBase.UI
{
    partial class NoteEditForm
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
                components.Dispose();
            base.Dispose(disposing);
        }

        private System.Windows.Forms.Label lblType;
        private System.Windows.Forms.ComboBox cmbType;
        private System.Windows.Forms.Label lblTitle;
        private System.Windows.Forms.TextBox txtTitle;
        private System.Windows.Forms.Label lblTags;
        private System.Windows.Forms.TextBox txtTags;
        private System.Windows.Forms.Label lblBody;
        private NoteBase.UI.Controls.MarkdownTextBox txtBody;
        private System.Windows.Forms.Button btnAddImage;
        private System.Windows.Forms.Button btnSave;
        private System.Windows.Forms.Button btnCancel;

        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            this.lblType = new System.Windows.Forms.Label();
            this.cmbType = new System.Windows.Forms.ComboBox();
            this.lblTitle = new System.Windows.Forms.Label();
            this.txtTitle = new System.Windows.Forms.TextBox();
            this.lblTags = new System.Windows.Forms.Label();
            this.txtTags = new System.Windows.Forms.TextBox();
            this.lblBody = new System.Windows.Forms.Label();
            this.txtBody = new NoteBase.UI.Controls.MarkdownTextBox();
            this.btnAddImage = new System.Windows.Forms.Button();
            this.btnSave = new System.Windows.Forms.Button();
            this.btnCancel = new System.Windows.Forms.Button();
            this.SuspendLayout();

            // lblType
            this.lblType.Text = "種類:";
            this.lblType.Location = new System.Drawing.Point(12, 15);
            this.lblType.Size = new System.Drawing.Size(60, 18);

            // cmbType
            this.cmbType.Location = new System.Drawing.Point(80, 12);
            this.cmbType.Size = new System.Drawing.Size(160, 24);
            this.cmbType.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbType.SelectedIndexChanged += new System.EventHandler(this.CmbType_SelectedIndexChanged);

            // lblTitle
            this.lblTitle.Text = "タイトル:";
            this.lblTitle.Location = new System.Drawing.Point(12, 50);
            this.lblTitle.Size = new System.Drawing.Size(70, 18);

            // txtTitle
            this.txtTitle.Location = new System.Drawing.Point(80, 47);
            this.txtTitle.Size = new System.Drawing.Size(500, 25);
            this.txtTitle.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;

            // lblTags
            this.lblTags.Text = "タグ:";
            this.lblTags.Location = new System.Drawing.Point(12, 85);
            this.lblTags.Size = new System.Drawing.Size(60, 18);

            // txtTags
            this.txtTags.Location = new System.Drawing.Point(80, 82);
            this.txtTags.Size = new System.Drawing.Size(500, 25);
            this.txtTags.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right;

            // lblBody
            this.lblBody.Text = "本文:";
            this.lblBody.Location = new System.Drawing.Point(12, 115);
            this.lblBody.Size = new System.Drawing.Size(60, 18);

            // txtBody (MarkdownTextBox)
            this.txtBody.Location = new System.Drawing.Point(12, 138);
            this.txtBody.Size = new System.Drawing.Size(568, 270);
            this.txtBody.Anchor = System.Windows.Forms.AnchorStyles.Top
                | System.Windows.Forms.AnchorStyles.Left
                | System.Windows.Forms.AnchorStyles.Right
                | System.Windows.Forms.AnchorStyles.Bottom;

            // btnAddImage
            this.btnAddImage.Text = "画像追加";
            this.btnAddImage.Location = new System.Drawing.Point(12, 420);
            this.btnAddImage.Size = new System.Drawing.Size(100, 30);
            this.btnAddImage.Anchor = System.Windows.Forms.AnchorStyles.Bottom
                | System.Windows.Forms.AnchorStyles.Left;
            this.btnAddImage.Click += new System.EventHandler(this.BtnAddImage_Click);

            // btnSave
            this.btnSave.Text = "保存";
            this.btnSave.Location = new System.Drawing.Point(400, 420);
            this.btnSave.Size = new System.Drawing.Size(80, 30);
            this.btnSave.Anchor = System.Windows.Forms.AnchorStyles.Bottom
                | System.Windows.Forms.AnchorStyles.Right;
            this.btnSave.Click += new System.EventHandler(this.BtnSave_Click);

            // btnCancel
            this.btnCancel.Text = "取消";
            this.btnCancel.Location = new System.Drawing.Point(500, 420);
            this.btnCancel.Size = new System.Drawing.Size(80, 30);
            this.btnCancel.Anchor = System.Windows.Forms.AnchorStyles.Bottom
                | System.Windows.Forms.AnchorStyles.Right;
            this.btnCancel.Click += new System.EventHandler(this.BtnCancel_Click);

            // NoteEditForm
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(594, 460);
            this.MinimumSize = new System.Drawing.Size(500, 400);
            this.Controls.Add(this.lblType);
            this.Controls.Add(this.cmbType);
            this.Controls.Add(this.lblTitle);
            this.Controls.Add(this.txtTitle);
            this.Controls.Add(this.lblTags);
            this.Controls.Add(this.txtTags);
            this.Controls.Add(this.lblBody);
            this.Controls.Add(this.txtBody);
            this.Controls.Add(this.btnAddImage);
            this.Controls.Add(this.btnSave);
            this.Controls.Add(this.btnCancel);
            this.Text = "新規ノート";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.NoteEditForm_FormClosing);
            this.ResumeLayout(false);
            this.PerformLayout();
        }
    }
}
