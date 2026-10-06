"""Build root for existing GitHub Pages compatibility and identical dist for private Sites.

Content lives in content/pages/*.md, page metadata in content/pages.json,
inline diagrams in content/diagrams/*.svg. Output goes to the repo root and dist/.
"""
from pathlib import Path
from string import Template
import html, json, re, shutil
import markdown
from markdown.extensions.toc import slugify_unicode

BASE = Path(__file__).resolve().parent
DIST = BASE / 'dist'
GROUPS = ['入門', '架構', '資料保護', '營運', '治理']
STATUS = {'已驗證': 'ok', '快照': 'snap', '待驗證': 'pending'}
RISK = {'唯讀': 'ro', '含變更': 'chg', '含中斷服務': 'stop'}
LEVEL = {'ro': '唯讀', 'chg': '變更', 'stop': '中斷服務'}
SHELL = {'bash': 'Linux bash', 'powershell': 'Windows PowerShell'}

PAGES_RAW = json.loads((BASE / 'content/pages.json').read_text(encoding='utf-8'))
# Navigation order: by group, then by order in pages.json.
PAGES = [p for g in GROUPS for p in PAGES_RAW if p['group'] == g]
TEMPLATE = Template((BASE / 'templates/page.html').read_text(encoding='utf-8'))
DIST.mkdir(exist_ok=True)


def diagram(match):
    name = match.group(1)
    svg = (BASE / 'content/diagrams' / f'{name}.svg').read_text(encoding='utf-8')
    svg = re.sub(r'\n\s*\n', '\n', svg).strip()
    cap = re.search(r'<title>(.*?)</title>', svg)
    caption = html.escape(cap.group(1)) if cap else ''
    return f'\n\n<figure class="diagram">{svg}<figcaption>{caption}</figcaption></figure>\n\n'


def level_pre(match):
    lang, lvl = match.group(1), match.group(2)
    label = f'{LEVEL[lvl]} · {SHELL[lang]}'
    return f'<pre data-level="{lvl}" data-label="{label}"><code class="language-{lang}">'


