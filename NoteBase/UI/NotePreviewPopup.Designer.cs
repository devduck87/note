namespace NoteBase.UI
{
    partial class NotePreviewPopup
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
                components.Dispose();
            base.Dispose(disposing);
        }

        private System.Windows.Forms.WebBrowser webContent;

        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            this.webContent = new System.Windows.Forms.WebBrowser();
            this.SuspendLayout();

            // webContent
            this.webContent.Dock = System.Windows.Forms.DockStyle.Fill;
            this.webContent.MinimumSize = new System.Drawing.Size(20, 20);
            this.webContent.AllowWebBrowserDrop = false;
            this.webContent.IsWebBrowserContextMenuEnabled = false;
            this.webContent.WebBrowserShortcutsEnabled = false;
            this.webContent.ScriptErrorsSuppressed = true;

            // NotePreviewPopup
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(520, 360);
            this.Controls.Add(this.webContent);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.Manual;
            this.Text = "プレビュー";
            this.TopMost = true;
            this.ResumeLayout(false);
        }
    }
}
