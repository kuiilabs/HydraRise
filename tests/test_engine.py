import unittest
from datetime import datetime

from hydrarise import ConfigManager, DailyRecord, ReminderEngine


class ReminderEngineTests(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigManager()
        self.rec = DailyRecord()
        self.rec.reset()
        self.engine = ReminderEngine()

    def test_current_period_weekday(self):
        now = datetime(2026, 4, 6, 10, 0, 0)  # Monday
        period = self.engine.current_period(now)
        self.assertIsNotNone(period)
        self.assertEqual(period[0].hour, 9)

    def test_no_period_on_weekend(self):
        now = datetime(2026, 4, 5, 10, 0, 0)  # Sunday
        self.assertIsNone(self.engine.current_period(now))

    def test_should_drink_after_interval(self):
        now = datetime(2026, 4, 6, 10, 0, 0)
        self.assertTrue(self.engine.should_drink(now, self.cfg, self.rec))

    def test_risk_level_escalation(self):
        self.rec._d["last_posture_reset_time"] = "2026-04-06 08:00:00"
        now = datetime(2026, 4, 6, 10, 30, 0)
        self.assertEqual(self.engine.risk_level(now, self.cfg, self.rec), "high")


if __name__ == "__main__":
    unittest.main()
