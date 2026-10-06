const toggle=document.querySelector('#menu-button');
const sidebar=document.querySelector('#navigation');
if(toggle&&sidebar){
 const close=()=>{sidebar.classList.remove('open');toggle.setAttribute('aria-expanded','false');};
 toggle.addEventListener('click',()=>{const open=sidebar.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){close();toggle.focus();}});
 document.addEventListener('click',event=>{if(!sidebar.contains(event.target)&&!toggle.contains(event.target))close();});
 sidebar.querySelectorAll('a').forEach(link=>link.addEventListener('click',close));
}

// theme toggle (persisted in localStorage)
const themeBtn=document.querySelector('#theme-toggle');
if(themeBtn){
 const apply=mode=>{
  document.documentElement.setAttribute('data-theme',mode);
  themeBtn.querySelector('span').textContent=mode==='dark'?'☀':'🌙';
 };
 let saved='light';
 try{saved=localStorage.getItem('theme')||'light';}catch(e){}
 apply(saved);
 themeBtn.addEventListener('click',()=>{
  const next=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  apply(next);
  try{localStorage.setItem('theme',next);}catch(e){}
 });
}

// sidebar search: page-name filter plus full-text results from window.SEARCH_INDEX
const navFilter=document.querySelector('#nav-filter');
const navEmpty=document.querySelector('#nav-empty');
const resultsBox=document.querySelector('#search-results');
if(navFilter&&sidebar){
 const links=[...sidebar.querySelectorAll('.nav a')];
 const groups=[...sidebar.querySelectorAll('.nav-group')];
 const esc=t=>t.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 const escRe=t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 const tokensOf=q=>q.toLowerCase().split(/\s+/).filter(Boolean);
 const mark=(text,tokens)=>{
  let out=esc(text);
  tokens.forEach(tok=>{out=out.replace(new RegExp('('+escRe(esc(tok))+')','ig'),'<mark>$1</mark>');});
  return out;
 };
 const snippet=(text,tokens)=>{
  const low=text.toLowerCase();
  let at=-1;
  tokens.forEach(tok=>{const i=low.indexOf(tok);if(i>=0&&(at<0||i<at))at=i;});
  const start=Math.max(0,at-24);
  return (start>0?'…':'')+text.slice(start,start+110)+(text.length>start+110?'…':'');
 };
 const search=q=>{
  const tokens=tokensOf(q);
  const hits=[];
  (window.SEARCH_INDEX||[]).forEach(e=>{
   const hay=(e.p+' '+e.h+' '+e.t).toLowerCase();
   if(!tokens.every(t=>hay.includes(t)))return;
   let score=0;
   tokens.forEach(t=>{
    if(e.h.toLowerCase().includes(t))score+=3;
    if(e.p.toLowerCase().includes(t))score+=2;
    score+=Math.min(3,hay.split(t).length-1);
   });
   hits.push({e,score});
  });
  return hits.sort((a,b)=>b.score-a.score).slice(0,8);
 };
 navFilter.addEventListener('input',()=>{
  const q=navFilter.value.trim();
  const ql=q.toLowerCase();
  let shown=0;
  links.forEach(link=>{
   const match=link.textContent.toLowerCase().includes(ql);
   link.hidden=!match;
   if(match)shown++;
  });
  groups.forEach(g=>{g.hidden=!g.querySelector('.nav a:not([hidden])');});
  let hits=[];
  if(resultsBox){
   if(q.length>=2&&window.SEARCH_INDEX)hits=search(q);
   if(hits.length){
    const tokens=tokensOf(q);
    resultsBox.innerHTML=hits.map(({e})=>
     '<a href="'+e.u+'"><span class="sr-t">'+mark(e.h||e.p,tokens)+'<span class="sr-g">'+esc(e.p)+'</span></span>'+
     '<span class="sr-s">'+mark(snippet(e.t,tokens),tokens)+'</span></a>').join('');
    resultsBox.hidden=false;
   }else{resultsBox.hidden=true;resultsBox.innerHTML='';}
  }
  if(navEmpty)navEmpty.hidden=(shown+hits.length)!==0;
 });
}

// outline scrollspy
const outlineLinks=[...document.querySelectorAll('.outline a')];
if(outlineLinks.length){
 const targets=outlineLinks.map(link=>document.getElementById(decodeURIComponent(link.getAttribute('href').slice(1)))).filter(Boolean);
 if('IntersectionObserver' in window && targets.length){
  const setActive=id=>outlineLinks.forEach(link=>link.classList.toggle('active',link.getAttribute('href')==='#'+id));
  const observer=new IntersectionObserver(entries=>{
   const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top);
   if(visible.length)setActive(visible[0].target.id);
  },{rootMargin:'-20% 0px -70% 0px'});
  targets.forEach(t=>observer.observe(t));
 }
}

// copy-to-clipboard on code blocks (falls back for non-secure origins, e.g. plain http on a LAN IP)
function legacyCopy(text){
 const area=document.createElement('textarea');
 area.value=text;
 area.setAttribute('readonly','');
 area.style.position='fixed';
 area.style.top='-1000px';
 area.style.left='-1000px';
 document.body.appendChild(area);
 area.select();
 area.setSelectionRange(0,text.length);
 let ok=false;
 try{ok=document.execCommand('copy');}catch(e){ok=false;}
 document.body.removeChild(area);
 return ok;
}
document.querySelectorAll('.article pre').forEach(pre=>{
 const btn=document.createElement('button');
 btn.className='copy-btn';
 btn.type='button';
 btn.textContent='複製';
 btn.setAttribute('aria-label','複製程式碼');
 btn.addEventListener('click',async()=>{
  const text=pre.querySelector('code')?.textContent??pre.textContent;
  let ok=false;
  if(window.isSecureContext&&navigator.clipboard&&navigator.clipboard.writeText){
   try{await navigator.clipboard.writeText(text);ok=true;}catch(e){ok=false;}
  }
  if(!ok)ok=legacyCopy(text);
  btn.textContent=ok?'已複製':'複製失敗';
  btn.classList.toggle('copied',ok);
  setTimeout(()=>{btn.textContent='複製';btn.classList.remove('copied');},1800);
 });
 pre.appendChild(btn);
});

// back-to-top
const backToTop=document.querySelector('#back-to-top');
if(backToTop){
 const onScroll=()=>backToTop.classList.toggle('visible',window.scrollY>480);
 document.addEventListener('scroll',onScroll,{passive:true});
 onScroll();
 backToTop.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
}
