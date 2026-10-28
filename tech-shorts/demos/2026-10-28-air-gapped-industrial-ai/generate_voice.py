#!/usr/bin/env python3
import os
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
import soundfile as sf
from kokoro import KPipeline
root=Path.home()/'flotilla/tech-shorts/assets/2026-10-28-yc-air-gapped-industrial-ai'
approved=(Path(__file__).parent/'script-approved.md').read_text()
paragraphs=[p.strip() for p in approved.split('\n\n') if p.strip() and not p.startswith(('#','Approved','['))]
assert paragraphs[0]=='Life is about stories, and we have always used stories to transmit knowledge.'
parts=[{'id':i,'text':p} for i,p in enumerate(paragraphs)]
(root/'audio').mkdir(parents=True,exist_ok=True)
(root/'narration-plan.json').write_text(json.dumps(parts,indent=2,ensure_ascii=False)+'\n')
pipeline=KPipeline(lang_code='a',repo_id='hexgrad/Kokoro-82M')
all_audio=[];time=0
for part in parts:
 target=root/'audio'/f"paragraph-{part['id']:02}.wav"
 cache=target.with_suffix('.json');digest=hashlib.sha256((part['text']+'|af_bella|1.04').encode()).hexdigest()
 if target.exists() and cache.exists() and json.loads(cache.read_text()).get('sha256')==digest:
  audio,sr=sf.read(target);assert sr==24000
 else:
  chunks=[]
  for _,_,a in pipeline(part['text'],voice='af_bella',speed=1.04,split_pattern=r'(?<=[.!?])\s+'):
   if a is not None and len(a):chunks.extend([np.asarray(a,dtype=np.float32),np.zeros(int(24000*.14),dtype=np.float32)])
  audio=np.concatenate(chunks);audio=np.concatenate([audio,np.zeros(int(24000*.16),dtype=np.float32)])
  sf.write(target,audio,24000)
  cache.write_text(json.dumps({'sha256':digest,'voice':'af_bella','speed':1.04}))
 part['start']=round(time,6);part['duration']=len(audio)/24000;time+=part['duration'];part['end']=round(time,6)
 all_audio.append(audio)
 print(part['id'],round(part['duration'],2),part['text'][:65],flush=True)
sf.write(root/'audio/narration-raw.wav',np.concatenate(all_audio),24000)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(root/'audio/narration-raw.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','48000','-ac','2',str(root/'audio/narration.wav')],check=True)
(root/'narration-timing.json').write_text(json.dumps({'voice':'af_bella','engine':'Kokoro-82M, cached offline','speed':1.04,'duration':time,'parts':parts},indent=2,ensure_ascii=False)+'\n')
print('TOTAL',time,flush=True)
