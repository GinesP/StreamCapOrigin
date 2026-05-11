import unittest

from app.qt.utils.formatters import fmt_duration


class FormattersTests(unittest.TestCase):
    def test_fmt_duration_none_returns_em_dash(self):
        self.assertEqual(fmt_duration(None), "—")

    def test_fmt_duration_below_one_minute(self):
        self.assertEqual(fmt_duration(0.5), "<1m")
        self.assertEqual(fmt_duration(0), "<1m")

    def test_fmt_duration_exact_hours(self):
        self.assertEqual(fmt_duration(60), "1:00")
        self.assertEqual(fmt_duration(120), "2:00")

    def test_fmt_duration_hours_and_minutes(self):
        self.assertEqual(fmt_duration(90), "1:30")
        self.assertEqual(fmt_duration(150), "2:30")
        self.assertEqual(fmt_duration(12 * 60 + 5), "12:05")

    def test_fmt_duration_single_digit_minutes_padded(self):
        self.assertEqual(fmt_duration(65), "1:05")


if __name__ == "__main__":
    unittest.main()
