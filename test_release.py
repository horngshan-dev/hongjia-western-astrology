# SPDX-License-Identifier: AGPL-3.0-only
import http.client,json,secrets,threading,unittest
from pathlib import Path
from service import create_server
class ReleaseTests(unittest.TestCase):
 def test_stable_contract_and_failure_boundary(self):
  key=secrets.token_hex(32)
  server=create_server(('127.0.0.1',0),Path('build/libswe.so').resolve(),Path('dist/source.tar.gz').resolve(),key,'stable')
  t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
  def request(body=None):
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
   c.request('POST' if body else 'GET','/v1/astrology/natal' if body else '/health',json.dumps(body) if body else None,{'Content-Type':'application/json','Authorization':'Bearer '+key})
   r=c.getresponse();d=json.loads(r.read());c.close();return r.status,d
  try:
   status,health=request();self.assertEqual(status,200);self.assertTrue(health['production_ready'])
   p=dict(date='2001-06-15',time='12:34:56',timezone='Asia/Taipei',latitude=25.033,longitude=121.5654,precision='exact')
   status,d=request(p);self.assertEqual(status,200);self.assertEqual(d['status'],'calculated');self.assertTrue(d['production_ready']);self.assertEqual(d['release_version'],'1.0.0')
   self.assertAlmostEqual(d['chart']['planets'][0]['longitude'],84.14881185582166);self.assertEqual(len(d['chart']['house_cusps']),12)
   for updates,code in [({'time':None,'precision':'unknown'},'BIRTH_TIME_REFINEMENT_REQUIRED'),({'date':'2099-12-31'},'TIME_MODEL_OUTSIDE_VALIDATED_RANGE'),({'latitude':70},'PLACIDUS_UNAVAILABLE')]:
    status,d=request(dict(p,**updates));self.assertEqual(status,422);self.assertEqual(d['code'],code);self.assertIsNone(d['chart']);self.assertNotEqual(d.get('production_ready'),True)
  finally:server.shutdown();server.server_close();t.join()
