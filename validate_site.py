from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

root=Path(__file__).resolve().parent/'dist'
class Scan(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set();self.title=False;self.lang=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  if tag=='html':self.lang=a.get('lang')=='zh-Hant'
  if tag=='title':self.title=True
  for key in ('href','src'):
   if key in a:self.links.append(a[key])
pages={}
for p in root.glob('*.html'):
 scan=Scan();scan.feed(p.read_text(encoding='utf-8'));pages[p.name]=scan
 assert scan.title and scan.lang,p.name
 assert 'BEGIN OPENSSH PRIVATE KEY' not in p.read_text(encoding='utf-8')
errors=[]
for name,scan in pages.items():
 for link in scan.links:
  parts=urlsplit(link)
  if parts.scheme or parts.netloc:continue
  target=unquote(parts.path) or name
  if not (root/target).is_file():errors.append((name,link,'missing file'))
  if parts.fragment and target in pages and unquote(parts.fragment) not in pages[target].ids:
   errors.append((name,link,'missing anchor'))
assert len(pages)==7
assert not errors,errors
print('PASS: 7 pages, local links, article anchors, assets, language and titles.')
