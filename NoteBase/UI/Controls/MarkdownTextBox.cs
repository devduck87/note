using System;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;
using NoteBase.Storage;

namespace NoteBase.UI.Controls
{
    /// <summary>
    /// Markdown 編集用 TextBox。
    /// Ctrl+V による画像貼り付け、画像ファイルのドラッグ&amp;ドロップに対応する。
    /// 画像は NoteDir プロパティで指定されたノートの images/ フォルダに保存し、
    /// カーソル位置に相対パスのリンクを挿入する。
    /// </summary>
    public class MarkdownTextBox : TextBox
    {
        private readonly ImageStore _imageStore = new ImageStore();

        /// <summary>
        /// 画像保存先のノートフォルダ。空のときは画像貼り付け／DnD は無視する。
        /// </summary>
        public string NoteDir { get; set; }

        public MarkdownTextBox()
        {
            this.Multiline = true;
            this.AcceptsTab = true;
            this.AcceptsReturn = true;
            this.ScrollBars = ScrollBars.Vertical;
            this.Font = new Font("Consolas", 10F);
            this.WordWrap = false;
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            // TextBox は AllowDrop の Designer 設定が無視されるケースがあるため
            // ハンドル生成後に明示的に有効化する。
            this.AllowDrop = true;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            if (e.Control && e.KeyCode == Keys.V
                && Clipboard.ContainsImage()
                && !string.IsNullOrEmpty(NoteDir))
            {
                using (var img = Clipboard.GetImage())
                {
                    if (img != null)
                    {
                        var rel = _imageStore.SavePastedImage(NoteDir, img);
                        InsertAtCursor("![](" + rel + ")\n");
                    }
                }
                e.Handled = true;
                e.SuppressKeyPress = true;
                return;
            }
            base.OnKeyDown(e);
        }

        protected override void OnDragEnter(DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop)
                && !string.IsNullOrEmpty(NoteDir))
            {
                e.Effect = DragDropEffects.Copy;
                return;
            }
            base.OnDragEnter(e);
        }

        protected override void OnDragDrop(DragEventArgs e)
        {
            if (string.IsNullOrEmpty(NoteDir))
            {
                base.OnDragDrop(e);
                return;
            }

            var files = e.Data.GetData(DataFormats.FileDrop) as string[];
            if (files != null)
            {
                foreach (var f in files.Where(ImageStore.IsImageFile))
                {
                    var rel = _imageStore.SaveDroppedImage(NoteDir, f);
                    InsertAtCursor("![](" + rel + ")\n");
                }
            }
            // base は呼ばない (TextBox 内部の drop 処理を抑制)
        }

        private void InsertAtCursor(string text)
        {
            int pos = this.SelectionStart;
            this.Text = this.Text.Insert(pos, text);
            this.SelectionStart = pos + text.Length;
            this.SelectionLength = 0;
            this.Focus();
        }
    }
}
