using System.Collections.Generic;

namespace NoteBase.Core
{
    /// <summary>
    /// ルーティーンの繰り返し頻度。
    /// </summary>
    public enum ScheduleFrequency
    {
        Daily,
        Weekly,
        Monthly,
    }

    public static class ScheduleFrequencyExtensions
    {
        public static string ToWireString(this ScheduleFrequency f)
        {
            switch (f)
            {
                case ScheduleFrequency.Daily: return "daily";
                case ScheduleFrequency.Weekly: return "weekly";
                case ScheduleFrequency.Monthly: return "monthly";
                default: return "daily";
            }
        }

        public static ScheduleFrequency ParseFrequency(string s)
        {
            switch (s)
            {
                case "daily": return ScheduleFrequency.Daily;
                case "weekly": return ScheduleFrequency.Weekly;
                case "monthly": return ScheduleFrequency.Monthly;
                default: return ScheduleFrequency.Daily;
            }
        }
    }

    /// <summary>
    /// ルーティーン (type=routine) のスケジュール定義。
    /// </summary>
    public class Schedule
    {
        public ScheduleFrequency Frequency { get; set; }
        public List<string> Days { get; set; }
        public int? DayOfMonth { get; set; }
        public bool Enabled { get; set; } = true;
    }
}
