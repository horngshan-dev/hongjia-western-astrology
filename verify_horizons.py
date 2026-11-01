# SPDX-License-Identifier: AGPL-3.0-only
"""Independent JPL comparison. Network required; no passed result on errors.
Run from this directory: python verify_horizons.py
Horizons quantity 31: apparent ecliptic-of-date longitude/latitude.
Tolerance is an engineering acceptance threshold, not claimed engine accuracy.
"""
import json, pathlib, urllib.request, urllib.parse, re, math
from datetime import datetime, timezone

TARGETS = dict(Sun='10', Moon='301', Mercury='199', Venus='299', Mars='499',
               Jupiter='599', Saturn='699', Uranus='799', Neptune='899', Pluto='999')

def parse_response(raw, target, instant):
    data=json.loads(raw)
    signature=data.get('signature',{})
    if signature.get('source')!='NASA/JPL Horizons API' or signature.get('version')!='1.2':
        raise ValueError('Unreviewed API source/version')
    if data.get('error'):
        raise ValueError(data['error'])
    text=data.get('result','')
    if not re.search(r'Target body name:.*\('+re.escape(target)+r'\)',text):
        raise ValueError('Wrong target')
    if not re.search(r'Center body name: Earth \(399\)',text) or 'Center-site name: GEOCENTRIC' not in text:
        raise ValueError('Wrong observing center')
    if 'ObsEcLon' not in text or 'ObsEcLat' not in text:
        raise ValueError('Wrong quantities')
    lines=text.split('$$SOE')[1].split('$$EOE')[0].strip().splitlines()
    if len(lines)!=1:
        raise ValueError('Expected exactly one epoch')
    fields=[x.strip() for x in lines[0].split(',')]
    observed=datetime.strptime(fields[0],'%Y-%b-%d %H:%M:%S.%f').replace(tzinfo=timezone.utc)
    if observed!=instant:
        raise ValueError('Wrong epoch')
    if len(fields)!=6 or fields[-1]!='':
        raise ValueError('Unexpected columns')
    lon,lat=map(float,fields[3:5])
    if not math.isfinite(lon) or not math.isfinite(lat) or not 0<=lon<360 or not -90<=lat<=90:
        raise ValueError('Invalid coordinates')
    return lon,lat,signature

def compare(sample_path='calculated_sample.json', output='horizons_evidence'):
    sample=json.loads(pathlib.Path(sample_path).read_text())
    folder=pathlib.Path(output);folder.mkdir(exist_ok=True)
    instant=datetime.fromisoformat(sample['input']['selected']['utc']).astimezone(timezone.utc)
    # Observer TLIST defaults to UT. Use exact UTC Gregorian timestamp, not the
    # engine's internally estimated UT1, to avoid mixing time standards.
    stamp=instant.strftime('%Y-%m-%d %H:%M:%S')
    evidence={'status':'not_passed','utc':instant.isoformat(),'rows':[],
              'coordinate_note':'Compare apparent geocentric ecliptic-of-date positions. Frame/model differences remain; not an absolute-accuracy certification.'}
    for planet in sample['chart']['planets']:
        params=dict(format='json',COMMAND="'"+TARGETS[planet['name']]+"'",OBJ_DATA="'NO'",
                    MAKE_EPHEM="'YES'",EPHEM_TYPE="'OBSERVER'",CENTER="'500@399'",
                    TLIST="'"+stamp+"'",TIME_TYPE="'UT'",QUANTITIES="'31'",
                    CSV_FORMAT="'YES'",ANG_FORMAT="'DEG'")
        url='https://ssd.jpl.nasa.gov/api/horizons.api?'+urllib.parse.urlencode(params)
        row={'name':planet['name'],'request_url':url,'status':'not_passed'}
        try:
            cache=folder/(planet['name']+'.json')
            if cache.exists():
                raw=cache.read_text()
            else:
                raw=urllib.request.urlopen(url,timeout=45).read().decode()
                cache.write_text(raw)
            lon,lat,signature=parse_response(raw,TARGETS[planet['name']],instant)
            row['api_signature']=signature
            delta=abs((planet['longitude']-lon+180)%360-180)*3600
            latdelta=abs(planet['latitude']-lat)*3600
            tolerance=5.0 if planet['name']=='Moon' else 2.0
            row.update(longitude=lon,latitude=lat,longitude_error_arcsec=delta,
                       latitude_error_arcsec=latdelta,tolerance_arcsec=tolerance,
                       status='pass' if max(delta,latdelta)<=tolerance else 'review')
        except Exception as exc:
            row['error']=str(exc)
        evidence['rows'].append(row)
        (folder/'comparison.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
        if row['status']=='not_passed':
            break  # Stop on network/schema failure; do not hammer NASA.
    if len(evidence['rows'])==10 and all(x['status']=='pass' for x in evidence['rows']):
        evidence['status']='pass_for_sample_only'
    (folder/'comparison.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
    return evidence

if __name__=='__main__':
    print(json.dumps(compare(),ensure_ascii=False,indent=2))
