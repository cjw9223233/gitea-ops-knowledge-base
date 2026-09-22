from pathlib import Path
import html,re,sys
import markdown
BASE=Path(__file__).resolve().parent
DIST=BASE/'dist'
NAV=[('index.html','總覽'),('start.html','新手入門'),('system.html','系統與網路'),('daily.html','巡檢與排查'),('backup.html','備份與還原'),('schedule.html','排程管理'),('access.html','權限與交接')]
FAVICON='data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"%3E%3Crect width="40" height="40" rx="10" fill="%23102c3c"/%3E%3Cpath d="m10 12 8 8-8 8m12 0h9" fill="none" stroke="%237ce4d4" stroke-width="3"/%3E%3C/svg%3E'

def shell(file,title,body):
 nav=''.join(f'<a href="{url}"'+(' aria-current="page"' if url==file else '')+f'><span>{i:02}</span>{label}</a>' for i,(url,label) in enumerate(NAV))
 return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="票務中心系統組 Gitea 維運知識庫：實機架構、巡檢、排程、備份還原與新人交接。"><title>{title} · Gitea 維運知識庫</title><link rel="icon" type="image/svg+xml" href='{FAVICON}'><link rel="stylesheet" href="styles.css"><script src="site.js" defer></script></head><body><a class="skip" href="#main">跳至主要內容</a><aside class="sidebar" id="navigation"><a class="brand" href="index.html"><span class="brand-icon" aria-hidden="true">&gt;_</span><span>Gitea 維運知識庫<small>OPERATIONS / DOCS</small></span></a><p class="nav-label">工作指南</p><nav class="nav" aria-label="知識庫導覽">{nav}</nav><div class="side-bottom"><strong>票務中心系統組</strong>coffee · 維運文件<br>文件基準 2026.09.22</div></aside><div class="shell"><header class="topbar"><button class="mobile-menu" id="menu-button" aria-controls="navigation" aria-expanded="false" aria-label="開啟或關閉導覽">☰</button><div class="crumb"><span>維運知識庫 /</span><b>{title}</b></div><div class="edition">交接版 <strong>01</strong></div></header><main id="main" class="content">{body}<footer class="footer"><span>依 2026.09.21–22 實機盤點與部署紀錄整理</span><span>文件快照 · 非即時監控</span></footer></main></div></body></html>'''

def home():
 cards=[('start.html','01 / ONBOARDING','第一次接手','先認識三種入口、帳號身分與操作分級。','閱讀新手指南'),('daily.html','02 / ROUTINE','今天要檢查什麼','五分鐘巡檢、日誌判讀與常見故障排查。','開始日常巡檢'),('backup.html','03 / RECOVERY','備份與復原','了解一致性備份、隔離還原與切換驗收。','查閱復原流程')]
 tiles=''.join(f'<a class="card" href="{url}"><span class="index">{num}</span><h3>{title}</h3><p>{desc}</p><span class="link-label">{link} ↗</span></a>' for url,num,title,desc,link in cards)
 body=f'''<div class="head"><div><p class="eyebrow">GITEA / 維護與交接</p><h1>Gitea 維運知識庫</h1><p class="intro">從第一次登入，到日常巡檢、排程管理與備份還原。依工作目的，找到已確認的設定與操作步驟。</p></div><div class="head-note">文件更新<strong>2026 年 9 月 22 日</strong>主機 coffee</div></div><div class="notice"><strong>先看驗證範圍</strong><span>新版排程已安裝；正式備份、備機傳輸與完整還原仍待驗收。以下狀態來自盤點紀錄，不代表目前即時狀態。</span></div><div class="section-heading"><h2>從你的工作開始</h2><span>給第一次接手，也給日常值班</span></div><div class="grid">{tiles}</div><div class="section-heading"><h2>環境與驗證進度</h2><span>基準日期 2026.09.22</span></div><div class="status-grid"><div><span class="label">服務版本</span><strong>Gitea 1.23.5</strong><p>rootless 容器 · PostgreSQL 14.18</p></div><div><span class="label">維護排程</span><strong>已完成部署</strong><span class="tag">程式核對通過</span></div><div><span class="label">異機備份</span><strong>待首次驗收</strong><span class="tag pending">備機開機後驗證</span></div><div><span class="label">主機校時</span><strong>待修復 NTP</strong><p>日誌時間需對照可信來源</p></div></div><div class="split"><section class="panel"><h2>固定維護時段</h2><div class="schedule"><time>20:30</time><div><strong>週一至週五 · Gitea 冷備份</strong><p>停止服務 → 一致性備份 → 恢復 → 傳送備機</p></div></div><div class="schedule"><time>09:00</time><div><strong>每週六 · 系統週備份</strong><p>系統檔案搭配最近成功的冷備份，不新增週六停機。</p></div></div><div class="schedule"><time>22:00</time><div><strong>每日 · 受保護的關機</strong><p>維護進行中或尚待復原時，跳過當次關機。</p></div></div><a href="schedule.html">查看排程邏輯與例外處理 →</a></section><section class="panel"><h2>交接前要完成的事</h2><ul class="pending-list"><li><b>01</b><span>驗收第一次正式備份，記錄停機長度與結果。</span></li><li><b>02</b><span>備機開機後確認 SSH、傳輸及校驗碼。</span></li><li><b>03</b><span>在隔離環境完整還原，驗證 Git、LFS 與權限。</span></li><li><b>04</b><span>指定代理管理員，補齊校時及告警責任人。</span></li></ul><a href="access.html">查看責任分工與交接清單 →</a></section></div>'''
 (DIST/'index.html').write_text(shell('index.html','總覽',body),encoding='utf-8')

home()
if '--home-only' in sys.argv:sys.exit()
manual=(BASE/'content/manual.md').read_text(encoding='utf-8')
report=(BASE/'content/schedule-report.md').read_text(encoding='utf-8')
sections={}
for match in re.finditer(r'^## (\d+)\. (.*)\n([\s\S]*?)(?=^## \d+\.|\Z)',manual,re.M):
 sections[int(match.group(1))]=match.group(0)
pages=[('start.html','新手入門','認識服務入口、基本名詞與操作界線。',[1]),('system.html','系統與網路','主機、Docker、資料路徑與防火牆的已確認現況。',[2,3,4]),('daily.html','巡檢與排查','先蒐集證據，再判斷是用戶端、網路、應用或資料庫問題。',[6,11,10]),('backup.html','備份與還原','分清楚歷史備份、新版排程，以及尚未完成的還原驗收。',[7,8,9]),('access.html','權限與交接','以個人帳號與最小權限管理專案，讓接手責任可追蹤。',[5,12])]
def article(file,title,desc,text,notice=''):
 text=re.sub(r'```mermaid[\s\S]*?```','<div class="topology"><div>使用者<small>HTTP 3000 / Git SSH 2222</small></div><span aria-hidden="true">→</span><div>Gitea<small>設定、Git 與 LFS</small></div><span aria-hidden="true">→</span><div>PostgreSQL<small>db:5432 · 容器內網</small></div></div>',text)
 md=markdown.Markdown(extensions=['tables','fenced_code','toc','sane_lists'],extension_configs={'toc':{'toc_depth':'2'}})
 rendered=md.convert(text)
 rendered=re.sub(r'(<table>[\s\S]*?</table>)',r'<div class="table-wrap">\1</div>',rendered)
 toc=''.join(f'<a href="#{html.escape(t["id"])}">{t["name"]}</a>' for t in md.toc_tokens)
 body=f'<div class="doc-title"><p class="eyebrow">OPERATIONS HANDBOOK</p><h1>{title}</h1><p>{desc}</p></div>'+notice+f'<div class="doc-layout" style="margin-top:24px"><article class="article">{rendered}</article><aside class="outline" aria-label="本頁目錄"><h2>本頁內容</h2>{toc}</aside></div>'
 (DIST/file).write_text(shell(file,title,body),encoding='utf-8')
for file,title,desc,ids in pages:
 notice=''
 if file=='backup.html':notice='<div class="notice warning"><strong>請區分新舊流程</strong><span>本頁第 7 章描述舊備份的盤點結果；新版自動排程已部署，請搭配<a href="schedule.html">排程管理</a>查閱。手動還原需在隔離環境驗證。</span></div>'
 if file=='system.html':notice='<div class="notice"><strong>現況快照</strong><span>本頁數值來自 2026.09.21 的盤點。root 排程已於次日完成更新，請以<a href="schedule.html">部署報告</a>為準。</span></div>'
 article(file,title,desc,'\n\n'.join(sections[i] for i in ids),notice)
report=re.sub(r'^# .*\n','',report,count=1)
article('schedule.html','排程管理','新版排程已部署。保留原維護時段，加入一致性備份、失敗復原與關機保護。',report)
print('Generated 7 knowledge pages.')
