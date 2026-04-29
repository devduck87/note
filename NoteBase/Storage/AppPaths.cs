using System.IO;
using System.Reflection;

namespace NoteBase.Storage
{
    /// <summary>
    /// MemoRoot 配下の各サブパスを提供する。
    /// </summary>
    public class AppPaths
    {
        public string Root { get; private set; }

        public AppPaths(string root)
        {
            Root = root;
        }

        public string Notes { get { return Path.Combine(Root, "notes"); } }
        public string Trash { get { return Path.Combine(Root, "trash"); } }
        public string Outputs { get { return Path.Combine(Root, "outputs"); } }
        public string Indexes { get { return Path.Combine(Root, "indexes"); } }
        public string Templates { get { return Path.Combine(Root, "templates"); } }
        public string Canvases { get { return Path.Combine(Root, "canvases"); } }
        public string Config { get { return Path.Combine(Root, "config"); } }

        public string NoteDir(string id) { return Path.Combine(Notes, id); }
        public string MetaPath(string id) { return Path.Combine(NoteDir(id), "meta.json"); }
        public string IndexMdPath(string id) { return Path.Combine(NoteDir(id), "index.md"); }
        public string ImagesDir(string id) { return Path.Combine(NoteDir(id), "images"); }

        public void EnsureLayout()
        {
            Directory.CreateDirectory(Root);
            Directory.CreateDirectory(Notes);
            Directory.CreateDirectory(Trash);
            Directory.CreateDirectory(Outputs);
            Directory.CreateDirectory(Indexes);
            Directory.CreateDirectory(Templates);
            Directory.CreateDirectory(Canvases);
            Directory.CreateDirectory(Config);
        }

        /// <summary>
        /// 既定の MemoRoot は実行ファイル直下の "MemoRoot/" とする。
        /// </summary>
        public static AppPaths Default()
        {
            var exeDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            return new AppPaths(Path.Combine(exeDir, "MemoRoot"));
        }
    }
}
