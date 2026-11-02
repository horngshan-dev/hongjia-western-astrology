# SPDX-License-Identifier: AGPL-3.0-only
"""Validation only: independent JPL position differences versus native speeds.
Serial NASA requests, fail closed on source/schema/network mismatch. TT epochs
are deliberately shared to isolate speeds from historical UTC reconstruction.
"""
import argparse, csv, hashlib, io, json, math, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from calculate_candidate import calculate
from verify_horizons import TARGETS

OFFSETS=(-1200,-600,-300,0,300,600,1200)
# Fixed BEFORE comparison: engineering acceptance, not claimed absolute accuracy.
TOLERANCE_ARCSEC_DAY=2.0
SIGN_GUARD_ARCSEC_DAY=0.2
STENCIL_STABILITY_ARCSEC_DAY=0.2


def delta(a,b):
    return (a-b+180)%360-180


def derivative(values, step_seconds):
    """Fourth-order symmetric derivative, unwrapped about the center."""
    h=step_seconds
    center=values[0]
    return (delta(values[-2*h],center)-8*delta(values[-h],center)
            +8*delta(values[h],center)-delta(values[2*h],center))/(12*h/86400)


def request_url(target,epochs):
    params=dict(format='json',COMMAND="'"+target+"'",OBJ_DATA="'NO'",MAKE_EPHEM="'YES'",EPHEM_TYPE="'OBSERVER'",CENTER="'500@399'",
                TLIST="'"+' '.join(f'{jd:.10f}' for jd in epochs)+"'",TLIST_TYPE="'JD'",TIME_TYPE="'TT'",CAL_FORMAT="'JD'",
                QUANTITIES="'31'",CSV_FORMAT="'YES'",ANG_FORMAT="'DEG'",TIME_DIGITS="'FRACSEC'",EXTRA_PREC="'YES'")
    return 'https://ssd.jpl.nasa.gov/api/horizons.api?'+urlencode(params)


def parse(raw,target,epochs):
    d=json.loads(raw); sig=d.get('signature',{})
    if sig.get('source')!='NASA/JPL Horizons API' or sig.get('version')!='1.2':
        raise ValueError('Unreviewed API source/version')
    text=d.get('result','')
    if d.get('error') or not re.search(r'Target body name:.*\('+re.escape(target)+r'\)',text):
        raise ValueError('Wrong target or API error')
    if 'Center body name: Earth (399)' not in text or 'Center-site name: GEOCENTRIC' not in text:
        raise ValueError('Wrong observing center')
    if 'Date_________JDTT' not in text or 'ObsEcLon' not in text or 'ObsEcLat' not in text:
        raise ValueError('Wrong time scale/columns')
    lines=text.split('$$SOE')[1].split('$$EOE')[0].strip().splitlines()
    rows=list(csv.reader(lines))
    if len(rows)!=len(epochs): raise ValueError('Epoch count mismatch')
    result={}
    for row,jd in zip(rows,epochs):
        fields=[x.strip() for x in row]
        if len(fields)!=6 or fields[-1]!='': raise ValueError('Unexpected columns')
        actual=float(fields[0]);lon,lat=map(float,fields[3:5])
        if abs(actual-jd)*86400>.001: raise ValueError('Wrong epoch')
        if not all(math.isfinite(v) for v in (actual,lon,lat)) or not 0<=lon<360 or not -90<=lat<=90:
            raise ValueError('Invalid numerical result')
        result[jd]=lon
    return result


def sample(lib,dt):
    return calculate(lib,dt.strftime('%Y-%m-%d'),dt.strftime('%H:%M:%S'),'UTC',25.033,121.5654,precision='exact')


def speed_at(lib,dt,name):
    s=sample(lib,dt)
    if s.get('status')!='candidate_calculated': raise ValueError('Unexpected calculation status')
    return s,next(p for p in s['chart']['planets'] if p['name']==name)


def engine_station(lib,name,start,end):
    """Native root selects challenging test inputs; JPL independently checks them."""
    lo=datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    hi=datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    a=speed_at(lib,lo,name)[1]['longitude_speed']
    b=speed_at(lib,hi,name)[1]['longitude_speed']
    if a*b>=0: raise ValueError('Native station not bracketed')
    while (hi-lo).total_seconds()>1:
        mid=lo+timedelta(seconds=int((hi-lo).total_seconds()/2))
        v=speed_at(lib,mid,name)[1]['longitude_speed']
        if a*v<=0: hi=mid
        else: lo=mid;a=v
    return hi


