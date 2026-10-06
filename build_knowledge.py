"""Build root for existing GitHub Pages and identical dist for private Sites."""
from pathlib import Path
from string import Template
import html,json,re,shutil
import markdown
BASE=Path(__file__).resolve().parent
PAGES=json.loads((BASE/'content/pages.json').read_text(encoding='utf-8'))
TEMPLATE=Template((BASE/'templates/page.html').read_text(encoding='utf-8'))
DIST=BASE/'dist'
DIST.mkdir(exist_ok=True)
for page in PAGES:
    slug=page['slug']
    raw=(BASE/'content/pages'/f'{slug}.md').read_text(encoding='utf-8')
    raw=re.sub(r'```mermaid[\s\S]*?```','<p class="flow">使用者 → Gitea → PostgreSQL<br>主機保存服務資料，備機接收獨立封存備份。</p>',raw)
    md=markdown.Markdown(extensions=['tables','fenced_code','toc','sane_lists'],extension_configs={'toc':{'toc_depth':'2'}})
    body=md.convert(raw)
    body=re.sub(r'(<table>[\s\S]*?</table>)',r'<div class="table-wrap" tabindex="0" role="region" aria-label="可橫向捲動的資料表">\1</div>',body)
    nav=''.join(f'<a href="{p["slug"]}.html"'+(' aria-current="page"' if p['slug']==slug else '')+f'><span>{i+1:02}</span>{html.escape(p["title"])}</a>' for i,p in enumerate(PAGES))
    outline=''.join(f'<a href="#{html.escape(t["id"])}">{html.escape(t["name"])}</a>' for t in md.toc_tokens)
    quick=''
    if slug=='index':
        quick='<section class="grid quick" aria-label="常用工作入口">'+''.join(f'<a class="card" href="{url}"><span class="index">{n}</span><h2>{title}</h2><p>{desc}</p></a>' for n,url,title,desc in [
            ('01','logs.html','查 Log 與備份','檔案位置、輪替紀錄與成功標記'),
            ('02','schedule.html','確認排程','時段、執行身分與保護機制'),
            ('03','hardware.html','排查開機異常','已知證據與硬體檢查優先序')])+'</section>'
    rendered=TEMPLATE.substitute(title=html.escape(page['title']),lead=html.escape(page['lead']),nav=nav,outline=outline,body=body,quick=quick)
    for target in [BASE,DIST]:(target/f'{slug}.html').write_text(rendered,encoding='utf-8')
for name in ['styles.css','site.js']:
    for target in [BASE,DIST]:shutil.copy2(BASE/'assets'/name,target/name)
shutil.copytree(BASE/'downloads',DIST/'downloads',dirs_exist_ok=True)
print(f'Built {len(PAGES)} routes for root and dist.')
