## 現行權限界線

| 身分 | 用途 |
|---|---|
| coffee 一般帳號 | 日常登入、查看可讀狀態；以既有 SSH 金鑰登入備機 |
| 主機 root | 執行維護排程、保護備份檔、管理容器與關機 |
| 備機 coffee | 接收封存檔及執行校驗；不是備機 root |

不要複製私鑰到報告、網站或 Git。正式備份目錄為 700，不能為了讓 scp 成功就改成全員可讀。

## 尚待收斂的權限

10/5 發現 Compose、data 與部分控制腳本權限過寬。應先核對容器的數字 UID/GID 與父目錄遍歷權限，再區分控制檔與資料目錄調整。不要整棵 chmod／chown，避免 PostgreSQL 無法啟動。

## 責任與驗收

| 項目 | 負責角色 | 完成條件 |
|---|---|---|
| 備份與傳輸 | Linux 管理員 | 正式 daily 遠端 checksum 與 SUCCESS，容量可追蹤 |
| 異機保留 | 備機管理員 | 有保留政策，清理只針對已驗證受管理副本 |
| 還原演練 | Gitea 管理員 | 隔離驗證 Git、DB、LFS、附件、Issue／PR、權限 |
| 校時與網路 | 網管 | 可信 NTP、備機路由、實際頻寬可確認 |
| 告警與維護窗口 | PM／值班人 | 指定接收人、回應時間、服務中斷與回復界線 |

## 個人帳號治理基準（9/21）

### 5. 帳號、權限與專案治理

### 5.1 四層權限

| 層次 | 管什麼 | 應授予誰 |
|---|---|---|
| 網路白名單 | 能否接觸服務埠 | 核准的來源網路／設備 |
| Linux SSH／sudo | 主機、設定、檔案與系統服務 | 少數具名維運人員 |
| Docker | 能操作容器及主機掛載資料 | 視同高權限維運，不給一般開發者 |
| Gitea 組織／團隊／儲存庫 | 原始碼、Issue、PR 及專案管理 | 依工作職責授權 |

