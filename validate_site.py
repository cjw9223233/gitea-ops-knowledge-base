from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json
BASE=Path(__file__).resolve().parent
pages=json.loads((BASE/'content/pages.json').read_text(encoding='utf-8'))
class Scan(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.lang=False;self.title=False;self.h1=0;self.current=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids,('duplicate id',a['id'])
            self.ids.add(a['id'])
        if tag=='html':self.lang=a.get('lang')=='zh-Hant'
        if tag=='title':self.title=True
        if tag=='h1':self.h1+=1
        if a.get('aria-current')=='page':self.current+=1
        for k in ['href','src']:
            if k in a:self.links.append(a[k])
for root in [BASE,BASE/'dist']:
    scans={}
    for p in pages:
        f=p['slug']+'.html';source=(root/f).read_text(encoding='utf-8')
        scan=Scan();scan.feed(source);scans[f]=scan
        assert scan.lang and scan.title and scan.h1==1 and scan.current==1,f
        assert 'BEGIN OPENSSH PRIVATE KEY' not in source
        assert '文件快照' in source
    for name,scan in scans.items():
        for link in scan.links:
            u=urlsplit(link)
            if u.scheme or u.netloc:continue
            target=unquote(u.path) or name
            assert (root/target).is_file(),(name,link)
            if u.fragment and target in scans:assert unquote(u.fragment) in scans[target].ids,(name,link)
for p in pages:
    name=p['slug']+'.html'
    assert (BASE/name).read_bytes()==(BASE/'dist'/name).read_bytes(),name
print(f'PASS: {len(pages)} pages; root/dist parity, links, anchors, language, headings and snapshot labels.')
