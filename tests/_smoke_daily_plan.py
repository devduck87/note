"""手動スモーク: DailyPlanDialog を構築 + 候補ロード + 即終了。"""

from __future__ import annotations

import tempfile
import tkinter as tk
from datetime import date

from notebase.core.note_type import NoteType
from notebase.core.schedule import Schedule, ScheduleFrequency
from notebase.storage.app_paths import AppPaths
from notebase.storage.note_repository import NoteRepository
from notebase.storage.trash_service import TrashService
from notebase.ui.daily_plan_dialog import DailyPlanDialog


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        paths = AppPaths(td)
        paths.ensure_layout()
        repo = NoteRepository(paths, TrashService(paths))

        # シードデータ
        r = repo.create_draft(NoteType.ROUTINE)
        r.title = "朝のルーティン"
        r.schedule = Schedule(frequency=ScheduleFrequency.DAILY, enabled=True)
        repo.save_new(r, "- [ ] メールチェック")

        t = repo.create_draft(NoteType.TODO)
        t.title = "雑務"
        repo.save_new(t, f"- [ ] テスト @{date.today().isoformat()}")

        root = tk.Tk()
        root.withdraw()
        dlg = DailyPlanDialog(root, repo)
        # show() は wait_window でブロックするので直接 _build + _reload を呼ぶ
        dlg._build()
        dlg._reload_candidates()
        root.update_idletasks()
        root.update()
        rows = dlg._tree.get_children()
        print(f"Candidate rows: {len(rows)}")
        if rows:
            vals = dlg._tree.item(rows[0], "values")
            # 種類 / 内容 / 所要分 を ASCII 文字で確認 (✓は cp932 で死ぬので除外)
            print(f"First kind={vals[1]!r} text={vals[2]!r} min={vals[3]!r}")
        dlg._top.destroy()
        root.destroy()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