本機 `coffee` 屬於 `sudo`、`docker`、`adm` 等群組，可 sudo 執行所有命令（大多需要密碼），另可免密碼執行 `/sbin/shutdown`。Docker 群組實質上具有 root 等級能力，不能用它當作「只看 Docker」的權限。[Docker 權限說明](https://docs.docker.com/engine/install/linux-postinstall/)

### 5.2 目前 Linux 與資料檔權限問題

| 路徑／項目 | 盤點值 | 管理解讀 |
|---|---|---|
| `/home/coffee/.ssh` | 700，1000:1000 | 正常的個人 SSH 目錄限制 |
| `authorized_keys` | 600，1000:1000 | 僅所有者可讀寫；這是檔案，不能 `cd` 進去 |
| `/home/Gitea`、`config` | 766，1000:1000 | 目錄權限不尋常；群組與其他人沒有 traverse 的 x，不能簡化解讀為所有人都能進入 |
| `config/app.ini` | 766，0:0 | 機密設定檔不應有廣泛寫入權及 executable bit；須連同父目錄與容器 UID 一起修正 |
| `docker-compose.yml` | 766，1000:1000 | 含 DB 密碼；應縮小讀寫範圍 |
| `data` | 777，1000:1000 | 容器資料目錄權限過寬 |
| `gitea-access-rules.sh` | 777，0:0 | 高權限執行腳本可被非 root 改寫，列為優先修正 |
| `postgres` | 700，999:1000 | 數字 UID 999 對應容器 postgres；主機顯示 dnsmasq 只是同 UID 名稱，不代表資料屬於 DNS 服務 |

建議由管理員在測試／維護時段逐項修正：Gitea 的 config/data 需讓 UID 1000 正常存取；app.ini 可朝 600 且讓執行 UID 正確持有的方向設計；Compose 只給部署管理者讀寫；防火牆腳本應 root 持有且不可讓一般帳號改寫。**不要對整個 `/home/Gitea` 執行同一組遞迴 chown／chmod**，因為 PostgreSQL、Git hooks、SSH 機密與一般資料的需求不同。

主機 `sshd_config` 明文設定 `PermitRootLogin yes`、`PasswordAuthentication yes`、`X11Forwarding yes`。這是檔案內容，尚未用 root 執行 `sshd -T` 驗證完整生效值。改善時先準備兩個可用的具名管理帳號與金鑰、驗證 sudo 及主控台，再收斂 root／密碼登入；不能先關掉唯一能登入的方式。

### 5.3 新人加入流程

1. PM 指定專案、直屬負責人、需要的權限及有效期間。
2. 網管處理連線來源；一般開發者不用申請 Linux 或 Docker 權限。
3. Gitea 管理員確認帳號，加入正確組織及團隊；新手先 Read，確需提交才授 Write。
4. 使用者在自己的電腦建立個人 SSH 金鑰，只把**公鑰**加入 Gitea「設定 → SSH／GPG 金鑰」；私鑰不傳給同事。
5. 啟用雙因素驗證並安全保存復原碼。因主機校時異常，先完成 NTP 修復，再集中推行 TOTP，避免大量無法登入。
6. 用指定測試專案驗證 clone、分支、PR。授 Write 的人驗證可提交測試分支；授 Read 的人應確認不能推送。
7. 讀取專案 README、建置方法、部署方式與負責人資訊；完成交接清單。

目前 SMTP 未啟用，不要承諾「忘記密碼一定能收重設信」。管理員須建立可追溯的身分確認及帳號復原流程。

### 5.4 建議的 Gitea 權限配置

| 身分 | 建議權限 | 不需要的權限 |
|---|---|---|
| 參與規格／查閱的人 | 專案 Read，加上需要的 Issue／PR 單元權限 | Linux、Docker、站台管理 |
| 開發者 | 指定 repository 的 Code Write | 全組織 Owner、站台管理 |
| 專案維護者 | 需要時給 repository Admin | 全站管理，除非兼任站台維運 |
| 組織負責人 | 組織 Owner，至少建立代理人 | 不因此自動取得主機 root |
| 站台管理員 | 少量具名帳號、MFA、定期稽核 | 共用密碼／共用權杖 |

Gitea 可分別設定 Code、Issues、Pull Requests 等單元權限，授權後仍要用實際帳號驗證。[Gitea 1.23 權限文件](https://docs.gitea.com/1.23/usage/permissions/)

建議關鍵專案使用組織持有，降低綁定單一個人帳號的風險。對 main／master／正式版本分支設定保護，要求 PR、至少一位審查者，限制 force push 及刪除；具體規則由各專案負責人核准。目前沒有註冊 Runner，不要把尚未建立的 CI 檢查設為必須通過而造成無法合併。

### 5.5 離職、轉調與金鑰管理

離職當日先停用 Gitea 帳號、移除組織／團隊權限、撤銷個人 token 與不再使用的金鑰，再交接個人名下的重要專案、Webhook、鏡像認證與機器帳號。另由系統管理員處理 Linux 帳號、sudo／Docker 群組與 authorized_keys；網管撤銷不再需要的來源白名單。

不可為了交接直接刪除唯一管理員、重要專案擁有者或尚未轉移的資料。復原碼、DB 密碼、SMTP 密碼、OAuth/LFS/JWT 等機密放在受控密碼庫；備份也必須保留必要機密，否則還原後部分功能可能失效。

本次為 Codex 建立的 SSH 公鑰只用於本次授權工作。它沒有被證實受到 SSH forced-command 的技術限制；「唯讀」是此次操作範圍，不等於 coffee 帳號本身是唯讀帳號。工作結束後由管理員決定撤銷或納入正式金鑰清冊。
