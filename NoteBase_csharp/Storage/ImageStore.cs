using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;

namespace NoteBase.Storage
{
    /// <summary>
    /// 画像をノートの images/ フォルダに保存し、相対パスを返す。
    /// </summary>
    public class ImageStore
    {
        private static readonly string[] AllowedExt =
            { ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp" };

        /// <summary>
        /// クリップボードからペーストされた Image を PNG として保存する。
        /// </summary>
        public string SavePastedImage(string noteDir, Image image)
        {
            if (image == null) throw new ArgumentNullException("image");

            var imagesDir = Path.Combine(noteDir, "images");
            Directory.CreateDirectory(imagesDir);

            var name = GenerateName(DateTime.Now, ".png");
            var dest = EnsureUniqueName(imagesDir, name);

            image.Save(Path.Combine(imagesDir, dest), ImageFormat.Png);
            return "images/" + dest;
        }

        /// <summary>
        /// ファイルパスから画像をコピーする。形式判定は拡張子。
        /// </summary>
        public string SaveDroppedImage(string noteDir, string srcPath)
        {
            if (!IsImageFile(srcPath))
                throw new ArgumentException("Not an image file: " + srcPath);

            var imagesDir = Path.Combine(noteDir, "images");
            Directory.CreateDirectory(imagesDir);

            var ext = Path.GetExtension(srcPath).ToLowerInvariant();
            var name = GenerateName(DateTime.Now, ext);
            var dest = EnsureUniqueName(imagesDir, name);

            File.Copy(srcPath, Path.Combine(imagesDir, dest), false);
            return "images/" + dest;
        }

        public static bool IsImageFile(string path)
        {
            if (string.IsNullOrEmpty(path)) return false;
            var ext = Path.GetExtension(path).ToLowerInvariant();
            return AllowedExt.Contains(ext);
        }

        private static string GenerateName(DateTime now, string ext)
        {
            return now.ToString("yyyyMMdd_HHmmss_fff") + ext;
        }

        private static string EnsureUniqueName(string dir, string name)
        {
            if (!File.Exists(Path.Combine(dir, name))) return name;

            var basename = Path.GetFileNameWithoutExtension(name);
            var ext = Path.GetExtension(name);
            for (int i = 2; i < 1000; i++)
            {
                var candidate = basename + "_" + i + ext;
                if (!File.Exists(Path.Combine(dir, candidate)))
                    return candidate;
            }
            throw new InvalidOperationException("Failed to generate unique image name: " + name);
        }
    }
}
