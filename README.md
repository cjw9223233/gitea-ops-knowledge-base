# Gitea 維運知識庫 · 交接版 02

給 PM、Linux 維運與新進接手者使用的繁體中文靜態知識庫。2026-10-06 重構，維運證據截至 2026-10-05 18:33（Asia/Taipei），不是即時監控。

## 閱讀

直接開啟根目錄 `index.html`，或在 repo 執行：

```bash
python -m http.server 4320 --bind 127.0.0.1 --directory dist
```

開啟 http://127.0.0.1:4320/ 。不需要 Node 套件、資料庫或連線正式主機。

## 修改與檢查

```bash
python -m pip install -r requirements.txt
python -X utf8 build_knowledge.py
python -X utf8 validate_site.py
node --check site.js
```

每條指令分別執行，檢查成功後才提交。Node 僅用於 JavaScript 語法檢查；網站執行不需要 Node。

| 路徑 | 用途 |
|---|---|
| content/pages/*.md | 現行網站內容；請優先編輯此處 |
| content/pages.json | 頁面順序、標題及說明 |
| templates/page.html | 共用版型 |
| assets/ | CSS 與行動版導覽程式 |
| build_knowledge.py | 產生根目錄與 dist 相同頁面 |
| validate_site.py | 檢查連結、錨點、標題、導覽及輸出一致性 |
| downloads/ | 網站提供的完整稽核報告 |
| content/manual.md、content/schedule-report.md | 保留 9 月歷史來源，不當作現行部署狀態 |

不直接手改根目錄或 dist 的產生檔。變更內容後執行 build，將來源與產生檔一併提交。

## Git 與發佈

沿用原 repository 歷史與 `origin`：`https://github.com/cjw9223233/gitea-ops-knowledge-base.git`，未另外建立重複的 GitHub repo。

- 根目錄 HTML 保留原 GitHub Pages 路徑相容性。
- `.openai/hosting.json` 保留既有私人 Sites 專案 ID，靜態目錄為 `dist`。
- 本次沒有推送 GitHub。文件含內網位址與維運弱點，未經確認不要推送至公開網站或公開 repo。
- Sites 發佈狀態必須以實際工具部署結果為準；本機預覽成功不等於正式網站已發佈。

## 資料與安全界線

網站不含私鑰、密碼、登入權杖或任何直接操作正式主機的後端。範例命令供管理員在正確主機執行，網站本身不會停止服務或執行備份。已部署、已驗證、待驗收三種狀態需分開；沒有新的正式證據，不把異機備份或還原標成成功。

查看 [重構紀錄](docs/REFACTOR.md) 與網站「變更與驗收」頁了解範圍。
