# SPDX-License-Identifier: AGPL-3.0-only
import ctypes as C,json,unittest
from pathlib import Path
from verify_houses import approximate_houses,difference

class HouseGeometryTests(unittest.TestCase):
    def test_independent_geometry_grid(self):
        lib=C.CDLL(str(Path('build/libswe.so').resolve()))
        lib.swe_houses_ex.argtypes=[C.c_double,C.c_int,C.c_double,C.c_double,C.c_int,C.POINTER(C.c_double),C.POINTER(C.c_double)]
        lib.swe_houses_ex.restype=C.c_int
        rows=[]
        # Arbitrary TT/UT1 pairs: both implementations receive the same epochs.
        # This tests geometry, not historical UTC/UT1 conversion or real births.
        for jd in (2451545.,2455197.5,2462502.75,2488069.9):
            for lat in (-50,-25,0,25,50):
                for lon in (-170,-70,30,121.5654):
                    out=approximate_houses(jd+69/86400,jd,lat,lon)
                    cusps=(C.c_double*13)();angles=(C.c_double*10)()
                    self.assertEqual(lib.swe_houses_ex(jd,0,lat,lon,ord('P'),cusps,angles),0)
                    errors=[difference(v,cusps[i+1]) for i,v in enumerate(out['house_cusps'])]
                    error=max(errors)
                    rows.append(dict(jd_ut1=jd,jd_tt=jd+69/86400,latitude=lat,longitude=lon,max_error_arcsec=error))
        result=dict(cases=len(rows),threshold_arcsec=30,max_error_arcsec=max(r['max_error_arcsec'] for r in rows),rows=rows)
        Path('house_grid_comparison.json').write_text(json.dumps(result,indent=2))
        self.assertLess(result['max_error_arcsec'],30)

    def test_checker_rejects_polar_and_outside_date(self):
        for args in ((2451545.,2451545.,80,0),(2400000.,2400000.,0,0)):
            with self.assertRaises(ValueError):approximate_houses(*args)

    def test_equator_symmetry_and_wrap(self):
        a=approximate_houses(2451545.001,2451545.,0,179.9)
        self.assertEqual(len(a['house_cusps']),12)
        self.assertTrue(all(0<=x<360 for x in a['house_cusps']))
        for i in range(6):self.assertAlmostEqual((a['house_cusps'][i+6]-a['house_cusps'][i])%360,180)
