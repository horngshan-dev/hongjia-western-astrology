# SPDX-License-Identifier: AGPL-3.0-only
import unittest
from birth_input import prepare_birth


class PreflightTests(unittest.TestCase):
    def test_taipei_modern(self):
        r=prepare_birth("2001-06-15","12:34:56","Asia/Taipei")
        self.assertEqual(r["selected"]["utc"],"2001-06-15T04:34:56+00:00")
        self.assertTrue(r["input_ready"])
        self.assertFalse(r["calculation_ready"])
        self.assertIsNone(r["chart"])

    def test_taipei_historical_dst_is_not_fixed_utc8(self):
        r=prepare_birth("1979-07-01","12:00","Asia/Taipei")
        self.assertEqual(r["selected"]["utc"],"1979-07-01T03:00:00+00:00")

    def test_new_york_gap(self):
        r=prepare_birth("2024-03-10","02:30","America/New_York")
        self.assertEqual(r["code"],"LOCAL_TIME_NONEXISTENT")

    def test_new_york_overlap_needs_choice(self):
        r=prepare_birth("2024-11-03","01:30","America/New_York")
        self.assertEqual(r["code"],"LOCAL_TIME_AMBIGUOUS")
        self.assertEqual(len(r["candidates"]),2)

    def test_explicit_overlap_choice(self):
        a=prepare_birth("2024-11-03","01:30","America/New_York",fold=0)
        b=prepare_birth("2024-11-03","01:30","America/New_York",fold=1)
        self.assertEqual(a["selected"]["utc"],"2024-11-03T05:30:00+00:00")
        self.assertEqual(b["selected"]["utc"],"2024-11-03T06:30:00+00:00")

    def test_branch_or_unknown_not_replaced(self):
        for precision in ("unknown","hour_branch_only"):
            r=prepare_birth("2001-06-15","辰時","Asia/Taipei",precision=precision)
            self.assertEqual(r["code"],"BIRTH_TIME_REFINEMENT_REQUIRED")
            self.assertNotIn("selected",r)

    def test_approximate_stays_approximate(self):
        r=prepare_birth("2001-06-15","12:34","Asia/Taipei",precision="approximate")
        self.assertEqual(r["birth_time_precision"],"approximate")
        self.assertTrue(r["warnings"])

    def test_invalid_date_timezone_and_fold(self):
        self.assertEqual(prepare_birth("2023-02-30","12:00","Asia/Taipei")["code"],"BIRTH_DATETIME_INVALID")
        for zone in ("../../etc/passwd","Not/AZone",""):
            self.assertEqual(prepare_birth("2000-01-01","12:00",zone)["code"],"TIMEZONE_INVALID")
        self.assertEqual(prepare_birth("2000-01-01","12:00","Asia/Taipei",fold=True)["code"],"TIMEZONE_FOLD_INVALID")



class StrictClockTests(unittest.TestCase):
    def test_rejects_noncanonical_clock(self):
        for clock in ('1:30', '12:3', '12:34:5', '24:00', '12:60', '12:34Z'):
            with self.subTest(clock=clock):
                self.assertEqual(prepare_birth('2001-06-15',clock,'Asia/Taipei')['code'],'BIRTH_DATETIME_INVALID')

if __name__ == "__main__":
    unittest.main()
