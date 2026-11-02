# SPDX-License-Identifier: AGPL-3.0-only
"""Single-process natal HTTP service; source offer has no auth wall.
No request bodies, names, tokens, or birth data are logged or persisted.
Candidate by default; stable mode is an explicit, scoped release setting.
"""
import hmac,json,os
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from calculate_candidate import calculate

ROOT=Path(__file__).resolve().parent
ALLOWED={'date','time','timezone','latitude','longitude','precision','fold'}
REQUIRED=ALLOWED-{'fold'}

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup();self.connection.settimeout(10)
    def log_message(self,*args):pass
    def reply(self,status,value):
        body=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
        self.send_header('Link','</source>; rel="service-desc"');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path=='/health':return self.reply(200,{'status':self.server.release_stage,'production_ready':self.server.release_stage=='stable','release_version':'1.0.0' if self.server.release_stage=='stable' else None,'source_url':'/source'})
        if self.path=='/license':return self.reply(200,{'license':'AGPL-3.0-only','source_url':'/source','publisher':'洪聖添','notice':'No warranty. Third-party notices retained.'})
        if self.path=='/source':
            archive=self.server.source_archive
            if not archive.is_file():return self.reply(503,{'code':'SOURCE_ARCHIVE_UNAVAILABLE'})
            body=archive.read_bytes();self.send_response(200)
            self.send_header('Content-Type','application/gzip');self.send_header('Content-Length',str(len(body)))
            self.send_header('Content-Disposition','attachment; filename="hongjia-western-source.tar.gz"')
            self.end_headers();return self.wfile.write(body)
        self.reply(404,{'code':'NOT_FOUND'})
    def do_POST(self):
        if self.path!='/v1/astrology/natal':return self.reply(404,{'code':'NOT_FOUND'})
        expected='Bearer '+self.server.api_key
        if not hmac.compare_digest(self.headers.get('Authorization','').encode(),expected.encode()):
            return self.reply(401,{'code':'UNAUTHORIZED'})
        lengths=self.headers.get_all('Content-Length',[])
        if self.headers.get('Transfer-Encoding') or len(lengths)!=1:
            self.close_connection=True;return self.reply(400,{'code':'CONTENT_LENGTH_REQUIRED'})
        try:length=int(lengths[0])
        except ValueError:return self.reply(400,{'code':'CONTENT_LENGTH_INVALID'})
        if not 0<length<=4096:
            self.close_connection=True;return self.reply(413,{'code':'BODY_TOO_LARGE'})
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
            self.close_connection=True;return self.reply(415,{'code':'JSON_REQUIRED'})
        try:
            def pairs(items):
                d={}
                for k,v in items:
                    if k in d:raise ValueError('duplicate key')
                    d[k]=v
                return d
            def bad_constant(v):raise ValueError('nonfinite JSON')
            data=json.loads(self.rfile.read(length),object_pairs_hook=pairs,parse_constant=bad_constant)
        except (ValueError,UnicodeError):return self.reply(400,{'code':'JSON_INVALID'})
        if not isinstance(data,dict) or set(data)-ALLOWED or not REQUIRED<=set(data):
            return self.reply(422,{'code':'REQUEST_FIELDS_INVALID','chart':None})
        if any(not isinstance(data[k],str) for k in ('date','timezone','precision')) or (data['time'] is not None and not isinstance(data['time'],str)):
            return self.reply(422,{'code':'REQUEST_TYPES_INVALID','chart':None})
        try:
            result=calculate(self.server.library,data['date'],data['time'],data['timezone'],data['latitude'],data['longitude'],precision=data['precision'],fold=data.get('fold'))
        except Exception:
            return self.reply(503,{'code':'ENGINE_UNAVAILABLE','chart':None})
        success=result['status']=='candidate_calculated'
        if success and self.server.release_stage=='stable':
            result.update(status='calculated',production_ready=True,release_version='1.0.0',release_scope='small_scale_natal_service')
        result['source_url']='/source'
        self.reply(200 if success else 422,result)


def create_server(address,library,source_archive,api_key,release_stage='candidate'):
    if release_stage not in ('candidate','stable'):raise ValueError('Invalid release stage')
    if not isinstance(api_key,str) or len(api_key)<32:raise ValueError('Set a dedicated random API key with at least 32 characters')
    if not Path(library).is_file() or not Path(source_archive).is_file():raise ValueError('Build native library and corresponding source archive first')
    server=HTTPServer(address,Handler) # Deliberately serial: shared native state.
    server.release_stage=release_stage
    server.library=str(library);server.source_archive=Path(source_archive);server.api_key=api_key
    return server

if __name__=='__main__':
    create_server((os.environ.get('HOST','127.0.0.1'),int(os.environ.get('PORT','8080'))),ROOT/'build/libswe.so',ROOT/'dist/source.tar.gz',os.environ.get('WESTERN_API_KEY',''),os.environ.get('WESTERN_RELEASE_STAGE','candidate')).serve_forever()
