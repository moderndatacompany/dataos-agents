import http.server,json,os,subprocess,pathlib
ROOT=pathlib.Path('/etc/dataos/work/project').resolve()
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_POST(self):
  try:
   n=int(self.headers.get('Content-Length','0'))
   if self.path!='/run' or n>65536: raise ValueError('Invalid tool request')
   d=json.loads(self.rfile.read(n)); args=d.get('args',[])
   if not isinstance(args,list) or not all(isinstance(a,str) for a in args): raise ValueError('Invalid arguments')
   cwd=pathlib.Path(d.get('cwd',str(ROOT))).resolve()
   if cwd!=ROOT and ROOT not in cwd.parents: raise ValueError('Working directory must be in the product repository')
   r=subprocess.run(['/opt/venv/bin/vulcan',*args],cwd=cwd,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=600)
   result={'code':r.returncode,'stdout':r.stdout[-2000000:],'stderr':r.stderr[-2000000:]}
   for k,v in os.environ.items():
    if len(v)>8 and any(x in k.upper() for x in ('TOKEN','APIKEY','PASSWORD','API_KEY')):
     for f in ('stdout','stderr'): result[f]=result[f].replace(v,'[credential withheld]')
   body=json.dumps(result).encode();self.send_response(200)
  except Exception as e:
   body=json.dumps({'code':1,'stdout':'','stderr':type(e).__name__+': '+str(e)}).encode();self.send_response(400)
  self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
http.server.ThreadingHTTPServer(('127.0.0.1',9173),Handler).serve_forever()
