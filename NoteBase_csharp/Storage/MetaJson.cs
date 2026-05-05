using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using NoteBase.Core;

namespace NoteBase.Storage
{
    /// <summary>
    /// meta.json 専用の JSON シリアライザ／デシリアライザ。
    /// 標準ライブラリのみで実装するため、自前で読み書きを行う。
    /// 出力はインデント付き、フィールド順固定、null 値は省略する。
    /// </summary>
    public static class MetaJson
    {
        // ============================================================
        // Serialize
        // ============================================================

        public static string Serialize(NoteMeta m)
        {
            var lines = new List<string>();
            lines.Add(IntField("meta_version", m.MetaVersion));
            lines.Add(StringField("id", m.Id));
            lines.Add(StringField("title", m.Title));
            lines.Add(StringField("type", m.Type.ToWireString()));
            if (m.Status.HasValue)
                lines.Add(StringField("status", m.Status.Value.ToWireString()));
            lines.Add(StringArrayField("tags", m.Tags ?? new List<string>()));
            if (!string.IsNullOrEmpty(m.Project))
                lines.Add(StringField("project", m.Project));
            if (m.Due.HasValue)
                lines.Add(StringField("due", FormatDate(m.Due.Value)));
            if (m.Schedule != null)
                lines.Add(ScheduleField("schedule", m.Schedule));
            if (!string.IsNullOrEmpty(m.InstanceOf))
                lines.Add(StringField("instance_of", m.InstanceOf));
            lines.Add(StringField("created", FormatDateTime(m.Created)));
            lines.Add(StringField("updated", FormatDateTime(m.Updated)));

            return "{\n" + string.Join(",\n", lines) + "\n}\n";
        }

        private static string IntField(string name, int value)
        {
            return "  \"" + name + "\": " + value.ToString(CultureInfo.InvariantCulture);
        }

        private static string StringField(string name, string value)
        {
            return "  \"" + name + "\": " + EscapeString(value ?? "");
        }

        private static string StringArrayField(string name, List<string> values)
        {
            var parts = new List<string>();
            foreach (var v in values) parts.Add(EscapeString(v ?? ""));
            return "  \"" + name + "\": [" + string.Join(", ", parts) + "]";
        }

        private static string ScheduleField(string name, Schedule s)
        {
            var sb = new StringBuilder();
            sb.Append("  \"").Append(name).Append("\": {\n");
            var inner = new List<string>();
            inner.Add("    \"frequency\": " + EscapeString(s.Frequency.ToWireString()));
            if (s.Days != null && s.Days.Count > 0)
            {
                var parts = new List<string>();
                foreach (var d in s.Days) parts.Add(EscapeString(d ?? ""));
                inner.Add("    \"days\": [" + string.Join(", ", parts) + "]");
            }
            if (s.DayOfMonth.HasValue)
                inner.Add("    \"day_of_month\": " + s.DayOfMonth.Value.ToString(CultureInfo.InvariantCulture));
            inner.Add("    \"enabled\": " + (s.Enabled ? "true" : "false"));
            sb.Append(string.Join(",\n", inner));
            sb.Append("\n  }");
            return sb.ToString();
        }

