namespace NoteBase.Core
{
    /// <summary>
    /// ノート単位のステータス。
    /// </summary>
    public enum NoteStatus
    {
        Active,
        Done,
        Pending,
        Archived,
    }

    public static class NoteStatusExtensions
    {
        public static string ToWireString(this NoteStatus s)
        {
            switch (s)
            {
                case NoteStatus.Active: return "active";
                case NoteStatus.Done: return "done";
                case NoteStatus.Pending: return "pending";
                case NoteStatus.Archived: return "archived";
                default: return "active";
            }
        }

        public static NoteStatus? ParseStatus(string s)
        {
            if (s == null) return null;
            switch (s)
            {
                case "active": return NoteStatus.Active;
                case "done": return NoteStatus.Done;
                case "pending": return NoteStatus.Pending;
                case "archived": return NoteStatus.Archived;
                default: return null;
            }
        }
    }
}
