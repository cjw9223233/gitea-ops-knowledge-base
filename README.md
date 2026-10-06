# Gitea 維運知識庫 · 手冊 v3

給新手、PM、開發者、Linux 維運與網管使用的繁體中文靜態知識庫。**僅供內部／私人使用**：內容含內網位址與維運弱點，不得推送到公開 repo 或公開網站。每頁標示「資料日期」與「狀態」，不是即時監控。

## 閱讀

直接開啟根目錄 `index.html`，或在 repo 執行：

```bash
python -m http.server 4320 --bind 127.0.0.1 --directory dist
```

開啟 http://127.0.0.1:4320/ 。不需要 Node 套件、資料庫或連線正式主機。全文搜尋的索引是 `search-index.js`，用 `file://` 直接開也能搜尋。

## 頁面（15 頁，四個導覽群組）

| 群組 | 頁面 |
|---|---|
| 入門 | `index` 維運總覽、`start` 新手入門、`glossary` 名詞與圖解 |
| 架構 | `system` 系統與服務、`network` 網路與連線 |
| 資料保護 | `backup` 備份與備援、`restore` 還原與演練 |
| 營運 | `schedule` 排程管理（含電源與喚醒）、`daily` 日常巡檢、`logs` Log 與產出物、`runbook` 事件處理手冊、`hardware` 硬碟與開機排查 |
| 治理 | `access` 權限與帳號、`risks` 風險與待辦、`changes` 變更與驗收 |

## 修改與檢查

```bash
python -m pip install -r requirements.txt
python -X utf8 build_knowledge.py
python -X utf8 validate_site.py
node --check assets/site.js
```

每條指令分別執行，檢查成功後才提交。Node 僅用於 JavaScript 語法檢查；網站執行不需要 Node。

| 路徑 | 用途 |
|---|---|
| `content/pages/*.md` | 現行網站內容；請優先編輯此處 |
| `content/pages.json` | 頁面順序、標題、導覽群組、讀者、資料日期、狀態、風險等級、用途與前置知識 |
| `content/diagrams/*.svg` | 內嵌圖（深色模式可讀）；在頁面以 `{{diagram:檔名}}` 插入 |
| `templates/page.html` | 共用版型 |
| `assets/` | CSS、導覽、搜尋、深色模式與複製按鈕程式 |
| `build_knowledge.py` | 產生根目錄與 `dist` 相同的頁面、`search-index.js` |
| `validate_site.py` | 檢查中繼資料、連結、錨點、指令分級、機密樣式、搜尋索引與輸出一致性 |
| `downloads/` | 網站提供的完整稽核報告 |
| `content/manual.md`、`content/schedule-report.md` | 9 月歷史來源，不當作現行狀態 |

不直接手改根目錄或 `dist` 的產生檔。變更內容後執行 build，將來源與產生檔一併提交。

## 寫作規則

1. 每個頁面在 `pages.json` 填 `purpose`（這頁解決什麼）、`prereq`（前置知識）、`risk`（唯讀／含變更／含中斷服務）、`evidence_date`、`status`（已驗證／快照／待驗證）。
2. 每個事實標資料日期；沒有新證據不改成「已驗證」或「已結案」。
3. 程式碼區塊必須標分級：`bash-ro`／`bash-chg`／`bash-stop`（Windows 用 `powershell-ro` 等）。`stop` 級指令所在頁面必須同時有「回退」與「驗收」。`cron`、`text` 區塊不需分級。
4. 一個程式碼區塊只放一條指令；多行指令不要合併。
5. 提示框用 `!!! tip "白話說明"`（新手）、`!!! info "給維運"`、`!!! warning`、`!!! danger`、`!!! note`。
6. `restore` 的每個 `## S…` 情境必須有「前置、決策、驗收、回退」；`runbook` 的每個 `## R…` 必須有「症狀、先看、判讀、升級」。
7. 禁止出現密碼、私鑰、權杖、SSH 公鑰內容，或完整的 `docker inspect`／`compose config` 輸出；`validate_site.py` 會掃描。

## Git 與發佈

沿用原 repository 歷史與 `origin`：`https://github.com/cjw9223233/gitea-ops-knowledge-base.git`。

- 手冊 v3 在 `feature/handbook-v3` 分支（由 `feature/ui-ux-enhancements` 開出），每個階段（P0–P6）小步提交；**不動 `main`、不推送**，合併順序由專案負責人決定。
- 根目錄 HTML 保留原 GitHub Pages 路徑相容性；因內容僅限內部，**不要**啟用公開的 GitHub Pages。
- `.openai/hosting.json` 保留既有私人 Sites 專案 ID，靜態目錄為 `dist`。
- Sites 發佈狀態必須以實際工具部署結果為準；本機預覽成功不等於正式網站已發佈。

## 資料與安全界線

網站不含私鑰、密碼、登入權杖或任何直接操作正式主機的後端。範例命令供管理員在正確主機執行，網站本身不會停止服務或執行備份。已部署、已驗證、待驗收三種狀態需分開；沒有新的正式證據，不把異機備份或還原標成成功。

查看 [重構紀錄](docs/REFACTOR.md) 與網站「變更與驗收」頁了解範圍。
