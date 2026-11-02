# SPDX-License-Identifier: AGPL-3.0-only
"""Validation only: ERFA Earth orientation plus independent Placidus bisection.

Never imported by the HTTP engine. Shares explicit TT/UT1 inputs, not Swiss
sidereal-time, obliquity or house routines. Does not certify UTC conversion.
"""
import math as m
import erfa


def independent_houses(jd_tt, jd_ut1, latitude, longitude):
    if not all(m.isfinite(x) for x in (jd_tt, jd_ut1, latitude, longitude)):
        raise ValueError('Nonfinite input')
    if abs(latitude) > 65.5 or abs(longitude) > 180:
        raise ValueError('Outside checker latitude/longitude range')
    if not 2415020.5 <= jd_tt < 2488069.5:
        raise ValueError('Outside checker epoch range')
    tta, ttb = 2451545., jd_tt - 2451545.
    theta = (m.degrees(erfa.gst06a(2451545., jd_ut1-2451545., tta, ttb)) + longitude) % 360
    _, deps = erfa.nut06a(tta, ttb)
    eps = erfa.obl06(tta, ttb) + deps
    phi, a = m.radians(latitude), m.radians(theta)

    def to_ecliptic(ra):
        ra = m.radians(ra)
        return m.degrees(m.atan2(m.sin(ra), m.cos(ra)*m.cos(eps))) % 360

    asc = (m.degrees(m.atan2(-m.cos(a), m.sin(a)*m.cos(eps)+m.tan(phi)*m.sin(eps)))+180) % 360

    def solve(offset, fraction):
        def residual(ra):
            ad = m.asin(m.tan(phi)*m.sin(m.radians(ra))*m.tan(eps))
            return ra-theta-offset-fraction*m.degrees(ad)
        lo, hi = theta+offset-60, theta+offset+60
        if residual(lo) > 0 or residual(hi) < 0:
            raise ValueError('Semi-arc root not bracketed')
        for _ in range(80):
            mid = (lo+hi)/2
            if residual(mid) > 0:
                hi = mid
            else:
                lo = mid
        return to_ecliptic((lo+hi)/2)

    c = {1:asc, 10:to_ecliptic(theta), 11:solve(30,1/3),
         12:solve(60,2/3), 2:solve(120,2/3), 3:solve(150,1/3)}
    for first, opposite in ((1,7),(10,4),(11,5),(12,6),(2,8),(3,9)):
        c[opposite] = (c[first]+180) % 360
    return dict(ascendant=asc, midheaven=c[10], house_cusps=[c[i] for i in range(1,13)])


def run_grid(library, output):
    import ctypes as C
    import json
    from pathlib import Path
    from verify_houses import difference
    lib = C.CDLL(str(Path(library).resolve()))
    lib.swe_houses_ex.argtypes = [C.c_double,C.c_int,C.c_double,C.c_double,C.c_int,C.POINTER(C.c_double),C.POINTER(C.c_double)]
    lib.swe_houses_ex.restype = C.c_int
    rows = []
    # Fixed mathematical TT/UT1 inputs: no future leap-second assumption here.
    for jd in (2415020.5,2431682.5,2444065.5,2451545.,2460482.5):
        for hour in (0,6,12,18):
            ut = jd + hour/24
            tt = ut + 69.184/86400
            for lat in (-65.5,-60,-50,-25,0,25,50,60,65.5):
                for lon in (-179.9,-120,-74,0,30,121.5654,150,179.9):
                    ref = independent_houses(tt,ut,lat,lon)
                    cusps, angles = (C.c_double*13)(), (C.c_double*10)()
                    status = lib.swe_houses_ex(ut,0,lat,lon,ord('P'),cusps,angles)
                    if status < 0:
                        raise RuntimeError('Unexpected Swiss house failure')
                    errors = dict(ascendant=difference(ref['ascendant'],angles[0]),
                                  midheaven=difference(ref['midheaven'],angles[1]))
                    errors.update({'house_'+str(i+1):difference(v,cusps[i+1]) for i,v in enumerate(ref['house_cusps'])})
                    rows.append(dict(jd_tt=tt,jd_ut1=ut,latitude=lat,longitude=lon,errors_arcsec=errors,max_error_arcsec=max(errors.values())))
    result = dict(pyerfa_version=erfa.__version__,erfa_version=erfa.version.erfa_version,
                  independence='ERFA GAST/true obliquity and independent semi-arc roots; shared TT/UT1, not UTC certification',
                  cases=len(rows),threshold_arcsec=1.0,passed=sum(r['max_error_arcsec']<=1 for r in rows),
                  max_error_arcsec=max(r['max_error_arcsec'] for r in rows),rows=rows)
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    return result


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--library',default='build/libswe.so');p.add_argument('--output',default='house_erfa_comparison.json')
    a=p.parse_args();r=run_grid(a.library,a.output)
    raise SystemExit(0 if r['passed']==r['cases'] else 1)