        private static string EscapeString(string s)
        {
            var sb = new StringBuilder();
            sb.Append('"');
            foreach (var c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\b': sb.Append("\\b"); break;
                    case '\f': sb.Append("\\f"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20)
                            sb.Append("\\u").Append(((int)c).ToString("X4"));
                        else
                            sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
            return sb.ToString();
        }

        private static string FormatDateTime(DateTime dt)
        {
            return dt.ToString("yyyy-MM-ddTHH:mm:ss", CultureInfo.InvariantCulture);
        }

        private static string FormatDate(DateTime dt)
        {
            return dt.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        }

        // ============================================================
        // Deserialize
        // ============================================================

        public static NoteMeta Deserialize(string json)
        {
            var parser = new Parser(json);
            var dict = parser.ParseObject();
            return MetaFromDict(dict);
        }

        private static NoteMeta MetaFromDict(Dictionary<string, object> d)
        {
            var m = new NoteMeta();

            object v;
            if (d.TryGetValue("meta_version", out v)) m.MetaVersion = ToInt(v);
            if (d.TryGetValue("id", out v)) m.Id = (string)v;
            if (d.TryGetValue("title", out v)) m.Title = (string)v;
            if (d.TryGetValue("type", out v)) m.Type = NoteTypeExtensions.ParseType((string)v);
            if (d.TryGetValue("status", out v))
                m.Status = (v == null) ? null : NoteStatusExtensions.ParseStatus((string)v);
            if (d.TryGetValue("tags", out v))
            {
                m.Tags = new List<string>();
                var lo = v as List<object>;
                if (lo != null)
                    foreach (var o in lo) m.Tags.Add(o == null ? "" : (string)o);
            }
            if (d.TryGetValue("project", out v)) m.Project = (string)v;
            if (d.TryGetValue("due", out v))
                m.Due = (v == null) ? (DateTime?)null : ParseDate((string)v);
            if (d.TryGetValue("schedule", out v) && v is Dictionary<string, object>)
                m.Schedule = ScheduleFromDict((Dictionary<string, object>)v);
            if (d.TryGetValue("instance_of", out v)) m.InstanceOf = (string)v;
            if (d.TryGetValue("created", out v) && v is string)
                m.Created = ParseDateTime((string)v);
            if (d.TryGetValue("updated", out v) && v is string)
                m.Updated = ParseDateTime((string)v);

            return m;
        }

        private static Schedule ScheduleFromDict(Dictionary<string, object> d)
        {
            var s = new Schedule();
            object v;
            if (d.TryGetValue("frequency", out v))
                s.Frequency = ScheduleFrequencyExtensions.ParseFrequency((string)v);
            if (d.TryGetValue("days", out v))
            {
                s.Days = new List<string>();
                var lo = v as List<object>;
                if (lo != null)
                    foreach (var o in lo) s.Days.Add((string)o);
            }
            if (d.TryGetValue("day_of_month", out v))
                s.DayOfMonth = (v == null) ? (int?)null : ToInt(v);
            if (d.TryGetValue("enabled", out v))
                s.Enabled = (v is bool) ? (bool)v : true;
            return s;
        }

        private static int ToInt(object v)
        {
            if (v is long) return (int)(long)v;
            if (v is int) return (int)v;
            if (v is double) return (int)(double)v;
            return 0;
        }

        private static DateTime ParseDateTime(string s)
        {
            DateTime r;
            if (DateTime.TryParseExact(s, "yyyy-MM-ddTHH:mm:ss",
                CultureInfo.InvariantCulture, DateTimeStyles.None, out r))
                return r;
            if (DateTime.TryParse(s, CultureInfo.InvariantCulture, DateTimeStyles.None, out r))
                return r;
            return DateTime.MinValue;
        }

        private static DateTime ParseDate(string s)
        {
            DateTime r;
            if (DateTime.TryParseExact(s, "yyyy-MM-dd",
                CultureInfo.InvariantCulture, DateTimeStyles.None, out r))
                return r;
            if (DateTime.TryParse(s, CultureInfo.InvariantCulture, DateTimeStyles.None, out r))
                return r;
            return DateTime.MinValue;
        }

        // ============================================================
        // 内部 JSON パーサー
        // ============================================================

        private class Parser
        {
            private readonly string _src;
            private int _pos;

            public Parser(string src)
            {
                _src = src ?? "";
                _pos = 0;
            }

            public Dictionary<string, object> ParseObject()
            {
                SkipWs();
                Expect('{');
                var dict = new Dictionary<string, object>();
                SkipWs();
                if (Peek() == '}') { _pos++; return dict; }
                while (true)
                {
                    SkipWs();
                    var key = ParseString();
                    SkipWs();
                    Expect(':');
                    var value = ParseValue();
                    dict[key] = value;
                    SkipWs();
                    char nc = Peek();
                    if (nc == ',') { _pos++; continue; }
                    if (nc == '}') { _pos++; return dict; }
                    throw new FormatException("Expected ',' or '}' at pos " + _pos);
                }
            }

            private object ParseValue()
            {
                SkipWs();
                if (_pos >= _src.Length)
                    throw new FormatException("Unexpected end of JSON");
                char c = _src[_pos];
                if (c == '{') return ParseObject();
                if (c == '[') return ParseArray();
                if (c == '"') return ParseString();
                if (c == 't' || c == 'f') return ParseBool();
                if (c == 'n') { ParseNull(); return null; }
                if (c == '-' || (c >= '0' && c <= '9')) return ParseNumber();
                throw new FormatException("Unexpected character at pos " + _pos + ": " + c);
            }

            private List<object> ParseArray()
            {
                Expect('[');
                var list = new List<object>();
                SkipWs();
                if (Peek() == ']') { _pos++; return list; }
                while (true)
                {
                    list.Add(ParseValue());
                    SkipWs();
                    char nc = Peek();
                    if (nc == ',') { _pos++; continue; }
                    if (nc == ']') { _pos++; return list; }
                    throw new FormatException("Expected ',' or ']' at pos " + _pos);
                }
            }

            private string ParseString()
            {
                Expect('"');
                var sb = new StringBuilder();
                while (_pos < _src.Length)
                {
                    char c = _src[_pos++];
                    if (c == '"') return sb.ToString();
                    if (c == '\\')
                    {
                        if (_pos >= _src.Length)
                            throw new FormatException("Unterminated escape");
                        char esc = _src[_pos++];
                        switch (esc)
                        {
                            case '"': sb.Append('"'); break;
                            case '\\': sb.Append('\\'); break;
                            case '/': sb.Append('/'); break;
                            case 'b': sb.Append('\b'); break;
                            case 'f': sb.Append('\f'); break;
                            case 'n': sb.Append('\n'); break;
                            case 'r': sb.Append('\r'); break;
                            case 't': sb.Append('\t'); break;
                            case 'u':
                                if (_pos + 4 > _src.Length)
                                    throw new FormatException("Bad \\u escape");
                                var hex = _src.Substring(_pos, 4);
                                _pos += 4;
                                sb.Append((char)int.Parse(hex,
                                    NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                                break;
                            default:
                                throw new FormatException("Unknown escape: \\" + esc);
                        }
                    }
                    else
                    {
                        sb.Append(c);
                    }
                }
                throw new FormatException("Unterminated string");
            }

            private object ParseNumber()
            {
                int start = _pos;
                if (_src[_pos] == '-') _pos++;
                while (_pos < _src.Length)
                {
                    char c = _src[_pos];
                    if (char.IsDigit(c) || c == '.' || c == 'e' || c == 'E' || c == '+' || c == '-')
                        _pos++;
                    else break;
                }
                var s = _src.Substring(start, _pos - start);
                if (s.IndexOf('.') < 0 && s.IndexOf('e') < 0 && s.IndexOf('E') < 0)
                {
                    long lv;
                    if (long.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out lv))
                        return lv;
                }
                double dv;
                if (double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out dv))
                    return dv;
                throw new FormatException("Invalid number: " + s);
            }

            private bool ParseBool()
            {
                if (Match("true")) return true;
                if (Match("false")) return false;
                throw new FormatException("Expected bool at pos " + _pos);
            }

            private void ParseNull()
            {
                if (Match("null")) return;
                throw new FormatException("Expected null at pos " + _pos);
            }

            private bool Match(string keyword)
            {
                if (_pos + keyword.Length > _src.Length) return false;
                if (_src.Substring(_pos, keyword.Length) != keyword) return false;
                _pos += keyword.Length;
                return true;
            }

            private void Expect(char c)
            {
                SkipWs();
                if (_pos >= _src.Length || _src[_pos] != c)
                    throw new FormatException("Expected '" + c + "' at pos " + _pos);
                _pos++;
            }

            private char Peek()
            {
                SkipWs();
                if (_pos >= _src.Length)
                    throw new FormatException("Unexpected end of JSON");
                return _src[_pos];
            }

            private void SkipWs()
            {
                while (_pos < _src.Length)
                {
                    char c = _src[_pos];
                    if (c == ' ' || c == '\t' || c == '\n' || c == '\r') _pos++;
                    else break;
                }
            }
        }
    }
}
