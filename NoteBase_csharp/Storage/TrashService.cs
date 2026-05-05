using System;
using System.IO;

namespace NoteBase.Storage
{
    /// <summary>
    /// ノートフォルダを trash/ へ移動する。
    /// </summary>
    public class TrashService
    {
        private readonly AppPaths _paths;

        public TrashService(AppPaths paths)
        {
            _paths = paths;
        }

        /// <summary>
        /// 指定 ID のノートフォルダを trash 配下に移動する。
        /// 既に存在しない場合は何もしない。
        /// </summary>
        public void MoveNote(string noteId)
        {
            if (string.IsNullOrEmpty(noteId)) return;
            var src = _paths.NoteDir(noteId);
            if (!Directory.Exists(src)) return;

            Directory.CreateDirectory(_paths.Trash);
            var stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss-fff");
            var destName = stamp + "_" + noteId;
            var dest = Path.Combine(_paths.Trash, destName);
            Directory.Move(src, dest);
        }
    }
}
