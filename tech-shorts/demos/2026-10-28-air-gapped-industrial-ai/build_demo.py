#!/usr/bin/env python3
"""First-cut YC product demo; cached offline narration and local media, no publishing."""
import argparse,hashlib,html,json,math,shutil,subprocess,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter

ROOT=Path.home()/'flotilla/tech-shorts/assets/2026-10-28-yc-air-gapped-industrial-ai'
HERE=Path(__file__).resolve().parent
W,H,FPS=1920,1080,30
BG='#101e29';FG='#f7f6ee';TEAL='#77e0c4';MUTED='#a5b7c1';PAPER='#f6f4ed';INK='#172a35';GOLD='#e8c58b'
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
SERIF='/System/Library/Fonts/Supplemental/Georgia.ttf'
ENC=['-c:v','h264_videotoolbox','-b:v','6500k','-pix_fmt','yuv420p']

def font(n,bold=False):return ImageFont.truetype(BOLD if bold else FONT,n)
def run(args):subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error']+list(map(str,args)),check=True)
def txt(d,xy,text,size=44,color=FG,width=40,bold=False,spacing=14):
    x,y=xy
    for para in text.split('\n'):
        for line in textwrap.wrap(para,width=width,break_long_words=False,break_on_hyphens=False) or ['']:
            d.text((x,y),line,font=font(size,bold),fill=color);y+=size+spacing
    return y

def base(kicker,title,lines=(),tag=None):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    d.line((105,82,260,82),fill=TEAL,width=5)
    txt(d,(105,118),kicker.upper(),25,TEAL,width=60,bold=True)
    y=txt(d,(105,230),title,76,width=23,bold=True,spacing=13)+45
    for line in lines:y=txt(d,(110,y),line,34,MUTED,width=41,spacing=11)+28
    if tag:txt(d,(110,985),tag,22,MUTED,width=80)
    return im

def save(im,name):
    p=ROOT/'graphics'/name;im.save(p);return p

