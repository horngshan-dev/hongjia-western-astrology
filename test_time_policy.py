# SPDX-License-Identifier: AGPL-3.0-only
import unittest
from pathlib import Path
from datetime import datetime, timezone
from calculate_candidate import calculate
from time_policy import check_time_model

LIB=str(Path('build/libswe.so').resolve())


class TimePolicyTests(unittest.TestCase):
    def chart(self,date,time='12:00:00',zone='UTC'):
        return calculate(LIB,date,time,zone,25.033,121.5654)

    def test_far_future_rejected_without_native_library(self):
        r=calculate('/does/not/exist','2099-12-31','12:00','UTC',25,121)
        self.assertEqual(r['code'],'TIME_MODEL_OUTSIDE_VALIDATED_RANGE')
        self.assertIsNone(r['chart'])

    def test_utc_boundary_not_local_year(self):
        r=self.chart('2027-01-01','00:30','Asia/Taipei')
        self.assertEqual(r['status'],'candidate_calculated')
        self.assertEqual(r['input']['selected']['utc'],'2026-12-31T16:30:00+00:00')
        r=self.chart('2026-12-31','23:30','America/New_York')
        self.assertEqual(r['code'],'TIME_MODEL_OUTSIDE_VALIDATED_RANGE')
        self.assertIsNone(r['chart'])

    def test_historical_approximation_explicit(self):
        r=self.chart('1945-08-15')
        self.assertEqual(r['time_model']['input_scale_interpretation'],'pre_1972_civil_as_ut1_approximation')
        self.assertTrue(any('Pre-1972' in w for w in r['warnings']))

    def test_leap_second_transition(self):
        a=self.chart('2016-12-31','23:59:59')
        b=self.chart('2017-01-01','00:00:00')
        self.assertEqual(a['time_model']['tai_minus_utc_seconds'],36)
        self.assertEqual(b['time_model']['tai_minus_utc_seconds'],37)
        self.assertAlmostEqual((b['provenance']['jd_tt']-a['provenance']['jd_tt'])*86400,2,delta=.0001)

    def test_native_tt_mismatch_fails_closed(self):
        dt=datetime(2000,1,1,12,tzinfo=timezone.utc)
        self.assertNotIn('code',check_time_model(dt,2451545+64.184/86400))
        r=check_time_model(dt,2451545+65.184/86400)
        self.assertEqual(r['code'],'TIME_STANDARD_CONVERSION_UNVERIFIED')

    def test_existing_natal_result_unchanged(self):
        r=calculate(LIB,'2001-06-15','12:34:56','Asia/Taipei',25.033,121.5654)
        self.assertAlmostEqual(r['chart']['planets'][0]['longitude'],84.14881185582166,places=9)
        self.assertAlmostEqual(r['chart']['ascendant'],183.47028655794708,places=9)
        self.assertFalse(r['production_ready'])
        self.assertEqual(r['warnings'],[])
