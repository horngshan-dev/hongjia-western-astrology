# SPDX-License-Identifier: AGPL-3.0-only
"""Isolated tropical/geocentric Moshier test adapter. Not a public API."""
import ctypes as C
import math
from datetime import datetime
from birth_input import prepare_birth

def calculate(library, date, time, zone, latitude, longitude, **options):
    pre = prepare_birth(date, time, zone, **options)
    if not pre['input_ready']:
        return pre
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in (latitude, longitude)) or not -90 < latitude < 90 or not -180 <= longitude <= 180:
        return {'status': 'needs_input', 'code': 'COORDINATES_INVALID', 'chart': None}
    dt = datetime.fromisoformat(pre['selected']['utc'])
    if not 1900 <= dt.year <= 2099:
        return {'status': 'unsupported', 'code': 'CANDIDATE_DATE_RANGE', 'chart': None}
    lib = C.CDLL(library)
    D = C.POINTER(C.c_double)
    lib.swe_utc_to_jd.argtypes = [C.c_int]*5 + [C.c_double, C.c_int, D, C.c_char_p]
    lib.swe_utc_to_jd.restype = C.c_int
    lib.swe_calc_ut.argtypes = [C.c_double, C.c_int, C.c_int, D, C.c_char_p]
    lib.swe_calc_ut.restype = C.c_int
    lib.swe_houses_ex.argtypes = [C.c_double, C.c_int, C.c_double, C.c_double, C.c_int, D, D]
    lib.swe_houses_ex.restype = C.c_int
    lib.swe_version.argtypes = [C.c_char_p]
    lib.swe_version.restype = C.c_char_p
    version = C.create_string_buffer(256)
    lib.swe_version(version)
    jd = (C.c_double*2)()
    err = C.create_string_buffer(512)
    if lib.swe_utc_to_jd(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,1,jd,err) < 0:
        raise ValueError(err.value.decode())
    planets = []
    for body, name in enumerate(('Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto')):
        values = (C.c_double*6)()
        flags = lib.swe_calc_ut(jd[1],body,4|256,values,err)
        if flags < 0 or flags & 7 != 4:
            raise RuntimeError('Requested Moshier engine not returned: '+err.value.decode())
        planets.append(dict(name=name, longitude=values[0], latitude=values[1], longitude_speed=values[3], retrograde=values[3]<0, returned_flags=flags))
    cusps, angles = (C.c_double*13)(), (C.c_double*10)()
    if lib.swe_houses_ex(jd[1],0,latitude,longitude,ord('P'),cusps,angles) < 0:
        return {'status':'unsupported', 'code':'PLACIDUS_UNAVAILABLE', 'chart':None}
    return dict(status='candidate_calculated', production_ready=False,
        input={k:v for k,v in pre.items() if k not in ('chart','calculation_ready','code','status')}, coordinates=dict(latitude=latitude,longitude=longitude),
        provenance=dict(engine='Swiss Ephemeris',version=version.value.decode(),source_commit='94621aba9f3ff9c32cb721eac0380c30dbb153fe',ephemeris='Moshier analytical',zodiac='tropical',reference='geocentric apparent',house_system='Placidus',jd_tt=jd[0],jd_ut1=jd[1]),
        chart=dict(planets=planets,ascendant=angles[0],midheaven=angles[1],house_cusps=list(cusps)[1:]),warnings=pre['warnings'])
