# SPDX-License-Identifier: AGPL-3.0-only
import json,unittest
from pathlib import Path
from datetime import datetime,timezone
from verify_horizons import parse_response

class JplResponseTests(unittest.TestCase):
    def setUp(self):
        self.raw=Path('horizons_evidence/Sun.json').read_text()
        self.instant=datetime(2001,6,15,4,34,56,tzinfo=timezone.utc)
    def test_real_response(self):
        lon,lat,sig=parse_response(self.raw,'10',self.instant)
        self.assertEqual(lon,84.1488067)
    def test_wrong_target(self):
        with self.assertRaises(ValueError):parse_response(self.raw,'301',self.instant)
    def test_wrong_time(self):
        with self.assertRaises(ValueError):parse_response(self.raw,'10',self.instant.replace(second=55))
    def test_wrong_center(self):
        with self.assertRaises(ValueError):parse_response(self.raw.replace('GEOCENTRIC','TOPOCENTRIC'),'10',self.instant)
    def test_unknown_version(self):
        d=json.loads(self.raw);d['signature']['version']='99'
        with self.assertRaises(ValueError):parse_response(json.dumps(d),'10',self.instant)
    def test_missing_data(self):
        d=json.loads(self.raw);d['result']='No data'
        with self.assertRaises(ValueError):parse_response(json.dumps(d),'10',self.instant)

    def test_all_ten_saved_responses(self):
        from verify_horizons import TARGETS
        for name,target in TARGETS.items():
            with self.subTest(body=name):
                parse_response(Path('horizons_evidence',name+'.json').read_text(),target,self.instant)
