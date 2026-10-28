#!/usr/bin/env python3
"""V2: real Sovereign Mind interactions; Canis only for its disposition panel."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
import build_demo as b

ROOT=b.ROOT
OUT=ROOT/'v2'
FPS=b.FPS


def device(background,source,offset,frames,out,available=None,crop=(0,110,1290,2600),width=480,x=1330,y=55):
    cx,cy,cw,ch=crop
    height=round(ch*width/cw/2)*2
    seconds=frames/FPS;live=seconds if available is None else min(seconds,available)
    graph=(f'[0:v]scale=1920:1080,fps=30,setsar=1[bg];'
      f'[1:v]crop={cw}:{ch}:{cx}:{cy},scale={width}:{height}:flags=lanczos,setsar=1,fps=30,'
      f'trim=duration={live},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={max(0,seconds-live)+.1}[phone];'
      f'[bg][phone]overlay={x}:{y}:shortest=1[out]')
    b.run(['-loop','1','-i',background,'-ss',offset,'-i',source,'-filter_complex',graph,
      '-map','[out]','-frames:v',frames,'-an']+b.ENC+[out])


def build():
    (OUT/'segments').mkdir(parents=True,exist_ok=True)
    g=b.make_graphics();src=ROOT/'sources'
    g['models-v2']=b.save(b.base('Model choice / knowledge packs / roles','Models, knowledge,\nand personas.',
      ['Curated knowledge on the device.','Choose the model and the role.']),'v2-models.png')
    g['languages-v2']=b.save(b.base('Sovereign Mind / conversation history','Your knowledge.\nYour language.',
      ['Return to earlier conversations.','English, German and Spanish interactions.']),'v2-languages.png')
    g['wiki-v2']=b.save(b.base('Reviewed knowledge / on the device','Knowledge you\ncan inspect.',
      ['Browse the Wiki in the field.','Technical text and supplier drawings.']),'v2-wiki.png')
    g['abrasives-v2']=b.save(b.base('Industrial pilot / abrasives','Technical knowledge,\nincluding drawings.',
      ['An active distributor pilot.','Supplier catalogs become usable knowledge.']),'v2-abrasives.png')
    g['camera-v2']=b.save(b.base('Camera / photo / OCR','Bring what you see\ninto the question.',
      ['Photograph machine information.','Read the extracted text.','Bring it into the local conversation.']),'v2-camera.png')
    timing=json.loads((ROOT/'narration-timing.json').read_text());p=timing['parts']
    old=json.loads((ROOT/'timeline.json').read_text());timeline=[]
    def at(i):return p[i]['start']
    def end(i):return p[i]['end']
    def add(label,start,stop,kind,**kw):
        first,last=round(start*FPS),round(stop*FPS)
        if timeline:assert first==timeline[-1]['end_frame'],(label,first,timeline[-1]['end_frame'])
        timeline.append(dict(label=label,kind=kind,start_frame=first,end_frame=last,frames=last-first,start=first/FPS,end=last/FPS,**kw))
    def reuse(i,label=None):
        s=old[i];add(label or s['label'],s['start'],s['end'],'reuse',path=s['output'],provenance='Canis disposition' if i==11 else 'Existing historical/diagram/SM-backend graphic')
    def phone(label,start,stop,source,offset,image,**kw):
        add(label,start,stop,'device',source=str(src/source),offset=offset,image=str(image),provenance='User-supplied Sovereign Mind screen recording',**kw)
    for i in range(4):reuse(i)
    phone('Sovereign Mind: asking a technical question',at(2),19.3,'sm-chat-multilingual.MP4',.2,g['converse'])
    phone('Sovereign Mind: answer arrives',19.3,end(2),'sm-chat-multilingual.MP4',10.8,g['converse'])
    phone('Sovereign Mind: technical answer with sources',at(3),end(3),'sm-chat-multilingual.MP4',12.565,g['field'])
    phone('Knowledge packs, local models and personas',at(4),34.85,'sm-settings.MP4',1.5,g['models-v2'])
    phone('Abrasives Wiki: technical text and diagrams',34.85,end(4),'sm-abrasives-wiki.MP4',6.,g['local'])
    phone('Sovereign Mind: chat history',at(5),45.1,'sm-chat-multilingual.MP4',29.1,g['offline'])
    phone('Sovereign Mind: German-language question',45.1,49.2,'sm-chat-multilingual.MP4',33.1,g['languages-v2'])
    phone('Sovereign Mind: Spanish-language answer',49.2,end(5),'sm-chat-multilingual.MP4',37.4,g['languages-v2'])
    reuse(9)
    phone('Sovereign Mind: answer feedback controls',at(7),62.655,'sm-chat-multilingual.MP4',34.,g['feedback-user'])
    reuse(11,'Canis only: actual model disposition readout')
    reuse(12);reuse(13);reuse(14)
    phone('Reviewed Wiki available on the device',94.2,end(9),'sm-abrasives-wiki.MP4',.5,g['wiki-v2'])
    phone('Sovereign Mind: calibration question before camera use',at(10),end(10),'sm-camera-ocr.mov',14.3,g['converse'])
    phone('Multiple models and role-specific personas',at(11),109.4,'sm-settings.MP4',4.,g['models-v2'])
    # Camera word in the UNCHANGED narration:113.1675s. Camera footage starts
    #112.7s; extracted text is visible while “read available text” is spoken.
    phone('Camera sequence: question and answer lead-in',109.4,110.4,'sm-camera-ocr.mov',23.8,g['camera-v2'])
    phone('Camera sequence: choose Take Photo',110.4,112.7,'sm-camera-ocr.mov',25.,g['camera-v2'])
    phone('Camera view of the machine log',112.7,114.65,'sm-camera-ocr.mov',34.8,g['camera-v2'])
    phone('OCR: photo and extracted text',114.65,115.5,'sm-camera-ocr.mov',38.65,g['camera-v2'])
    phone('OCR: readable extracted-text detail',115.5,end(11),'sm-camera-ocr.mov',39.,g['camera-v2'],
      available=1.9,crop=(0,1100,1290,1600),width=740,x=1090,y=90)
    phone('Industrial abrasives pilot: real Wiki diagrams',at(12),124.73,'sm-abrasives-wiki.MP4',6.45,g['abrasives-v2'])
    add('Equipment-manufacturer discussions',124.73,end(12),'still',image=str(g['pilot']))
    reuse(21);reuse(22)
    assert timeline[-1]['end_frame']==4467
    canis=[s for s in timeline if s.get('provenance')=='Canis disposition']
    assert len(canis)==1 and canis[0]['start']>=62 and canis[0]['end']<=70
    for i,s in enumerate(timeline):
        fingerprint=hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest()[:10]
        s['output']=s['path'] if s['kind']=='reuse' else str(OUT/'segments'/f'{i:02}-{fingerprint}.mp4')
    (OUT/'timeline.json').write_text(json.dumps(timeline,indent=2,ensure_ascii=False)+'\n')
    for i,s in enumerate(timeline):
        out=Path(s['output'])
        if out.exists():continue
        print(f'Render {i+1}/{len(timeline)}: {s["label"]}',flush=True)
        if s['kind']=='still':b.clip_still(s['image'],s['frames'],out)
        elif s['kind']=='device':device(s['image'],s['source'],s['offset'],s['frames'],out,
          s.get('available'),tuple(s.get('crop',(0,110,1290,2600))),s.get('width',480),s.get('x',1330),s.get('y',55))
    concat=OUT/'segments/concat.txt';concat.write_text(''.join("file '"+s['output'].replace("'","'\\''")+"'\n" for s in timeline))
    picture=OUT/'picture.mp4';b.run(['-f','concat','-safe','0','-i',concat,'-c','copy',picture])
    # Copy the approved V1 AAC track without regeneration or re-encoding.
    final=OUT/'Air-Gapped-Industrial-AI-Demo-v2.mp4'
    b.run(['-i',picture,'-i',ROOT/'Air-Gapped-Industrial-AI-Demo-v1.mp4','-map','0:v','-map','1:a:0',
      '-c','copy','-t',timeline[-1]['end'],'-movflags','+faststart',final])
    for ext in ['srt','vtt']:
        shutil.copy2(ROOT/f'Air-Gapped-Industrial-AI-Demo-v1.en.{ext}',OUT/f'Air-Gapped-Industrial-AI-Demo-v2.en.{ext}')
    print('COMPLETE',final,flush=True)

if __name__=='__main__':build()
