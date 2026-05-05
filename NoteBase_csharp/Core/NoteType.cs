namespace NoteBase.Core
{
    /// <summary>
    /// ノート種別。meta.json の "type" フィールドと対応する。
    /// </summary>
    public enum NoteType
    {
        Procedure,
        Memo,
        Todo,
        Routine,
        Checklist,
        Log,
        Daily,
        Project,
    }

    public static class NoteTypeExtensions
    {
        public static string ToWireString(this NoteType t)
        {
            switch (t)
            {
                case NoteType.Procedure: return "procedure";
                case NoteType.Memo: return "memo";
                case NoteType.Todo: return "todo";
                case NoteType.Routine: return "routine";
                case NoteType.Checklist: return "checklist";
                case NoteType.Log: return "log";
                case NoteType.Daily: return "daily";
                case NoteType.Project: return "project";
                default: return "memo";
            }
        }

        public static NoteType ParseType(string s)
        {
            if (s == null) return NoteType.Memo;
            switch (s)
            {
                case "procedure": return NoteType.Procedure;
                case "memo": return NoteType.Memo;
                case "todo": return NoteType.Todo;
                case "routine": return NoteType.Routine;
                case "checklist": return NoteType.Checklist;
                case "log": return NoteType.Log;
                case "daily": return NoteType.Daily;
                case "project": return NoteType.Project;
                default: return NoteType.Memo;
            }
        }

        public static string DisplayName(this NoteType t)
        {
            switch (t)
            {
                case NoteType.Procedure: return "手順書";
                case NoteType.Memo: return "備忘録";
                case NoteType.Todo: return "Todo";
                case NoteType.Routine: return "ルーティーン";
                case NoteType.Checklist: return "チェックリスト";
                case NoteType.Log: return "ログ";
                case NoteType.Daily: return "日次メモ";
                case NoteType.Project: return "プロジェクト";
                default: return t.ToString();
            }
        }
    }
}
