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

// sidebar nav filter
const navFilter=document.querySelector('#nav-filter');
const navEmpty=document.querySelector('#nav-empty');
if(navFilter&&sidebar){
 const links=[...sidebar.querySelectorAll('.nav a')];
 navFilter.addEventListener('input',()=>{
  const q=navFilter.value.trim().toLowerCase();
  let shown=0;
  links.forEach(link=>{
   const match=link.textContent.toLowerCase().includes(q);
   link.hidden=!match;
   if(match)shown++;
  });
  if(navEmpty)navEmpty.hidden=shown!==0;
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

// copy-to-clipboard on code blocks
document.querySelectorAll('.article pre').forEach(pre=>{
 const btn=document.createElement('button');
 btn.className='copy-btn';
 btn.type='button';
 btn.textContent='複製';
 btn.setAttribute('aria-label','複製程式碼');
 btn.addEventListener('click',async()=>{
  const text=pre.querySelector('code')?.textContent??pre.textContent;
  try{
   await navigator.clipboard.writeText(text);
   btn.textContent='已複製';
   btn.classList.add('copied');
  }catch(e){
   btn.textContent='複製失敗';
  }
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
