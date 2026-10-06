"""Validate the generated site: metadata, structure, links, anchors, safety rules and root/dist parity."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import datetime, json, re

BASE = Path(__file__).resolve().parent
pages = json.loads((BASE / 'content/pages.json').read_text(encoding='utf-8'))
GROUPS = {'入門', '架構', '資料保護', '營運', '治理'}
STATUS = {'已驗證', '快照', '待驗證'}
RISK = {'唯讀', '含變更', '含中斷服務'}
REQUIRED = ['slug', 'title', 'lead', 'group', 'audience', 'evidence_date', 'status', 'risk', 'purpose', 'prereq']
SECRET_PATTERNS = [
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'private key block'),
    (re.compile(r'AAAAC3NzaC1lZDI1NTE5[A-Za-z0-9+/]{20,}'), 'ssh public key body'),
    (re.compile(r'(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*[=:]\s*[^\s<`\'"]{6,}'), 'credential assignment'),
    (re.compile(r'(?i)(POSTGRES_PASSWORD|GITEA__database__PASSWD|SECRET_KEY|INTERNAL_TOKEN|JWT_SECRET)\s*[=:]\s*\S{4,}'), 'known secret key'),
]

# ---- metadata ----
slugs = [p['slug'] for p in pages]
assert len(slugs) == len(set(slugs)), 'duplicate slug'
for p in pages:
    for key in REQUIRED:
        assert p.get(key) not in (None, '', []), (p.get('slug'), 'missing', key)
    assert p['group'] in GROUPS, (p['slug'], p['group'])
    assert p['status'] in STATUS, (p['slug'], p['status'])
    assert p['risk'] in RISK, (p['slug'], p['risk'])
    datetime.date.fromisoformat(p['evidence_date'])
    assert (BASE / 'content/pages' / f'{p["slug"]}.md').is_file(), p['slug']


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()
        self.lang = self.title = False
        self.h1 = self.current = self.meta = 0
        self.pre_total = self.pre_unleveled = self.pre_leveled = 0
        self._pre = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, ('duplicate id', a['id'])
            self.ids.add(a['id'])
        if tag == 'html':
            self.lang = a.get('lang') == 'zh-Hant'
        if tag == 'title':
            self.title = True
        if tag == 'h1':
            self.h1 += 1
        if tag == 'dl' and a.get('class') == 'meta':
            self.meta += 1
        if a.get('aria-current') == 'page':
            self.current += 1
        if tag == 'pre':
            self.pre_total += 1
            self._pre = a.get('data-level')
            if self._pre:
                self.pre_leveled += 1
        if tag == 'code' and self._pre is None and a.get('class', '').startswith(('language-bash', 'language-powershell')):
            self.pre_unleveled += 1
        for k in ['href', 'src']:
            if k in a:
                self.links.append(a[k])

    def handle_endtag(self, tag):
        if tag == 'pre':
            self._pre = None


def check_sections(slug, prefix, keywords):
    text = (BASE / 'content/pages' / f'{slug}.md').read_text(encoding='utf-8')
    sections = [s for s in re.split(r'\n## ', '\n' + text) if re.match(prefix, s)]
    assert sections, (slug, 'no sections matching', prefix)
    for s in sections:
        title = s.splitlines()[0]
        for kw in keywords:
            assert kw in s, (slug, title, 'missing', kw)


for root in [BASE, BASE / 'dist']:
    scans = {}
    for p in pages:
        f = p['slug'] + '.html'
        source = (root / f).read_text(encoding='utf-8')
        scan = Scan()
        scan.feed(source)
        scans[f] = scan
        assert scan.lang and scan.title and scan.h1 == 1 and scan.current == 1, f
        assert scan.meta == 1, (f, 'meta block')
        assert p['evidence_date'] in source and p['status'] in source, (f, 'date/status chip')
        assert '文件快照' in source, f
        assert scan.pre_unleveled == 0, (f, 'shell code block without a command level (use bash-ro / bash-chg / bash-stop)')
        for rx, label in SECRET_PATTERNS:
            m = rx.search(source)
            assert not m, (f, 'possible secret', label, m.group(0)[:40])
        if 'data-level="stop"' in source:
            assert '回退' in source and '驗收' in source, (f, 'service-interrupting commands need 回退 and 驗收')
    for name, scan in scans.items():
        for link in scan.links:
            u = urlsplit(link)
            if u.scheme or u.netloc:
                continue
            target = unquote(u.path) or name
            assert (root / target).is_file(), (name, link)
            if u.fragment and target in scans:
                assert unquote(u.fragment) in scans[target].ids, (name, link)
    idx = (root / 'search-index.js').read_text(encoding='utf-8')
    assert idx.startswith('window.SEARCH_INDEX='), 'search-index.js format'
    entries = json.loads(idx[len('window.SEARCH_INDEX='):].rstrip().rstrip(';'))
    assert len(entries) >= len(pages), 'search index too small'
    for e in entries:
        target = unquote(urlsplit(e['u']).path)
        frag = urlsplit(e['u']).fragment
        assert (root / target).is_file(), e['u']
        if frag:
            assert unquote(frag) in scans[target].ids, ('search anchor', e['u'])

# ---- source-level structure rules ----
if 'restore' in slugs:
    check_sections('restore', r'S\d', ['前置', '決策', '驗收', '回退'])
if 'runbook' in slugs:
    check_sections('runbook', r'R\d', ['症狀', '先看', '判讀', '升級'])
for p in pages:
    src = (BASE / 'content/pages' / f'{p["slug"]}.md').read_text(encoding='utf-8')
    for rx, label in SECRET_PATTERNS:
        m = rx.search(src)
        assert not m, (p['slug'], 'possible secret in source', label, m.group(0)[:40])

# ---- parity ----
for name in [f'{p["slug"]}.html' for p in pages] + ['styles.css', 'site.js', 'search-index.js']:
    assert (BASE / name).read_bytes() == (BASE / 'dist' / name).read_bytes(), name
print(f'PASS: {len(pages)} pages; metadata, links, anchors, language, headings, command levels, secret scan, search index and root/dist parity.')
