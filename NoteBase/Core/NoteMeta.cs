using System;
using System.Collections.Generic;

namespace NoteBase.Core
{
    /// <summary>
    /// meta.json と 1:1 対応する POCO。
    /// </summary>
    public class NoteMeta
    {
        public int MetaVersion { get; set; } = 1;
        public string Id { get; set; }
        public string Title { get; set; }
        public NoteType Type { get; set; }
        public NoteStatus? Status { get; set; }
        public List<string> Tags { get; set; } = new List<string>();
        public string Project { get; set; }
        public DateTime? Due { get; set; }
        public Schedule Schedule { get; set; }
        public string InstanceOf { get; set; }
        public DateTime Created { get; set; }
        public DateTime Updated { get; set; }
    }
}
