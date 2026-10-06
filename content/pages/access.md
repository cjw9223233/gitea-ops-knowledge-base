## 四層權限

{{diagram:access-layers}}

!!! tip "白話說明"
    想進到 Gitea 做事，要同時通過四道門：**① 網路放行 → ② 有主機帳號（只有維運需要）→ ③ Docker 權限（只有維運需要）→ ④ Gitea 裡有被授權的專案**。一般開發者只需要 ① 和 ④。**docker 群組等同 root**：能操作容器就能讀寫所有掛載的資料，不能因為「只是看看 Docker」就給。

## 現況事實（資料日期標在每列）

| 項目 | 現況 | 資料日期 |
|---|---|---|
| 主機一般帳號 | 只有 `coffee`（UID 1000），屬 `sudo`、`docker`、`adm`；**多人共用一個帳號，無法分辨是誰操作** | 2026-10-06 |
| sudo | 可 sudo 執行所有命令（多數需要密碼）；9/21 記錄另可免密碼執行 `/sbin/shutdown`，目前 `/etc/sudoers.d` 只有 README，該設定位置待確認 | 2026-10-06 |
| 其他家目錄 | `/home/cjw`（權限 777）、`/home/foo`、`/home/testg`、`/home/myXAMPP`（766）殘留，用途待確認 | 2026-10-06 |
| SSH 設定 | 設定檔寫明 `PermitRootLogin yes`、`PasswordAuthentication yes`、`X11Forwarding yes`；**是檔案內容，尚未用 root 的 `sshd -T` 驗證實際生效值** | 2026-10-06 |
| 主機防火牆 | `ufw` inactive、`fail2ban` inactive；`netfilter-persistent` active，白名單由 `DOCKER-USER` 規則實作 | 2026-10-06 |
| Gitea 帳號 | 17 帳號、1 位站台管理員、**0 位啟用雙因素驗證**、**0 條分支保護**、可自行註冊、允許匿名檢視 | 2026-09-21 |

## 目錄與檔案權限

| 路徑 | 盤點值 | 管理解讀 | 資料日期 |
|---|---|---|---|
| `/home/coffee/.ssh` | 700 | 正常 | 2026-10-05 |
| `authorized_keys` | 600 | 正常；這是檔案，不能 `cd` 進去 | 2026-10-05 |
| `/home/Gitea`、`config` | 766（coffee:coffee） | 權限不尋常；其他人沒有進入目錄的 x，不能簡化解讀為「所有人都能進入」 | 2026-10-06 |
| `config/app.ini` | 766（root:root） | 機密設定檔不應有廣泛寫入權與 executable bit；要連同父目錄與容器 UID 一起規劃 | 2026-09-21 |
| `docker-compose.yml` | 766（coffee:coffee） | 含資料庫密碼；應縮小讀寫範圍 | 2026-10-06 |
| `data` | 777（coffee:coffee） | 容器資料目錄權限過寬 | 2026-10-06 |
| `gitea-access-rules.sh` | 777（root:root） | **最優先**：高權限執行腳本可被非 root 改寫 | 2026-10-06 |
| `postgres` | 700（UID 999:coffee 群組） | 數字 UID 999 對應容器的 postgres；主機上顯示 `dnsmasq` 只是同號碼的名稱，不代表資料屬於 DNS 服務 | 2026-10-06 |
| `/var/backups/gitea-maintenance`、`/var/log/gitea-maintenance` | 700（root） | 正確；不要為了讓 `scp` 成功就放寬 | 2026-10-06 |

## 角色與責任

| 工作 | PM | Linux 管理員 | Gitea 管理員 | 網管 | 開發者 |
|---|---|---|---|---|---|
| 新人加入（帳號／權限） | A | I | R | C（連線來源） | 申請 |
| 白名單變更 | A | R（主機規則） | I | R（上游 ACL） | 申請 |
| 備份與外送 | I | R／A | I | C | — |
| 還原演練 | A | R | R（驗收功能） | I | I |
| 校時修復 | I | R | — | A／R | — |
| 權限收斂（目錄、SSH） | A | R | C | C | — |
| 離職處理 | A | R（Linux） | R（Gitea） | R（來源） | — |
| 事件通報與升級 | A／R | R | R | R | 回報 |

