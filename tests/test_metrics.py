import unittest

from app.services.metrics import calculate_daily_returns, calculate_max_drawdown


class MetricsTest(unittest.TestCase):
    def test_calculates_daily_returns_from_nav_series(self):
        self.assertEqual(calculate_daily_returns([1.0, 1.1, 1.21]), [0.1, 0.1])

    def test_calculates_max_drawdown_from_nav_series(self):
        self.assertAlmostEqual(calculate_max_drawdown([1.0, 1.2, 0.9, 1.1]), -0.25)


if __name__ == "__main__":
    unittest.main()
