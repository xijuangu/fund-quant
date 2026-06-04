import io
import unittest
from datetime import date

from app.importers.csv_importer import parse_nav_csv


class CsvImporterTest(unittest.TestCase):
    def setUp(self):
        self.header = "fund_code,date,unit_nav,accumulated_nav,adjusted_nav,source\n"

    def test_parses_single_row(self):
        csv_content = self.header + "000001,2024-01-02,1.234,2.345,2.456,csv\n"
        rows = parse_nav_csv(io.StringIO(csv_content))
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["fund_code"], "000001")
        self.assertEqual(r["nav_date"], date(2024, 1, 2))
        self.assertAlmostEqual(r["unit_nav"], 1.234)
        self.assertAlmostEqual(r["accumulated_nav"], 2.345)
        self.assertAlmostEqual(r["adjusted_nav"], 2.456)
        self.assertEqual(r["source"], "csv")

    def test_parses_multiple_rows(self):
        csv_content = (
            self.header
            + "000001,2024-01-02,1.0,2.0,2.1,csv\n"
            + "000001,2024-01-03,1.01,2.02,2.12,csv\n"
            + "000002,2024-01-02,3.0,5.0,5.1,akshare\n"
        )
        rows = parse_nav_csv(io.StringIO(csv_content))
        self.assertEqual(len(rows), 3)

    def test_nullable_nav_fields(self):
        csv_content = self.header + "000001,2024-01-02,,,,\n"
        rows = parse_nav_csv(io.StringIO(csv_content))
        r = rows[0]
        self.assertIsNone(r["unit_nav"])
        self.assertIsNone(r["accumulated_nav"])
        self.assertIsNone(r["adjusted_nav"])

    def test_default_source_when_missing(self):
        csv_content = self.header + "000001,2024-01-02,1.0,2.0,2.1,\n"
        rows = parse_nav_csv(io.StringIO(csv_content))
        self.assertEqual(rows[0]["source"], "csv")

    def test_strips_whitespace(self):
        csv_content = self.header + ' 000001 , 2024-01-02 , 1.0 , 2.0 , 2.1 , csv \n'
        rows = parse_nav_csv(io.StringIO(csv_content))
        r = rows[0]
        self.assertEqual(r["fund_code"], "000001")
        self.assertAlmostEqual(r["unit_nav"], 1.0)


class CsvImporterEdgeCaseTest(unittest.TestCase):
    def setUp(self):
        self.header = "fund_code,date,unit_nav,accumulated_nav,adjusted_nav,source\n"

    def test_empty_file_returns_empty_list(self):
        rows = parse_nav_csv(io.StringIO(self.header))
        self.assertEqual(rows, [])

    def test_skips_empty_lines(self):
        csv_content = self.header + "\n\n000001,2024-01-02,1.0,2.0,2.1,csv\n\n"
        rows = parse_nav_csv(io.StringIO(csv_content))
        self.assertEqual(len(rows), 1)

    def test_rejects_missing_fund_code(self):
        csv_content = self.header + ",2024-01-02,1.0,2.0,2.1,csv\n"
        with self.assertRaises(ValueError):
            parse_nav_csv(io.StringIO(csv_content))

    def test_rejects_missing_date(self):
        csv_content = self.header + "000001,,1.0,2.0,2.1,csv\n"
        with self.assertRaises(ValueError):
            parse_nav_csv(io.StringIO(csv_content))

    def test_rejects_invalid_date_format(self):
        csv_content = self.header + "000001,2024/01/02,1.0,2.0,2.1,csv\n"
        with self.assertRaises(ValueError):
            parse_nav_csv(io.StringIO(csv_content))
