import asyncio,base64,io,threading,types,copy,time,json
from unittest.mock import patch
from PIL import Image
import live_backend as lb
from contracts import AssistRequest,deny

buf=io.BytesIO();Image.new('RGB',(32,24)).save(buf,format='JPEG')
request=AssistRequest(query='Can I draw this here?',image_jpeg_base64=base64.b64encode(buf.getvalue()).decode())

# Independent server instances each own their local semaphore, sharing one
# external window store. Both read one remaining call before either writes.
store={'active':{'id':'fixture-window','expires_at':9e9,'calls_used':0,'max_calls':1}}
barrier=threading.Barrier(2);paid=[]
class FakeStore:
 def get(self,key):
  value=copy.deepcopy(store.get(key))
  if key=='active':barrier.wait(timeout=2)
  return value
 def put(self,key,value):store[key]=copy.deepcopy(value)
fake=types.SimpleNamespace(Dict=types.SimpleNamespace(from_name=lambda *a,**kw:FakeStore()))
async def race():
 with patch.dict('sys.modules',{'modal':fake}),patch.object(lb.client,'retrieve',return_value={'chunks':[{'id':'c'}]}),patch.object(lb,'segment_paper',side_effect=lambda *a,**k:(paid.append(1) or {'masks':[]})):
  results=await asyncio.gather(lb.LiveAssistService().assist(request),lb.LiveAssistService().assist(request))
  print(json.dumps({'case':'shared_window_race','max_calls':1,'provider_invocations':len(paid),'recorded_calls_used':store['active']['calls_used'],'http_statuses':[r[0] for r in results]}))
asyncio.run(race())

# wait_for cancels to_thread's Future, not the running thread. Slots become
# available while the old worker can still reach later paid stages.
active=0;peak=0;lock=threading.Lock();release=threading.Event()
service=lb.LiveAssistService(limits=lb.LiveLimits(timeout_seconds=.03,queue_seconds=.01,breaker_failures=10))
def work(req):
 global active,peak
 with lock:active+=1;peak=max(peak,active)
 release.wait(timeout=.2)
 with lock:active-=1
 return deny('fixture')
service.compose=work
async def timeout_case():
 a=await service.assist(request)
 b=await service.assist(request)
 print(json.dumps({'case':'timeout_releases_worker_slot','configured_concurrency':1,'peak_running_workers':peak,'http_statuses':[a[0],b[0]]}))
 release.set()
asyncio.run(timeout_case())
