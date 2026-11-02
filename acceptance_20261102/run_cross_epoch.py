# SPDX-License-Identifier: AGPL-3.0-only
"""Synthetic multi-epoch acceptance; does not change production settings.
Run from repository root: PYTHONPATH=vendor:. python acceptance_20261102/run_cross_epoch.py
JPL requests are serial. A network/schema failure stops the remaining requests.
"""
import json,hashlib
from pathlib import Path
from calculate_candidate import calculate
from verify_horizons import compare
ROOT=Path('acceptance_20261102')
CASES=[('range_start','1900-01-01','12:00:00','Etc/UTC',0,0),('mid_century','1945-08-15','12:00:00','Etc/UTC',35,139),('taipei_dst','1979-07-01','12:00:00','Asia/Taipei',25.033,121.5654),('modern_south','2024-06-21','12:00:00','Australia/Sydney',-33.8688,151.2093),('range_end','2099-12-31','12:00:00','Etc/UTC',0,0)]
rows=[]
for name,date,time,zone,lat,lon in CASES:
 p=ROOT/name;p.mkdir(parents=True,exist_ok=True)
 sample=calculate(str(Path('build/libswe.so').resolve()),date,time,zone,lat,lon,precision='exact')
 (p/'sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2)+'\n')
 if sample['status']!='candidate_calculated':raise RuntimeError(name+': unexpected calculation status')
 result=compare(str(p/'sample.json'),str(p/'jpl'))
 row={'id':name,'utc':sample['input']['selected']['utc'],'status':result['status'],'rows':len(result['rows']),'review_bodies':[r['name'] for r in result['rows'] if r['status']!='pass']}
 rows.append(row)
 hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((p/'jpl').glob('*.json')) if f.name!='response_sha256.json'}
 (p/'jpl/response_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
 print(json.dumps(row),flush=True)
 if any('error' in r for r in result['rows']):break
summary={'synthetic_only':True,'production_ready_changed':False,'cases_completed':len(rows),'all_requested_epochs_passed':len(rows)==len(CASES) and all(r['status']=='pass_for_sample_only' for r in rows),'cases':rows}
(ROOT/'cross_epoch_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