R＝執行、A＝負責核准、C＝需諮詢、I＝需知會。**負責人姓名尚待 PM 填寫：**

| 角色 | 姓名 | 代理人 |
|---|---|---|
| PM | | |
| Linux 管理員 | | |
| Gitea 管理員 | | |
| 網管 | | |
| 備機管理員 | | |

## 新手：我需要什麼權限？

| 我想做的事 | 需要 | 去找誰 |
|---|---|---|
| 讀程式碼、開 Issue | 連線來源＋Gitea 專案 Read | Gitea 管理員／專案負責人 |
| 提交程式碼、開 PR | 連線來源＋專案 Write | 專案負責人 |
| 管理專案設定與分支保護 | 專案 Admin | 專案負責人／Gitea 管理員 |
| 看主機狀態、讀日誌 | 具名 Linux 帳號（尚未建立）；目前只有共用 `coffee` | Linux 管理員 |
| 改設定、做備份還原 | Linux 管理員，且經過變更流程 | PM 核准 |

**一般開發者不需要 Linux 或 Docker 權限。**

## 新人加入、轉調、離職

**新人加入**（可貼進工單）：

- ☐ PM 指定專案、直屬負責人、需要的權限與有效期間。
- ☐ 網管確認連線來源（見 [網路與連線](network.html) 的申請單）。
- ☐ Gitea 管理員確認帳號、加入正確組織與團隊；新手先給 Read，確需提交才給 Write。
- ☐ 使用者在**自己的電腦**建立個人 SSH 金鑰，只把**公鑰**加入 Gitea「設定 → SSH／GPG 金鑰」；私鑰不傳給任何人。
- ☐ 校時修好後，再推行雙因素驗證（TOTP 依賴正確時間）。
- ☐ 用指定測試專案驗證：Write 的人能推送測試分支；Read 的人**不能**推送。
- ☐ 讀完專案 README、建置與部署方式，完成交接清單。

Gitea 目前沒有啟用 SMTP，不要承諾「忘記密碼一定收得到信」；管理員須建立可追溯的身分確認與復原流程。

**離職或轉調當日**（順序）：

- ☐ 先停用 Gitea 帳號，移除組織與團隊權限，撤銷個人 token 與不再使用的金鑰。
- ☐ 交接個人名下的重要專案、Webhook、鏡像認證與機器帳號；**不要**直接刪除唯一管理員、重要專案擁有者或尚未轉移的資料。
- ☐ 由 Linux 管理員處理主機帳號、`sudo`／`docker` 群組與 `authorized_keys`。
- ☐ 網管撤銷不再需要的來源白名單。
- ☐ 復原碼、資料庫密碼、SMTP 密碼、OAuth／LFS／JWT 等機密放在受控密碼庫；備份也必須保留必要機密，否則還原後部分功能可能失效。

## 金鑰清冊

| 金鑰 | 位置 | 持有者／用途 | 建立日 | 撤銷條件 |
|---|---|---|---|---|
| Codex 專用公鑰 | 主機 `coffee` 的 `authorized_keys` | 2026-09 至 10 月的稽核與修正工作 | 2026-09 | 工作結束後由管理員決定撤銷或納入正式清冊 |
| Claude 唯讀盤點公鑰（註解 `claude-sps-readonly-10-253-114-160-20261005`） | 主機 `coffee` 的 `authorized_keys` | 2026-10-05 起的唯讀盤點，經 `ro_ssh.py` 限制指令並留稽核紀錄 | 2026-10-05 | **盤點結束後撤銷**；若要保留，需納入正式清冊並指派持有者 |
| 個人 Gitea SSH 公鑰 | 各人在 Gitea 帳號 | 個人 clone／push | 各自 | 離職或轉調當日撤銷 |
| `coffee` 主機到備機的金鑰 | 主機 `coffee` 家目錄 `.ssh` | 備份外送的 SSH 登入備機 | 既有 | 換備機或金鑰輪替時更換；私鑰不複製、不放進文件 |