def photo(src,title,credit,name,contain=False):
    im=Image.open(src).convert('RGB')
    if contain:
        canvas=Image.new('RGB',(W,H),PAPER);fit=ImageOps.contain(im,(1380,920));canvas.paste(fit,((W-fit.width)//2,35));im=canvas
    else:
        im=ImageOps.fit(im,(W,H),method=Image.Resampling.LANCZOS)
        shade=Image.new('RGB',(W,H),'black');im=Image.blend(im,shade,.20)
    d=ImageDraw.Draw(im)
    if title:
        d.rounded_rectangle((82,788,1345,948),radius=15,fill=BG)
        txt(d,(113,823),title,70,width=34,bold=True)
    d.rectangle((0,1019,W,H),fill=BG)
    txt(d,(42,1036),credit,19,MUTED,width=160)
    return save(im,name)

def screen(src,kicker,title,subtitle,name,crop=None):
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
    txt(d,(80,50),kicker.upper(),23,'#277d6a',width=90,bold=True)
    txt(d,(80,100),title,51,INK,width=65,bold=True)
    txt(d,(80,174),subtitle,26,'#526671',width=100)
    shot=Image.open(src).convert('RGB')
    if crop:shot=shot.crop(crop)
    shot=ImageOps.contain(shot,(1770,770),method=Image.Resampling.LANCZOS)
    im.paste(shot,((W-shot.width)//2,260+(770-shot.height)//2))
    return save(im,name)

def make_graphics():
    src=ROOT/'sources'
    g={}
    g['cave']=photo(src/'cave-painting.jpg','Life is about stories.','Altamira cave art · Photo: Daniel VILLAFRUELA · CC BY-SA 3.0 · resized/reframed','history-cave.png')
    g['trojan']=photo(src/'trojan-horse.jpg','How to outsmart an opponent.','Giovanni Domenico Tiepolo · The Procession of the Trojan Horse into Troy · Public domain','history-trojan.png')
    g['leonardo']=photo(src/'leonardo-aerial-screw.jpg','How to build a machine.','Leonardo da Vinci · Aerial screw, Manuscript B · Public domain','history-leonardo.png',contain=True)
    wiki=Image.open(src/'wikipedia-home.png').convert('RGB').crop((610,10,1320,620))
    im=Image.new('RGB',(W,H),'white');wiki=ImageOps.contain(wiki,(1090,990));im.paste(wiki,(775,30));d=ImageDraw.Draw(im)
    txt(d,(100,200),'KNOWLEDGE, ORGANIZED',24,'#277d6a',width=30,bold=True)
    txt(d,(100,310),'Available\nto everyone.',76,INK,width=19,bold=True)
    txt(d,(100,997),'Wikipedia home page · Wikimedia contributors / Foundation · CC BY-SA',20,'#526671',width=120)
    g['wikipedia']=save(im,'history-wikipedia.png')
    g['converse']=save(base('Knowledge becomes a conversation','Ask the knowledge.', ['A technician asks a question.','The answer carries its sources.']),'converse.png')
    g['feedback-user']=save(base('User feedback / human input','Learn from corrections.', ['Technicians flag unhelpful advice.','Human review keeps control.']),'feedback-user.png')
    g['disposition']=save(base('Model disposition / internal signals','Read more than\nthe answer.', ['Internal disposition signals.','Interactions worth reviewing.']),'disposition.png')
    g['field']=save(base('Industrial AI / on device','Where cloud AI\ncannot go.', ['Technical guidance on the device.','Knowledge stays within your perimeter.']),'field.png')
    g['local']=save(base('Your equipment / your expertise','Knowledge packs.\nLocal models.', ['Technical manuals and procedures.','Expertise for interpreting machine logs.']),'local-models.png')
    g['offline']=save(base('Inference / disconnected','Offline by design.', ['No per-query cloud inference fees.','No questions sent to an external AI API.','Your models. Your knowledge. Your deployment.']),'offline.png')
    g['knowledge']=screen(src/'console-knowledge.png','Customer premises / knowledge hub','From technical documents to local knowledge','Existing admin-console capture','console-knowledge.png')
    g['wiki']=screen(src/'console-wiki.png','Review / edit / approve','A Wiki that experts can review and edit','Human review before updated knowledge is deployed','console-wiki.png')
    g['wiki-detail']=screen(src/'console-wiki.png','Domain expertise / human control','Approve or modify the proposed changes','The reviewer controls what reaches technicians','console-wiki-detail.png',crop=(440,120,1530,1030))
    g['settings']=save(base('Model choice / knowledge packs','Your choice\nof models.', ['Open weights, running locally.','Knowledge packs for the task at hand.']),'settings.png')
    g['image']=save(base('Image input / local context','Bring what you see\ninto the question.', ['Read available text.','Add visual information to the interaction.'],tag='Recorded image-input interaction'),'image-input.png')
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
    txt(d,(110,95),'EARLY CUSTOMER VALIDATION',25,'#277d6a',width=70,bold=True)
    txt(d,(110,200),'Built for industrial service.',76,INK,width=36,bold=True)
    d.rounded_rectangle((110,390,930,880),radius=25,fill='white');d.rounded_rectangle((980,390,1800,880),radius=25,fill='white')
    txt(d,(160,445),'PILOT',24,'#277d6a',width=25,bold=True)
    txt(d,(160,525),'Industrial\nabrasives',65,INK,width=20,bold=True)
    txt(d,(160,725),'Distributor test system',31,'#526671',width=28)
    txt(d,(1030,445),'MANUFACTURER DISCUSSIONS',24,'#277d6a',width=40,bold=True)
    txt(d,(1030,525),'Switzerland\nand Germany',65,INK,width=21,bold=True)
    txt(d,(1030,725),'Equipment manufacturers',31,'#526671',width=32)
    g['pilot']=save(im,'pilot.png')
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    txt(d,(110,90),'THE BUSINESS CASE',25,TEAL,width=50,bold=True)
    txt(d,(110,190),'Less time lost in the field.',76,width=40,bold=True)
    for i,(a,b) in enumerate([('Shorter','setup times'),('Fewer','unnecessary repairs'),('Fewer','repeat customer visits')]):
        x=110+i*580;d.rounded_rectangle((x,420,x+540,850),radius=24,fill='#1b303c')
        txt(d,(x+38,475),a,68,TEAL,width=20,bold=True)
        txt(d,(x+38,600),b,43,width=20)
    g['business']=save(im,'business.png')
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    txt(d,(110,120),'TIME SAVED / VISITS AVOIDED',27,TEAL,width=65,bold=True)
    txt(d,(110,290),'Lower service costs.\nA stronger bottom line.',91,width=31,bold=True,spacing=24)
    d.line((110,685,1800,685),fill='#38505e',width=2)
    txt(d,(110,755),'Built to pay for itself.',63,GOLD,width=45,bold=True)
    g['closing']=save(im,'closing.png')
    return g

def clip_still(image_path,frames,out,zoom=True):
    vf=f"scale={W}:{H},zoompan=z='1+0.025*on/{max(frames-1,1)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s={W}x{H}:fps={FPS}" if zoom else f'scale={W}:{H},fps={FPS}'
    run(['-loop','1','-i',image_path,'-vf',vf,'-frames:v',frames,'-an']+ENC+[out])

def clip_device(background,src,offset,frames,out,available=None):
    # All footage is a genuine physical-iPhone screen recording. Crop status-bar
    # chrome only, preserving app contents and the original disposition values.
    n=frames/FPS
    max_live=n if available is None else min(n,available)
    vf=f"[0:v]scale={W}:{H},fps={FPS},setsar=1[bg];[1:v]crop=1290:2600:0:110,scale=480:968:flags=lanczos,setsar=1,fps={FPS},trim=duration={max_live},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={max(0,n-max_live)+.1}[phone];[bg][phone]overlay=1330:55:shortest=1[out]"
    run(['-loop','1','-i',background,'-ss',offset,'-i',src,'-filter_complex',vf,'-map','[out]','-frames:v',frames,'-an']+ENC+[out])

def graph_frame(stage,progress):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    txt(d,(90,65),'THE KNOWLEDGE FEEDBACK LOOP',25,TEAL,width=80,bold=True)
    txt(d,(90,125),'Field experience becomes shared knowledge.',58,width=60,bold=True)
    nodes=[(100,350,430,520,'User feedback','Unhelpful advice'),(100,650,430,820,'Disposition signals','Possible knowledge gap'),(570,500,900,700,'Propose improvements','Customer-premises models'),(1040,500,1370,700,'Human review','Edit / approve in the Wiki'),(1510,500,1840,700,'Approved knowledge','Deploy to local devices')]
    paths=[[(430,435),(500,435),(500,600),(570,600)],[(430,735),(500,735),(500,600),(570,600)],[(900,600),(1040,600)],[(1370,600),(1510,600)],[(1675,700),(1675,925),(265,925),(265,820)]]
    for path in paths:d.line(path,fill='#38505e',width=5,joint='curve')
    active={0:[0,1],1:[0],2:[1],3:[2],4:[3],5:[4],6:[4]}[stage]
    for i,(x0,y0,x1,y1,title,sub) in enumerate(nodes):
        on=i in active
        d.rounded_rectangle((x0,y0,x1,y1),radius=22,fill='#223b46' if on else '#182b36',outline=TEAL if on else '#38505e',width=4 if on else 2)
        txt(d,(x0+25,y0+35),title,33,FG,width=18,bold=True,spacing=8)
        txt(d,(x0+25,y1-65),sub,23,TEAL if on else MUTED,width=23,spacing=6)
    path_id={0:None,1:0,2:1,3:2,4:3,5:4,6:4}[stage]
    if path_id is not None:
        path=paths[path_id];lengths=[math.dist(a,b) for a,b in zip(path,path[1:])];distance=(progress%1)*sum(lengths)
        for a,b,length in zip(path,path[1:],lengths):
            if distance<=length:
                q=distance/length;x=a[0]+q*(b[0]-a[0]);y=a[1]+q*(b[1]-a[1]);d.ellipse((x-10,y-10,x+10,y+10),fill=GOLD);break
            distance-=length
    txt(d,(90,1010),'A human controls what gets deployed.',25,GOLD,width=100)
    return im

def clip_graph(frames,out,stages):
    proc=subprocess.Popen(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-frames:v',str(frames),'-an']+ENC+[str(out)],stdin=subprocess.PIPE)
    for i in range(frames):
        p=i/max(1,frames-1);phase=min(int(p*len(stages)),len(stages)-1)
        proc.stdin.write(graph_frame(stages[phase],p*len(stages)%1).tobytes())
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('Feedback animation encoder failed')

def srt_time(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def build():
    timing=json.loads((ROOT/'narration-timing.json').read_text());p=timing['parts'];g=make_graphics();src=ROOT/'sources';timeline=[]
    def add(label,kind,frames,**kw):
        if frames>0:timeline.append(dict(label=label,kind=kind,frames=frames,**kw))
    def N(i):return round(p[i]['end']*FPS)-round(p[i]['start']*FPS)
    # Single continuous cave shot across the opening and the hunting phrase;
    # no restarting the same Ken Burns move at the paragraph boundary.
    hunt=round(1.5*FPS);trojan=round(2.3*FPS);leonardo=round(2.7*FPS)
    add('Life is about stories / hunting','still',N(0)+hunt,image=str(g['cave']))
    add('Trojan horse','still',trojan,image=str(g['trojan']))
    add('Leonardo machine drawing','still',leonardo,image=str(g['leonardo']))
    add('Wikipedia home page','still',N(1)-hunt-trojan-leonardo,image=str(g['wikipedia']))
    add('Real technical question and answer','device',N(2),image=str(g['converse']),offset=60.)
    add('Guidance in the field','device',N(3),image=str(g['field']),offset=63.6)
    a=N(4)//2;add('Knowledge ingestion / existing admin capture','still',a,image=str(g['knowledge']))
    add('Technical guidance with local sources','device',N(4)-a,image=str(g['local']),offset=68.0)
    add('Offline inference / source packs','device',N(5),image=str(g['offline']),offset=92.0,available=2.8)
    add('Two feedback channels','graph',N(6),stages=[0])
    a=round(3.3*FPS);b=round(7.2*FPS)
    add('User feedback controls','device',a,image=str(g['feedback-user']),offset=74.,available=3.3)
    add('Real model disposition readout','device',b,image=str(g['disposition']),offset=78.0,available=6.)
    add('Disposition signals / feedback paths','graph',N(7)-a-b,stages=[1,2])
    add('Proposed improvements on customer premises','graph',N(8),stages=[3])
    a=N(9)//2;add('Human-editable Wiki','still',a,image=str(g['wiki']))
    add('Human review and approval','still',N(9)-a,image=str(g['wiki-detail']))
    add('Approved knowledge returns to devices','graph',N(10),stages=[4,5])
    a=round(3.5*FPS);b=round(3.3*FPS)
    add('Actual model selection screen','device',a,image=str(g['settings']),offset=100.0,available=1/30)
    add('Actual knowledge-pack settings','device',b,image=str(g['settings']),offset=92.,available=2.3)
    add('Image input / replace with dedicated OCR recording','device',N(11)-a-b,image=str(g['image']),offset=112.,available=4.)
    add('Industrial pilot and manufacturer discussions','still',N(12),image=str(g['pilot']))
    add('Service economics','still',N(13),image=str(g['business']))
    add('Commercial ending','still',N(14)+round(1.8*FPS),image=str(g['closing']))
    clock=0
    for i,s in enumerate(timeline):
        s['start']=clock/FPS;clock+=s['frames'];s['end']=clock/FPS;s['output']=str(ROOT/'segments'/f'{i:02}.mp4')
    (ROOT/'timeline.json').write_text(json.dumps(timeline,indent=2,ensure_ascii=False)+'\n')
    for i,s in enumerate(timeline):
        out=Path(s['output'])
        if out.exists():continue
        print(f'Render {i+1}/{len(timeline)}: {s["label"]}',flush=True)
        if s['kind']=='still':clip_still(s['image'],s['frames'],out,zoom=True)
        elif s['kind']=='device':clip_device(s['image'],src/'device-actual.mp4',s['offset'],s['frames'],out,s.get('available'))
        else:clip_graph(s['frames'],out,s['stages'])
    concat=ROOT/'segments/concat.txt';concat.write_text(''.join("file '"+s['output'].replace("'","'\\''")+"'\n" for s in timeline))
    run(['-f','concat','-safe','0','-i',concat,'-c','copy',ROOT/'picture-v1.mp4'])
    duration=clock/FPS
    run(['-i',ROOT/'picture-v1.mp4','-i',ROOT/'audio/narration.wav','-map','0:v','-map','1:a','-c:v','copy','-af','apad','-c:a','aac','-b:a','192k','-t',duration,'-movflags','+faststart',ROOT/'Air-Gapped-Industrial-AI-Demo-v1.mp4'])
    # Separate captions for review/accessibility; no burned-in subtitles.
    subs=[];counter=1
    for part in p:
        chunks=textwrap.wrap(part['text'],width=95,break_long_words=False,break_on_hyphens=False)
        weights=[len(c.split()) for c in chunks];total=sum(weights);at=part['start']
        for chunk,w in zip(chunks,weights):
            end=at+part['duration']*w/total
            subs.append(f'{counter}\n{srt_time(at)} --> {srt_time(end)}\n'+ '\n'.join(textwrap.wrap(chunk,width=48))+'\n');counter+=1;at=end
    (ROOT/'Air-Gapped-Industrial-AI-Demo-v1.en.srt').write_text('\n'.join(subs))
    print('COMPLETE',duration,ROOT/'Air-Gapped-Industrial-AI-Demo-v1.mp4',flush=True)

if __name__=='__main__':build()
