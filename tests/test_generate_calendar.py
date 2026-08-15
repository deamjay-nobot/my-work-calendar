import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_calendar import build_calendar, stable_uid

class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.base = {"calendar": {"name": "Test", "timezone": "Europe/Moscow", "location": "Test location"}, "shifts": []}

    def test_normal_shift(self):
        self.base["shifts"] = [{"type":"DT","date":"2026-08-20","start":"15:00","end":"18:00"}]
        ics = build_calendar(self.base)
        self.assertIn("DTSTART;TZID=Europe/Moscow:20260820T150000", ics)
        self.assertIn("DTEND;TZID=Europe/Moscow:20260820T180000", ics)

    def test_overnight_shift(self):
        self.base["shifts"] = [{"type":"DTN","date":"2026-08-20","start":"22:00","end":"07:00"}]
        ics = build_calendar(self.base)
        self.assertIn("DTEND;TZID=Europe/Moscow:20260821T070000", ics)

    def test_duplicates(self):
        shift = {"type":"K","date":"2026-08-21","start":"15:00","end":"16:00"}
        self.base["shifts"] = [shift, shift]
        self.assertEqual(build_calendar(self.base).count("BEGIN:VEVENT"), 1)

    def test_stable_uid(self):
        shift = {"type":"TR","date":"2026-08-22","start":"16:00","end":"19:45"}
        self.assertEqual(stable_uid(shift, "Test location"), stable_uid(shift, "Test location"))

if __name__ == "__main__":
    unittest.main()
