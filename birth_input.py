# SPDX-License-Identifier: AGPL-3.0-only
"""Offline Western natal input preflight; no horoscope is calculated."""
from datetime import datetime, timezone
import re
from importlib.resources import files
from zoneinfo import ZoneInfo
import tzdata


def prepare_birth(date_text, time_text, timezone_id, *, precision="exact", fold=None):
    base = {"contract": "hongjia-western-birth-preflight@0.1.0",
            "calculation_ready": False, "input_ready": False,
            "provenance": {"tzdata_package": tzdata.__version__,
                           "iana_version": tzdata.IANA_VERSION},
            "chart": None}
    def stop(code, **extra):
        return dict(base, status="needs_input", code=code, **extra)
    if precision not in ("exact", "approximate", "hour_branch_only", "unknown"):
        return stop("BIRTH_TIME_PRECISION_INVALID")
    if precision in ("unknown", "hour_branch_only") or not time_text:
        return stop("BIRTH_TIME_REFINEMENT_REQUIRED",
                    message="No noon, branch midpoint or minute is substituted.")
    if fold is not None and (type(fold) is not int or fold not in (0, 1)):
        return stop("TIMEZONE_FOLD_INVALID")
    if not isinstance(time_text, str) or not re.fullmatch(r'([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?', time_text):
        return stop('BIRTH_DATETIME_INVALID')
    try:
        # Explicit format: no silently accepted offsets or inferred dates.
        naive = datetime.strptime(date_text + "T" + time_text,
            "%Y-%m-%dT%H:%M:%S" if len(time_text) == 8 else "%Y-%m-%dT%H:%M")
        if naive.strftime("%Y-%m-%d") != date_text:
            return stop("BIRTH_DATETIME_INVALID")
    except (ValueError, TypeError, AttributeError):
        return stop("BIRTH_DATETIME_INVALID")
    if not isinstance(timezone_id, str) or any(
        part in ("", ".", "..") for part in timezone_id.split("/")
    ) or timezone_id.startswith("/"):
        return stop("TIMEZONE_INVALID")
    try:
        # Read the identified tzdata package, not an unversioned host database.
        with files("tzdata.zoneinfo").joinpath(*timezone_id.split("/")).open("rb") as f:
            zone = ZoneInfo.from_file(f, key=timezone_id)
    except (OSError, ValueError):
        return stop("TIMEZONE_INVALID")
    candidates = []
    seen = set()
    for choice in (0, 1):
        local = naive.replace(tzinfo=zone, fold=choice)
        utc = local.astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None) != naive:
            continue
        stamp = utc.isoformat()
        if stamp not in seen:
            seen.add(stamp)
            candidates.append({"fold": choice, "utc": stamp,
                               "local_with_offset": local.isoformat()})
    if not candidates:
        return stop("LOCAL_TIME_NONEXISTENT", timezone=timezone_id)
    if len(candidates) > 1 and fold is None:
        return stop("LOCAL_TIME_AMBIGUOUS", candidates=candidates, timezone=timezone_id)
    selected = next((c for c in candidates if c["fold"] == fold), None) if len(candidates)>1 else candidates[0]
    return dict(base, status="input_ready_engine_pending", input_ready=True,
                code="EPHEMERIS_NOT_CONNECTED", timezone=timezone_id,
                birth_time_precision=precision, selected=selected,
                warnings=["Approximate birth time: angles and houses need uncertainty review."]
                    if precision == "approximate" else [])
