"""UAES bounded autonomous daemon for local allowlisted work only."""
import argparse,json,os,signal,sqlite3,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from src.job_runner import JobRunner

class Daemon:
 def __init__(self,db,agent,mandate,interval=5):
  self.db,self.agent,self.mandate,self.interval=db,agent,mandate,interval
  self.stop_event=threading.Event()
  self.stats={"ticks":0,"completed":0,"failures":0,"last_error":None}
 def once(self):
  runner=JobRunner(self.db)
  try:
   result=runner.run_once(self.agent,self.mandate)
   self.stats["ticks"]+=1
   if result:self.stats["completed"]+=1
   return result
  except (sqlite3.Error,ValueError,PermissionError) as exc:
   self.stats["failures"]+=1
   self.stats["last_error"]=type(exc).__name__
   return None
  finally:runner.close()
 def serve(self,max_iterations=None):
  n=0
  while not self.stop_event.is_set() and (max_iterations is None or n<max_iterations):
   self.once();n+=1
   self.stop_event.wait(self.interval)
  return dict(self.stats)

def health_server(daemon,bind="127.0.0.1",port=8080):
 class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
   if self.path not in ("/healthz","/readyz"):
    self.send_error(404);return
   good=not daemon.stop_event.is_set() and bool(daemon.agent and daemon.mandate)
   status=200 if good else 503
   data=json.dumps({"ok":good,"mode":"local-only","stats":daemon.stats}).encode()
   self.send_response(status);self.send_header("Content-Type","application/json")
   self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
  def log_message(self,*args):pass
 server=ThreadingHTTPServer((bind,port),Handler)
 thread=threading.Thread(target=server.serve_forever,daemon=True)
 thread.start()
 return server

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--db",default=os.environ.get("UAES_DB","/data/uaes.sqlite"))
 p.add_argument("--agent",default=os.environ.get("UAES_AGENT_ID"))
 p.add_argument("--mandate",default=os.environ.get("UAES_MANDATE_ID"))
 p.add_argument("--interval",type=float,default=5)
 p.add_argument("--max-iterations",type=int,default=None)
 a=p.parse_args()
 if not a.agent or not a.mandate:raise SystemExit("configured agent and mandate required; cannot invent runtime identity")
 daemon=Daemon(a.db,a.agent,a.mandate,a.interval)
 server=health_server(daemon)
 try:
  signal.signal(signal.SIGTERM,lambda *_:daemon.stop_event.set())
  signal.signal(signal.SIGINT,lambda *_:daemon.stop_event.set())
  print(json.dumps({"status":"STARTING","mode":"local-only"}),flush=True)
  print(json.dumps(daemon.serve(a.max_iterations)),flush=True)
 finally:server.shutdown();server.server_close()

if __name__=="__main__":main()
