import json, os

story_dir = r'C:\Users\migue\Videos\StoryVideos'
data = json.load(open(os.path.join(story_dir, 'hub_data.json'), encoding='utf-8'))
data_js = json.dumps(data, ensure_ascii=False)

head = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>The Lost Coins — Runway Hub</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f1117; color: #e2e8f0; display: flex; height: 100vh; overflow: hidden; }
#sidebar { width: 280px; min-width: 280px; background: #1a1d27; border-right: 1px solid #2d3148; display: flex; flex-direction: column; overflow: hidden; }
#sidebar-header { padding: 16px; border-bottom: 1px solid #2d3148; }
#sidebar-header h1 { font-size: 1rem; font-weight: 700; color: #a78bfa; margin-bottom: 8px; }
#stats { font-size: 0.75rem; color: #64748b; line-height: 1.6; }
#filter-bar { padding: 10px 16px; border-bottom: 1px solid #2d3148; display: flex; gap: 6px; }
.filter-btn { flex: 1; padding: 5px; border: 1px solid #2d3148; background: #0f1117; color: #94a3b8; border-radius: 4px; cursor: pointer; font-size: 0.72rem; }
.filter-btn.active { background: #4f46e5; border-color: #4f46e5; color: white; }
#chapter-list { overflow-y: auto; flex: 1; }
.ch-item { padding: 10px 16px; cursor: pointer; border-bottom: 1px solid #1e2130; display: flex; align-items: center; gap: 10px; }
.ch-item:hover { background: #232640; }
.ch-item.active { background: #2d3060; border-left: 3px solid #4f46e5; }
.ch-num { font-size: 0.65rem; color: #64748b; min-width: 28px; }
.ch-title { font-size: 0.78rem; flex: 1; line-height: 1.3; }
.ch-badge { font-size: 0.65rem; padding: 2px 6px; border-radius: 10px; white-space: nowrap; }
.badge-done { background: #14532d; color: #4ade80; }
.badge-partial { background: #78350f; color: #fbbf24; }
.badge-empty { background: #1e1b4b; color: #818cf8; }
#main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
#main-header { padding: 16px 24px; border-bottom: 1px solid #2d3148; background: #1a1d27; }
#main-header h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 4px; }
.sub { font-size: 0.78rem; color: #64748b; }
#prompts-area { flex: 1; overflow-y: auto; padding: 20px 24px; display: grid; gap: 16px; align-content: start; }
.prompt-card { background: #1a1d27; border: 1px solid #2d3148; border-left: 3px solid #2d3148; border-radius: 8px; overflow: hidden; }
.prompt-header { padding: 10px 14px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #2d3148; flex-wrap: wrap; }
.prompt-num { font-size: 0.7rem; font-weight: 700; color: #a78bfa; min-width: 60px; }
.prompt-scene { font-size: 0.82rem; font-weight: 600; flex: 1; }
.clip-label { font-size: 0.65rem; color: #64748b; }
.status-select { font-size: 0.7rem; padding: 3px 6px; border-radius: 4px; border: 1px solid #2d3148; background: #0f1117; color: #e2e8f0; cursor: pointer; }
.copy-btn { font-size: 0.7rem; padding: 4px 10px; border: 1px solid #4f46e5; background: transparent; color: #818cf8; border-radius: 4px; cursor: pointer; }
.copy-btn:hover { background: #4f46e5; color: white; }
.copy-btn.copied { background: #14532d; border-color: #14532d; color: #4ade80; }
.prompt-text { padding: 12px 14px; font-size: 0.78rem; line-height: 1.7; color: #cbd5e1; white-space: pre-wrap; }
#empty-state { color: #64748b; font-size: 0.9rem; padding: 40px; text-align: center; }
</style>
</head>
<body>
<div id="sidebar">
  <div id="sidebar-header">
    <h1>The Lost Coins Hub</h1>
    <div id="stats"></div>
  </div>
  <div id="filter-bar">
    <button class="filter-btn active" onclick="setFilter('all',this)">All</button>
    <button class="filter-btn" onclick="setFilter('incomplete',this)">Incomplete</button>
    <button class="filter-btn" onclick="setFilter('done',this)">Done</button>
  </div>
  <div id="chapter-list"></div>
</div>
<div id="main">
  <div id="main-header">
    <h2 id="chapter-title">Select a chapter</h2>
    <div class="sub" id="chapter-sub"></div>
  </div>
  <div id="prompts-area"><div id="empty-state">Select a chapter to view its prompts</div></div>
</div>
<script>
const CHAPTERS = """

script = """;

function getState(){try{return JSON.parse(localStorage.getItem('tlc_hub')||'{}')}catch{return{}}}
function saveState(s){localStorage.setItem('tlc_hub',JSON.stringify(s))}

function getClipStatus(chNum,idx){
  var s=getState(),key=chNum+'_'+idx;
  if(s[key]) return s[key];
  var ch=CHAPTERS.find(function(c){return c.num===chNum;});
  if(ch && ch.clips_done.indexOf(idx)>=0) return 'done';
  return 'pending';
}
function setClipStatus(chNum,idx,val){
  var s=getState(); s[chNum+'_'+idx]=val; saveState(s);
  updateStats(); renderSidebar();
  var card=document.getElementById('card_'+idx);
  if(card) card.style.borderLeftColor=val==='done'?'#4ade80':val==='generating'?'#fbbf24':'#2d3148';
}
function chDone(ch){
  var d=0;
  for(var i=1;i<=10;i++) if(getClipStatus(ch.num,i)==='done') d++;
  return d;
}

var currentFilter='all', currentChNum=null;

function setFilter(f,btn){
  currentFilter=f;
  document.querySelectorAll('.filter-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  renderSidebar();
}

function renderSidebar(){
  var list=document.getElementById('chapter-list');
  list.innerHTML='';
  CHAPTERS.forEach(function(ch){
    var done=chDone(ch),total=ch.prompts.length;
    if(currentFilter==='done' && done<total) return;
    if(currentFilter==='incomplete' && done>=total) return;
    var div=document.createElement('div');
    div.className='ch-item'+(ch.num===currentChNum?' active':'');
    div.onclick=(function(n){return function(){renderChapter(n);};})(ch.num);
    var bc=done===total?'badge-done':done>0?'badge-partial':'badge-empty';
    var label=ch.num==='PostCredits'?'PC':'Ch'+ch.num;
    var shortTitle=ch.title.replace(/^(Preamble|Post-Credits[^:]*:?\\s*|Chapter\\s*\\d+[:\\s]*)/i,'').trim()||ch.title;
    div.innerHTML='<span class="ch-num">'+label+'</span><span class="ch-title">'+shortTitle+'</span><span class="ch-badge '+bc+'">'+done+'/'+total+'</span>';
    list.appendChild(div);
  });
}

function updateStats(){
  var total=0,done=0;
  CHAPTERS.forEach(function(ch){total+=10;done+=chDone(ch);});
  document.getElementById('stats').innerHTML=
    CHAPTERS.length+' chapters &bull; '+done+'/'+total+' clips done<br>'+(total-done)+' clips remaining';
}

function renderChapter(chNum){
  currentChNum=chNum;
  renderSidebar();
  var ch=CHAPTERS.find(function(c){return c.num===chNum;});
  document.getElementById('chapter-title').textContent=ch.title;
  var done=chDone(ch);
  document.getElementById('chapter-sub').textContent=
    ch.folder+' \u2022 '+done+'/10 clips done \u2022 Save as '+ch.prefix+'_clip1.mp4 \u2026 '+ch.prefix+'_clip10.mp4';
  var area=document.getElementById('prompts-area');
  area.innerHTML='';
  ch.prompts.forEach(function(p,i){
    var idx=i+1;
    var status=getClipStatus(ch.num,idx);
    var borderColor=status==='done'?'#4ade80':status==='generating'?'#fbbf24':'#2d3148';
    var card=document.createElement('div');
    card.className='prompt-card'; card.id='card_'+idx;
    card.style.borderLeftColor=borderColor;
    var scene=p.scene.replace(/</g,'&lt;').replace(/>/g,'&gt;');
    var text=p.text.replace(/</g,'&lt;').replace(/>/g,'&gt;');
    var safeText=p.text.replace(/&/g,'&amp;').replace(/"/g,'&quot;');
    card.innerHTML=
      '<div class="prompt-header">'+
        '<span class="prompt-num">PROMPT '+idx+'</span>'+
        '<span class="prompt-scene">'+scene+'</span>'+
        '<span class="clip-label">'+ch.prefix+'_clip'+idx+'.mp4</span>'+
        '<select class="status-select" data-ch="'+ch.num+'" data-idx="'+idx+'">'+
          '<option value="pending"'+(status==='pending'?' selected':'')+'>Pending</option>'+
          '<option value="generating"'+(status==='generating'?' selected':'')+'>Generating</option>'+
          '<option value="done"'+(status==='done'?' selected':'')+'>Done</option>'+
        '</select>'+
        '<button class="copy-btn" data-text="'+safeText+'">Copy</button>'+
      '</div>'+
      '<div class="prompt-text">'+text+'</div>';
    area.appendChild(card);
  });

  area.querySelectorAll('.status-select').forEach(function(sel){
    sel.addEventListener('change',function(){
      setClipStatus(this.dataset.ch,parseInt(this.dataset.idx),this.value);
    });
  });
  area.querySelectorAll('.copy-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      var t=this;
      navigator.clipboard.writeText(this.dataset.text).then(function(){
        t.textContent='Copied!'; t.classList.add('copied');
        setTimeout(function(){t.textContent='Copy';t.classList.remove('copied');},2000);
      });
    });
  });
}

updateStats();
renderSidebar();
</script>
</body>
</html>"""

out = os.path.join(story_dir, 'runway_hub.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(head + data_js + script)
print('Written:', out, '({:,} bytes)'.format(len(head) + len(data_js) + len(script)))
