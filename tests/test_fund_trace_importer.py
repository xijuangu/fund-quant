import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.import_fund_trace import load_fund_trace


class FundTraceImporterTest(unittest.TestCase):
    def _build_db(self) -> Path:
        temp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp.close()
        db_path = Path(temp.name)
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            create table funds (
                code text primary key,
                name text not null default '',
                type integer not null default 0,
                added_at datetime not null default current_timestamp
            );
            create table nav_snapshots (
                id integer primary key autoincrement,
                fund_code text not null,
                date text not null,
                unit_nav real not null,
                accumulated_nav real not null,
                daily_growth_pct real not null default 0,
                recorded_at datetime not null default current_timestamp,
                unique(fund_code, date)
            );
            """
        )
        conn.execute(
            "insert into funds (code, name, type, added_at) values (?, ?, ?, ?)",
            ("000217", "华安黄金ETF联接C", 4, "2026-05-25 14:48:06 +0800"),
        )
        conn.execute(
            "insert into nav_snapshots "
            "(fund_code, date, unit_nav, accumulated_nav, daily_growth_pct, recorded_at) "
            "values (?, ?, ?, ?, ?, ?)",
            ("000217", "2026-04-22", 3.5411, 3.5411, -0.17, "2026-05-25"),
        )
        conn.execute(
            "insert into nav_snapshots "
            "(fund_code, date, unit_nav, accumulated_nav, daily_growth_pct, recorded_at) "
            "values (?, ?, ?, ?, ?, ?)",
            ("007531", "2026-04-22", 1.234, 1.234, 0.1, "2026-05-25"),
        )
        conn.commit()
        conn.close()
        return db_path

    def test_loads_active_funds_and_skips_orphan_nav_by_default(self):
        db_path = self._build_db()

        dataset = load_fund_trace(db_path)

        self.assertEqual([f["fund_code"] for f in dataset.funds], ["000217"])
        self.assertEqual(dataset.funds[0]["asset_bucket"], "gold_commodity")
        self.assertEqual(len(dataset.nav_rows), 1)
        self.assertEqual(dataset.nav_rows[0]["fund_code"], "000217")
        self.assertEqual(dataset.skipped_orphan_nav_rows, 1)

    def test_can_include_orphan_nav_with_inactive_placeholder_fund(self):
        db_path = self._build_db()

        dataset = load_fund_trace(db_path, include_orphans=True)

        self.assertEqual({f["fund_code"] for f in dataset.funds}, {"000217", "007531"})
        orphan = next(f for f in dataset.funds if f["fund_code"] == "007531")
        self.assertFalse(orphan["is_active"])
        self.assertEqual(orphan["fund_name"], "007531")
        self.assertEqual(len(dataset.nav_rows), 2)
        self.assertEqual(dataset.skipped_orphan_nav_rows, 0)


if __name__ == "__main__":
    unittest.main()
