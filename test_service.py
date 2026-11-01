# SPDX-License-Identifier: AGPL-3.0-only
import http.client,json,secrets,threading,unittest,tarfile,io
from pathlib import Path
from service import create_server

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=secrets.token_hex(32)
        cls.server=create_server(('127.0.0.1',0),Path('build/libswe.so').resolve(),Path('dist/source.tar.gz').resolve(),cls.key)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def call(self,body=None,auth=True,path='/v1/astrology/natal',raw=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        h={'Content-Type':'application/json'}
        if auth:h['Authorization']='Bearer '+self.key
        c.request('POST' if body is not None or raw is not None else 'GET',path,body=raw if raw is not None else json.dumps(body) if body is not None else None,headers=h)
        r=c.getresponse();b=r.read();status=r.status;c.close();return status,b
    def payload(self):return dict(date='2001-06-15',time='12:34:56',timezone='Asia/Taipei',latitude=25.033,longitude=121.5654,precision='exact')
    def test_source_offer_without_auth(self):
        status,b=self.call(path='/source.tar.gz',auth=False);self.assertEqual(status,200)
        with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
            self.assertIn('hongjia-western/service.py',t.getnames())
            self.assertIn('hongjia-western/third_party/swisseph/sweph.c',t.getnames())
            self.assertIn('hongjia-western/LICENSE',t.getnames())
    def test_auth_required(self):self.assertEqual(self.call(self.payload(),auth=False)[0],401)
    def test_actual_chart_over_http(self):
        status,b=self.call(self.payload());d=json.loads(b)
        self.assertEqual(status,200);self.assertEqual(len(d['chart']['planets']),10)
        self.assertFalse(d['production_ready']);self.assertEqual(d['source_url'],'/source.tar.gz')
    def test_unknown_time(self):
        d=self.payload();d.update(time=None,precision='unknown');status,b=self.call(d)
        self.assertEqual(status,422);self.assertIsNone(json.loads(b)['chart'])
    def test_extra_private_field_rejected(self):
        d=self.payload();d['name']='synthetic';self.assertEqual(self.call(d)[0],422)
    def test_malformed_duplicate_or_nonfinite(self):
        for raw in ('{','{"date":1,"date":2}','{"latitude":NaN}'):
            self.assertEqual(self.call(raw=raw)[0],400)
    def test_input_wrong_type(self):
        d=self.payload();d['date']=[];self.assertEqual(self.call(d)[0],422)
    def test_body_limit(self):self.assertEqual(self.call(raw='x'*4097)[0],413)
