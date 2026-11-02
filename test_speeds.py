# SPDX-License-Identifier: AGPL-3.0-only
import json, unittest
from pathlib import Path
from verify_speeds import derivative, parse, OFFSETS


class IndependentSpeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=Path('speed_acceptance_20261102')
        cls.raw=(folder/'Sun.json').read_text()
        tasks=json.loads((folder/'inputs.json').read_text())['tasks']
        cls.epochs=sorted({t['jd_tt']+offset/86400 for t in tasks if t['planet']['name']=='Sun' for offset in OFFSETS})

    def test_actual_jpl_timeline(self):
        self.assertEqual(len(parse(self.raw,'10',self.epochs)),len(self.epochs))

    def test_reject_wrong_target_center_scale_and_epoch(self):
        bad_epochs=self.epochs.copy();bad_epochs[0]+=1/86400
        for raw,target,epochs in (
            (self.raw,'301',self.epochs),
            (self.raw.replace('GEOCENTRIC','TOPOCENTRIC'),'10',self.epochs),
            (self.raw.replace('Date_________JDTT','Date_________JDUT'),'10',self.epochs),
            (self.raw,'10',bad_epochs),
            (self.raw,'10',self.epochs[:-1])):
            with self.assertRaises(ValueError):parse(raw,target,epochs)

    def test_reject_unreviewed_api_version(self):
        d=json.loads(self.raw);d['signature']['version']='99'
        with self.assertRaises(ValueError):parse(json.dumps(d),'10',self.epochs)

    def test_circular_difference_across_zero(self):
        # Known linear motion crossing 360/0; naïve differencing fails badly.
        for speed in (-1.25,1.25):
            values={offset:(359.999+speed*offset/86400)%360 for offset in OFFSETS}
            self.assertAlmostEqual(derivative(values,600),speed,places=8)
            self.assertAlmostEqual(derivative(values,300),speed,places=8)

    def test_near_station_keeps_small_signed_speed(self):
        for speed in (-1e-6,0,1e-6):
            values={offset:(12+speed*offset/86400)%360 for offset in OFFSETS}
            self.assertAlmostEqual(derivative(values,600),speed,places=9)
