using System.IO;
using System.Text;

namespace NoteBase.Storage
{
    /// <summary>
    /// 一時ファイル + File.Replace でテキストファイルを書き込む。
    /// 書き込み中の中断によるファイル破損を防ぐ。
    /// </summary>
    public static class AtomicWriter
    {
        private static readonly UTF8Encoding Utf8NoBom = new UTF8Encoding(false);

        public static void WriteTextAtomic(string path, string content)
        {
            var dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                Directory.CreateDirectory(dir);

            var tmp = path + ".tmp";
            File.WriteAllText(tmp, content ?? "", Utf8NoBom);

            if (File.Exists(path))
            {
                // 既存ファイルがある場合: tmp → 本体へ置換 (バックアップ無し)
                File.Replace(tmp, path, null);
            }
            else
            {
                File.Move(tmp, path);
            }
        }
    }
}
