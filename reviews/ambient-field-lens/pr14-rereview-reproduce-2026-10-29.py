import asyncio, copy, json, threading
from unittest.mock import patch
import live_backend as lb
from test_live_backend import request_with_image, EVIDENCE, WINDOW

# Cancellation during retrieval releases the slot and never sets stage guard.
async def cancelled():
    entered=threading.Event(); release=threading.Event(); stages=[]
    def retrieve(*args):
        entered.set(); release.wait(2); return EVIDENCE
    def segment(*args,**kwargs):
        stages.append('segment_after_cancel'); return {'masks': []}
    svc=lb.LiveAssistService(limits=lb.LiveLimits(timeout_seconds=5))
    with patch.object(lb,'read_window',return_value=WINDOW), patch.object(lb,'claim_call',return_value='w1'), patch.object(lb.client,'retrieve',side_effect=retrieve), patch.object(lb,'segment_paper',side_effect=segment), patch.object(lb,'note_progress'), patch.object(lb,'note_failure'):
        task=asyncio.create_task(svc.assist(request_with_image()))
        while not entered.is_set(): await asyncio.sleep(.005)
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass
        released=not svc.slots.locked()
        release.set()
        await asyncio.sleep(.1)
        print(json.dumps({'case':'cancelled_request','slot_released_while_worker_running':released,'stages':stages}))
asyncio.run(cancelled())

# Active is closed after admission read, before atomic token consumption.
class Closed:
    def __init__(self): self.active=dict(WINDOW); self.token=True
    def get(self,key): return copy.deepcopy(self.active)
    def pop(self,key): self.active=None; self.token=False; return True
    def put(self,key,val): self.active=copy.deepcopy(val)
s=Closed()
with patch.object(lb,'_store',return_value=s):
    wid=lb.claim_call(dict(WINDOW))
    print(json.dumps({'case':'closed_during_claim','admitted_window':wid,'active_after':s.active}))

# Best-effort statistics put can resurrect a window closed after the read.
class Resurrect(Closed):
    def pop(self,key): self.token=False; return True
    def get(self,key):
        value=copy.deepcopy(self.active)
        if not self.token: self.active=None
        return value
s=Resurrect()
with patch.object(lb,'_store',return_value=s):
    wid=lb.claim_call(dict(WINDOW))
    print(json.dumps({'case':'closed_window_resurrected','admitted_window':wid,'active_after':s.active}))
