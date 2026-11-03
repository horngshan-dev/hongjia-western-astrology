# SPDX-License-Identifier: AGPL-3.0-only
"""Pinned candidate time-model policy; not an Earth orientation data service."""
from datetime import datetime, timezone

POLICY = 'western-time-model@0.2.0'
UTC_LIMIT = datetime(2027, 1, 1, tzinfo=timezone.utc)  # exclusive
LEAP_SOURCE = 'https://datacenter.iers.org/data/html/bulletinc-072.html'
# Effective UTC dates after the initial TAI-UTC=10s at 1972-01-01.
LEAPS = tuple(datetime.fromisoformat(d).replace(tzinfo=timezone.utc) for d in (
    '1972-07-01','1973-01-01','1974-01-01','1975-01-01','1976-01-01',
    '1977-01-01','1978-01-01','1979-01-01','1980-01-01','1981-07-01',
    '1982-07-01','1983-07-01','1985-07-01','1988-01-01','1990-01-01',
    '1991-01-01','1992-07-01','1993-07-01','1994-07-01','1996-01-01',
    '1997-07-01','1999-01-01','2006-01-01','2009-01-01','2012-07-01',
    '2015-07-01','2017-01-01'))


def check_time_model(dt, jd_tt):
    if dt >= UTC_LIMIT:
        return dict(status='unsupported',code='TIME_MODEL_OUTSIDE_VALIDATED_RANGE',chart=None)
    metadata = dict(policy=POLICY,utc_limit_exclusive=UTC_LIMIT.isoformat(),
                    leap_second_source=LEAP_SOURCE,ut1_model='Swiss Ephemeris Delta T; no observed IERS EOP supplied')
    warnings = []
    if dt.year < 1972:
        metadata['input_scale_interpretation'] = 'pre_1972_civil_as_ut1_approximation'
        warnings.append('Pre-1972 civil time is treated as approximate UT1, not reconstructed historical UTC; angles and houses inherit this uncertainty.')
    else:
        nominal_jd = 2440587.5 + (dt-datetime(1970,1,1,tzinfo=timezone.utc)).total_seconds()/86400
        tai_minus_utc = 10 + sum(dt >= effective for effective in LEAPS)
        expected_tt = nominal_jd + (tai_minus_utc+32.184)/86400
        # Detect native silent UTC->UT1 fallback rather than accepting its label.
        if abs(jd_tt-expected_tt)*86400 > 0.001:
            return dict(status='unsupported',code='TIME_STANDARD_CONVERSION_UNVERIFIED',chart=None)
        metadata.update(input_scale_interpretation='UTC',tai_minus_utc_seconds=tai_minus_utc)
    return dict(metadata=metadata,warnings=warnings)
