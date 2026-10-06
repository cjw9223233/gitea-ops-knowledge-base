const toggle=document.querySelector('#menu-button');
const sidebar=document.querySelector('#navigation');
if(toggle&&sidebar){
 const close=()=>{sidebar.classList.remove('open');toggle.setAttribute('aria-expanded','false');};
 toggle.addEventListener('click',()=>{const open=sidebar.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){close();toggle.focus();}});
 document.addEventListener('click',event=>{if(!sidebar.contains(event.target)&&!toggle.contains(event.target))close();});
 sidebar.querySelectorAll('a').forEach(link=>link.addEventListener('click',close));
}