def strip_text(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def nav_html(current):
    out = []
    n = 0
    for g in GROUPS:
        links = []
        for p in PAGES:
            if p['group'] != g:
                continue
            n += 1
            cur = ' aria-current="page"' if p['slug'] == current else ''
            links.append(f'<a href="{p["slug"]}.html"{cur}><span>{n:02}</span>{html.escape(p["title"])}</a>')
        out.append(f'<div class="nav-group"><p class="nav-label">{g}</p><nav class="nav" aria-label="{g}">{"".join(links)}</nav></div>')
    return ''.join(out)


def index_extras():
    have = {p['slug'] for p in PAGES}

    def link(slug, text):
        return f'<a href="{slug}.html">{text}</a>' if slug in have else ''

    pro_slug = 'runbook' if 'runbook' in have else 'daily'
    entry = (
        '<section class="entry" aria-label="選擇你的入口">'
        '<a class="entry-card newbie" href="start.html"><span class="tag">我是新手</span><h2>從這裡開始</h2>'
        '<p>30 分鐘學習路徑：看懂系統、只用唯讀指令、知道哪些事不能做、遇到問題找誰。</p><span class="go">開始 Day 1 →</span></a>'
        f'<a class="entry-card pro" href="{pro_slug}.html"><span class="tag">我已在專案</span><h2>直接找答案</h2>'
        '<p>依症狀查處理步驟，或直接看排程、備份與還原、權限與風險。</p><span class="go">'
        + ('事件處理手冊' if pro_slug == 'runbook' else '日常巡檢') + ' →</span></a></section>')
    roles = [
        ('PM', [link('risks', '風險與待辦'), link('access', '權限與帳號')]),
        ('開發者', [link('network', '連不上時'), link('access', '申請權限')]),
        ('Linux 維運', [link('daily', '日常巡檢'), link('restore', '還原與演練') or link('backup', '備份與還原')]),
        ('網管', [link('network', '白名單與校時') or link('system', '系統與網路'), link('schedule', '排程與電源')]),
    ]
    entry += ('<section class="roles" aria-label="依角色查閱"><h2>依角色</h2><ul>'
              + ''.join(f'<li><b>{r}</b>{"".join(ls)}</li>' for r, ls in roles) + '</ul></section>')
    cards = [('01', 'logs', '查 Log 與備份', '檔案位置、輪替紀錄與成功標記'),
             ('02', 'schedule', '確認排程與電源', '時段、執行身分、22:00 關機行為'),
             ('03', 'restore' if 'restore' in have else 'backup', '還原與演練', '分情境步驟與演練紀錄表')]
    quick = ('<section class="grid quick" aria-label="常用工作入口">' + ''.join(
        f'<a class="card" href="{slug}.html"><span class="index">{n}</span><h2>{title}</h2><p>{desc}</p></a>'
        for n, slug, title, desc in cards) + '</section>')
    return entry + quick


search_index = []
for page in PAGES:
    slug = page['slug']
    raw = (BASE / 'content/pages' / f'{slug}.md').read_text(encoding='utf-8')
    raw = re.sub(r'\{\{diagram:([a-z0-9-]+)\}\}', diagram, raw)
    md = markdown.Markdown(
        extensions=['tables', 'fenced_code', 'toc', 'sane_lists', 'admonition'],
        extension_configs={'toc': {'toc_depth': '2', 'slugify': slugify_unicode}})
    body = md.convert(raw)
    body = re.sub(r'<pre><code class="language-(bash|powershell)-(ro|chg|stop)">', level_pre, body)
    body = re.sub(r'(<table>[\s\S]*?</table>)',
                  r'<div class="table-wrap" tabindex="0" role="region" aria-label="可橫向捲動的資料表">\1</div>', body)
    outline = ''.join(f'<a href="#{html.escape(t["id"])}">{html.escape(t["name"])}</a>' for t in md.toc_tokens)
    status = page['status']
    risk = page['risk']
    audience = ''.join(f'<span class="aud">{html.escape(a)}</span>' for a in page.get('audience', []))
    meta = (
        '<dl class="meta">'
        f'<div><dt>這頁解決什麼</dt><dd>{html.escape(page["purpose"])}</dd></div>'
        f'<div><dt>前置知識</dt><dd>{html.escape(page["prereq"])}</dd></div>'
        f'<div><dt>風險等級</dt><dd><span class="risk r-{RISK[risk]}">{html.escape(risk)}</span></dd></div>'
        f'<div><dt>適合讀者</dt><dd>{audience}</dd></div></dl>')
    rendered = TEMPLATE.substitute(
        title=html.escape(page['title']), lead=html.escape(page['lead']), group=html.escape(page['group']),
        nav=nav_html(slug), outline=outline, body=body, meta=meta,
        evidence_date=html.escape(page['evidence_date']), status=html.escape(status),
        status_class=STATUS[status], quick=index_extras() if slug == 'index' else '')
    for target in (BASE, DIST):
        (target / f'{slug}.html').write_text(rendered, encoding='utf-8')
    # Search index: one entry per h2 section so results deep-link to the section.
    parts = re.split(r'(<h2 id="[^"]*">.*?</h2>)', body)
    head_text = strip_text(parts[0])
    if head_text:
        search_index.append({'u': f'{slug}.html', 'p': page['title'], 'g': page['group'], 'h': '', 't': head_text[:600]})
    for i in range(1, len(parts), 2):
        m = re.match(r'<h2 id="([^"]*)">(.*?)</h2>', parts[i])
        search_index.append({'u': f'{slug}.html#{m.group(1)}', 'p': page['title'], 'g': page['group'],
                             'h': strip_text(m.group(2)), 't': strip_text(parts[i + 1])[:600]})

index_js = 'window.SEARCH_INDEX=' + json.dumps(search_index, ensure_ascii=False, separators=(',', ':')) + ';\n'
for target in (BASE, DIST):
    (target / 'search-index.js').write_text(index_js, encoding='utf-8')
for name in ['styles.css', 'site.js']:
    for target in (BASE, DIST):
        shutil.copy2(BASE / 'assets' / name, target / name)
shutil.copytree(BASE / 'downloads', DIST / 'downloads', dirs_exist_ok=True)
print(f'Built {len(PAGES)} routes for root and dist; {len(search_index)} search entries.')