def run(library,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    tasks=[];stations=[]
    for date in ('1900-01-01T12:00:00','1945-08-15T12:00:00','1979-07-01T12:00:00',
                 '2001-06-15T04:34:56','2024-03-20T03:00:00','2024-06-21T02:00:00','2026-11-01T12:00:00'):
        dt=datetime.fromisoformat(date).replace(tzinfo=timezone.utc);s=sample(library,dt)
        if s.get('status')!='candidate_calculated':raise ValueError('Sample rejected')
        for p in s['chart']['planets']:
            tasks.append(dict(id=date+'_'+p['name'],kind='grid',utc=dt.isoformat(),jd_tt=s['provenance']['jd_tt'],planet=p))
    for name,start,end in (('Mercury','2024-04-01','2024-04-03'),('Venus','2025-03-01','2025-03-03'),('Mars','2024-12-06','2024-12-08')):
        root=engine_station(library,name,start,end)
        stations.append(dict(name=name,native_root_utc=root.isoformat(),selection='Engine-selected challenge input, not an independently certified station time'))
        for hours in (-6,0,6):
            dt=root+timedelta(hours=hours);s,p=speed_at(library,dt,name)
            tasks.append(dict(id=name+'_station_'+str(hours),kind='station',utc=dt.isoformat(),hours_from_native_root=hours,jd_tt=s['provenance']['jd_tt'],planet=p))
    (folder/'inputs.json').write_text(json.dumps(dict(stations=stations,tasks=tasks),indent=2)+'\n')
    evidence={};requests=[]
    # One request per body with all seven-point stencils; no parallel API calls.
    for name,target in TARGETS.items():
        epochs=sorted({t['jd_tt']+seconds/86400 for t in tasks if t['planet']['name']==name for seconds in OFFSETS})
        # Retain an already verified full response; new queries are bounded to
        # 21 epochs to avoid repeatedly resubmitting a large failing request.
        full=folder/(name+'.json')
        if full.exists():
            raw=full.read_text();evidence[name]=parse(raw,target,epochs)
            requests.append(dict(name=name,url=request_url(target,epochs),cache_file=full.name,sha256=hashlib.sha256(raw.encode()).hexdigest(),epochs=len(epochs),source='previous full request cached in this run'))
            print(json.dumps(dict(body=name,epochs=len(epochs),cached=True)),flush=True)
            continue
        evidence[name]={}
        for start in range(0,len(epochs),21):
            subset=epochs[start:start+21]
            url=request_url(target,subset)
            p=folder/(name+'_'+str(start//21)+'.json')
            raw=p.read_text() if p.exists() else urlopen(url,timeout=45).read().decode()
            p.write_text(raw)
            evidence[name].update(parse(raw,target,subset))
            requests.append(dict(name=name,url=url,cache_file=p.name,sha256=hashlib.sha256(raw.encode()).hexdigest(),epochs=len(subset)))
            print(json.dumps(dict(body=name,batch=start//21,epochs=len(subset),retrieved=True)),flush=True)
    rows=[]
    for t in tasks:
        p=t['planet'];jd=t['jd_tt']
        values={seconds:evidence[p['name']][jd+seconds/86400] for seconds in OFFSETS}
        v=derivative(values,600);fine=derivative(values,300)
        err=abs(p['longitude_speed']-v)*3600
        stability=abs(v-fine)*3600
        guard=max(SIGN_GUARD_ARCSEC_DAY,stability)
        sign='near_station_unresolved' if abs(v)*3600<=guard else 'retrograde' if v<0 else 'direct'
        flag_consistent=p['retrograde']==(p['longitude_speed']<0)
        sign_matches=None if sign=='near_station_unresolved' else p['retrograde']==(v<0)
        passed=err<=TOLERANCE_ARCSEC_DAY and stability<=STENCIL_STABILITY_ARCSEC_DAY and flag_consistent and sign_matches is not False
        rows.append(dict(id=t['id'],kind=t['kind'],utc=t['utc'],name=p['name'],native_speed_deg_day=p['longitude_speed'],jpl_finite_difference_deg_day=v,
                         error_arcsec_day=err,stencil_disagreement_arcsec_day=stability,reference_direction=sign,sign_matches=sign_matches,
                         native_flag_consistent=flag_consistent,pass_=passed,hours_from_native_root=t.get('hours_from_native_root')))
    summary=dict(status='pass_for_tested_samples' if all(r['pass_'] for r in rows) else 'review',cases=len(rows),passed=sum(r['pass_'] for r in rows),
                 tolerance_arcsec_day=TOLERANCE_ARCSEC_DAY,stencil_stability_limit_arcsec_day=STENCIL_STABILITY_ARCSEC_DAY,sign_guard_arcsec_day=SIGN_GUARD_ARCSEC_DAY,
                 max_error_arcsec_day=max(r['error_arcsec_day'] for r in rows),max_stencil_disagreement_arcsec_day=max(r['stencil_disagreement_arcsec_day'] for r in rows),
                 unresolved_direction_cases=sum(r['reference_direction']=='near_station_unresolved' for r in rows),stations=stations,requests=requests,rows=rows,
                 independence='NASA/JPL apparent ecliptic-of-date TT positions differentiated with 300s/600s fourth-order stencils; shared TT epochs; not historical civil-time certification',
                 production_ready_changed=False)
    (folder/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('requests','rows','stations')}),flush=True)
    return summary


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--library',default='build/libswe.so');a.add_argument('--output',default='speed_acceptance_20261102');args=a.parse_args()
    r=run(str(Path(args.library).resolve()),args.output)
    raise SystemExit(0 if r['status']=='pass_for_tested_samples' else 1)
