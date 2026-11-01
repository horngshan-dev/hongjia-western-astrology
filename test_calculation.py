# SPDX-License-Identifier: AGPL-3.0-only
import json, os, subprocess, unittest
from pathlib import Path
from calculate_candidate import calculate

ROOT=Path(__file__).resolve().parent/'build'
LIB=str(ROOT/'libswe.so')

class CalculationTests(unittest.TestCase):
    def sample(self, **kw):
        return calculate(LIB,'2001-06-15','12:34:56','Asia/Taipei',kw.get('lat',25.033),121.5654)

    def test_official_cli_same_ut1(self):
        r=self.sample()
        output=subprocess.check_output([str(ROOT/'swetest'),'-bj'+str(r['provenance']['jd_ut1']),'-ut','-p0123456789','-emos','-house121.5654,25.033,P','-fPl','-g,','-head'],text=True)
        rows={k.strip():float(v) for k,v in (line.split(',') for line in output.splitlines())}
        for p in r['chart']['planets']:
            self.assertAlmostEqual(p['longitude'],rows[p['name']],delta=1e-7)
        for i,v in enumerate(r['chart']['house_cusps'],1):
            self.assertAlmostEqual(v,rows['house '+str(i).rjust(2)],delta=1e-7)
        self.assertAlmostEqual(r['chart']['ascendant'],rows['Ascendant'],delta=1e-7)
        self.assertAlmostEqual(r['chart']['midheaven'],rows['MC'],delta=1e-7)

    def test_polar_no_silent_porphyry(self):
        self.assertEqual(self.sample(lat=80)['code'],'PLACIDUS_UNAVAILABLE')

    def test_nonfinite_coordinates(self):
        self.assertEqual(self.sample(lat=float('nan'))['code'],'COORDINATES_INVALID')

    def test_unknown_birth_time_never_filled(self):
        r=calculate(LIB,'2001-06-15',None,'Asia/Taipei',25,121,precision='unknown')
        self.assertIsNone(r['chart'])

    def test_dst_gap_no_chart(self):
        r=calculate(LIB,'2024-03-10','02:30','America/New_York',40,-74)
        self.assertEqual(r['code'],'LOCAL_TIME_NONEXISTENT')

    def test_geometry_and_retrograde(self):
        c=self.sample()['chart']
        self.assertEqual(len(c['planets']),10)
        self.assertEqual(len(c['house_cusps']),12)
        for v in c['house_cusps']:
            self.assertTrue(0<=v<360)
        self.assertAlmostEqual((c['house_cusps'][6]-c['house_cusps'][0])%360,180)
        self.assertTrue(next(p for p in c['planets'] if p['name']=='Mercury')['retrograde'])

if __name__=='__main__': unittest.main()