!!! warning "「唯讀」是工作範圍，不是技術限制"
    上述專用金鑰登入的帳號仍是 `coffee`，本身有 `sudo` 與 `docker` 權限。「唯讀」靠的是**操作紀律與工具檢查**，並沒有 SSH `forced-command` 之類的技術強制。因此專用金鑰要在工作結束後撤銷，私鑰檔也不可放進會被提交或分享的資料夾。

## 權限修正：先量、再改、不遞迴

!!! danger "不要對整個 `/home/Gitea` 執行遞迴的 chmod 或 chown"
    PostgreSQL（UID 999）、Gitea（UID 1000）、Git hooks、SSH 機密與一般資料的需求不同；整棵改權限可能讓資料庫無法啟動。每次只改**一個檔案**，並先記錄原值。

先量（唯讀）：

```bash-ro
stat -c '%a %U:%G %n' /home/Gitea /home/Gitea/config /home/Gitea/data /home/Gitea/postgres /home/Gitea/docker-compose.yml /home/Gitea/gitea-access-rules.sh
```

```bash-ro
docker exec gitea-server-1 id
```

建議順序（每一步都先記錄原值，改完驗收，失敗就回退）：

1. **`gitea-access-rules.sh`**（風險最高）：收回非 root 的寫入權限。

```bash-chg
sudo chmod 750 /home/Gitea/gitea-access-rules.sh
```

2. **`docker-compose.yml`**（含資料庫密碼）：縮小讀寫範圍，仍讓管理者可讀。

```bash-chg
sudo chmod 640 /home/Gitea/docker-compose.yml
```

3. **`config/app.ini` 與 `data`**：需要先確認容器 UID 1000 是否能正常讀寫，**在隔離環境測試**後再調整（見 [還原與演練](restore.html) 的隔離環境）。
4. **`/home/cjw` 等殘留目錄**：確認無用途後再收斂或移除。

**驗收**：每改一項後，確認 `healthz` 為 pass、能 clone 與 push 測試分支、備份排程下一輪仍成功。**回退**：把該檔案改回記錄的原值（例如 `sudo chmod 766 <檔案>`）；任何一步造成容器異常，立刻回退並通知 Linux 管理員。

## SSH 強化：兩階段

目前 `PermitRootLogin yes` 與 `PasswordAuthentication yes`（檔案內容，待驗證實際值）：

```bash-ro
sudo sshd -T | grep -E 'permitrootlogin|passwordauthentication|x11forwarding'
```

1. **階段一（先建立退路）**：為每位維運人員建立**具名**主機帳號與個人金鑰；驗證 `sudo`、現場主控台可用；確認備份外送的 coffee 金鑰不受影響。
2. **階段二（再收斂）**：在維護時段關閉 root 登入與密碼登入，重新載入設定並**保持原連線不斷**，另開一個連線驗證新帳號可登入後，才關閉原連線。**絕對不要先關掉唯一能登入的方式**。

## Gitea 治理建議

| 項目 | 現況 | 建議 |
|---|---|---|
| 分支保護 | 0 條 | 對 `main`／正式分支要求 Pull Request、至少一位審查者、限制 force push 與刪除；沒有註冊 Runner，不要把尚未存在的 CI 設為必過 |
| 雙因素驗證 | 0 個帳號 | 先修好校時，再分批推行 TOTP，並安全保存復原碼 |
| 註冊 | 可自行註冊 | 評估關閉，改為管理員建立 |
| 匿名檢視 | `REQUIRE_SIGNIN_VIEW=false` | 由專案負責人確認是否所有可連線者都應看見非私有專案 |
| 重要專案持有 | 多為個人名下 | 改由組織持有，並至少建立一位代理 Owner |
| 站台管理員 | 1 位 | 少量具名、啟用 MFA、定期稽核；不共用密碼或權杖 |

Gitea 可分別設定 Code、Issues、Pull Requests 等單元權限，授權後要用實際帳號驗證。[Gitea 1.23 權限文件](https://docs.gitea.com/1.23/usage/permissions/)
