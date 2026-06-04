import unittest

import pandas as pd

from app.services.nav_alignment import (
    align_nav_dates,
    build_common_date_index,
    select_nav_policy,
)


class NavAlignmentTest(unittest.TestCase):
    def setUp(self):
        self.fund_navs = {
            "A": pd.DataFrame(
                {"unit_nav": [1.0, 1.1, 1.2, 1.3], "adjusted_nav": [2.0, 2.2, 2.4, 2.6]},
                index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
            ),
            "B": pd.DataFrame(
                {"unit_nav": [3.0, 3.3, 3.6], "adjusted_nav": [5.0, 5.5, 6.0]},
                index=pd.to_datetime(["2024-01-03", "2024-01-04", "2024-01-05"]),
            ),
        }

    def test_builds_common_date_index(self):
        common = build_common_date_index(self.fund_navs)
        expected = pd.to_datetime(["2024-01-03", "2024-01-04", "2024-01-05"])
        self.assertEqual(list(common), list(expected))

    def test_select_nav_policy_prefers_adjusted(self):
        policy = select_nav_policy(self.fund_navs)
        self.assertEqual(policy["preferred"], "adjusted_nav")
        self.assertEqual(policy["actual_used"]["A"], "adjusted_nav")
        self.assertEqual(policy["mixed_policy"], False)

    def test_select_nav_policy_falls_back(self):
        navs = {
            "A": pd.DataFrame(
                {"unit_nav": [1.0], "accumulated_nav": [2.0]},
                index=pd.to_datetime(["2024-01-02"]),
            ),
            "B": pd.DataFrame(
                {"unit_nav": [3.0], "accumulated_nav": [5.0]},
                index=pd.to_datetime(["2024-01-02"]),
            ),
        }
        policy = select_nav_policy(navs)
        self.assertEqual(policy["preferred"], "accumulated_nav")

    def test_align_nav_dates_ffills_short_gaps(self):
        navs = {
            "A": pd.DataFrame(
                {"adjusted_nav": [1.0, 1.1, 1.2]},
                index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05"]),
            ),
        }
        common = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
        aligned, diag = align_nav_dates(navs, common, "adjusted_nav")
        self.assertEqual(len(aligned["A"]), 4)
        self.assertAlmostEqual(aligned["A"].iloc[2], 1.1)  # forward-filled

    def test_align_nav_dates_does_not_ffill_before_start(self):
        navs = {
            "A": pd.DataFrame(
                {"adjusted_nav": [1.0, 1.1]},
                index=pd.to_datetime(["2024-01-03", "2024-01-04"]),
            ),
        }
        common = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
        aligned, diag = align_nav_dates(navs, common, "adjusted_nav")
        self.assertTrue(pd.isna(aligned["A"].iloc[0]))  # before inception, not filled

    def test_missing_data_diagnostics(self):
        navs = {
            "A": pd.DataFrame(
                {"adjusted_nav": [1.0, 1.1, 1.2]},
                index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05"]),
            ),
        }
        common = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
        aligned, diag = align_nav_dates(navs, common, "adjusted_nav")
        self.assertEqual(diag["A"]["forward_fill_count"], 1)
