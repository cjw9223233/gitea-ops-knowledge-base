# Gitea 主機維護與管理手冊

> 對象：第一次接手本專案的 PM、開發人員與 Linux 維運人員。  
> 主機：`coffee`／`10.253.114.160`；服務名稱：**票務中心系統組**。  
> 版本：1.0；盤點日期：2026-09-21；文件性質：實機盤點＋建議操作程序。  
> 分類：內部文件，包含內網位址、架構及安全缺口，請放在限制存取的文件庫。

本次已以 SSH 唯讀盤點可存取的作業系統、網路狀態、Docker、Gitea 設定、資料庫統計、備份腳本、服務與近期日誌。沒有修改主機、重啟服務、執行備份或還原，也沒有讀取儲存庫程式內容、密碼雜湊、私鑰或權杖內容。

**不能把本文件視為「所有設定皆已驗證」**：Netplan 原始檔、現行防火牆規則、root 排程及完整 SSH 生效設定需要 sudo 密碼，本次無法讀取；備機、交換器、外部備份、Gitea 網頁管理功能及實際還原也未做驗證。各章標示「已確認」「待確認」「建議」，避免把規劃當成現況。

## 目錄

1. [接手先讀：入口、名詞與操作分級](#1-接手先讀入口名詞與操作分級)
2. [系統架構與實機清單](#2-系統架構與實機清單)
3. [網路、連線與防火牆](#3-網路連線與防火牆)
4. [Docker 與 Gitea 設定管理](#4-docker-與-gitea-設定管理)
5. [帳號、權限與專案治理](#5-帳號權限與專案治理)
6. [每日巡檢與例行維護](#6-每日巡檢與例行維護)
7. [備份現況與改善](#7-備份現況與改善)
8. [一致性備份作業程序](#8-一致性備份作業程序)
9. [異機還原與備援切換](#9-異機還原與備援切換)
10. [更新、重啟與回復程序](#10-更新重啟與回復程序)
11. [常見故障排查](#11-常見故障排查)
12. [交接、責任分工與改善清單](#12-交接責任分工與改善清單)
13. [盤點證據、限制與官方參考](#13-盤點證據限制與官方參考)

## 1. 接手先讀：入口、名詞與操作分級

### 1.1 三種入口不要混用

| 用途 | 入口 | 使用的身分 |
|---|---|---|
| 開啟 Gitea 網站 | `http://10.253.114.160:3000/` | 個人的 Gitea 帳號 |
| 管理 Linux 主機 | `ssh coffee@10.253.114.160`，TCP 22 | Linux 帳號；接手後應改用具名維運帳號 |
| Git clone／push | `ssh://git@10.253.114.160:2222/組織或帳號/專案.git` | SSH 使用者為 `git`，公鑰對應個人的 Gitea 帳號 |

`coffee` 不是所有人的 Gitea 登入帳號；Git 用的 2222 也不是 Linux 管理用的 22。正式 clone 網址應從該專案頁面的「複製／Clone」取得，不要把表格中的中文字當成實際專案名稱。

目前網站使用 HTTP，沒有傳輸加密。登入或使用 HTTP Git 認證時，應走已核准且受保護的內網／VPN；優先規劃 HTTPS。沒有觀察到本機 80／443 監聽，但不能據此排除網路外部另有代理。

### 1.2 新手名詞表

| 名詞 | 白話說明 |
|---|---|
| Linux 主機 | 承載整套服務的電腦與作業系統 |
| Docker 映像 image | 啟動程式所需的版本套件，不等於使用者資料 |
| 容器 container | 正在執行的程式環境；刪除、重建容器與刪除資料是不同事情 |
| Docker Compose | 用一份 YAML 檔描述多個容器如何一起運作 |
| bind mount | 把主機上的資料夾提供給容器使用；本機 Gitea 採此方式 |
| PostgreSQL | 儲存使用者、權限、Issue、PR 等結構化資料的資料庫 |
| Git 儲存庫 | 程式碼、提交歷史、分支與標籤；不能取代 Gitea 資料庫 |
| LFS | Git 大型檔案儲存；只複製 Git repository 可能漏掉這些檔案 |
| 白名單 | 指定來源 IP 才能連線；與 Gitea 的帳號權限是不同層次 |
| 備份 | 保存某個時間點的資料，供誤刪或故障後還原 |
| 鏡像 mirror | 把 Git 內容同步到另一個儲存庫；不代表整個 Gitea 可直接接手 |
| 備援 | 主機故障時，另一套可驗證的環境能接替服務 |
| RPO／RTO | 最多能接受遺失多久的資料／最多能接受服務中斷多久 |

### 1.3 指令在哪裡輸入

本手冊的 `bash` 區塊在 **SSH 登入後的 Linux 終端機**執行；`powershell` 區塊在自己的 Windows 電腦執行。不要連同提示符號或說明文字一起貼上。

| 分級 | 意義 | 本手冊中的使用原則 |
|---|---|---|
| 唯讀檢查 | 看狀態、設定或日誌 | 已授權維運人員可執行；日誌仍可能含敏感資訊 |
| 維護變更 | 重啟、修改設定、升級、產生備份 | 由管理員依核准的維護時段執行；本次沒有執行 |
| 災難復原 | 還原、切換 IP、替換資料 | 先核對主機、資料集與備份時間，兩人覆核後執行 |

不要自行執行 `docker system prune --volumes`、遞迴刪除 `/home/Gitea`、遞迴 `chmod 777` 或刪除 PostgreSQL 的 WAL。遇到不懂的錯誤，先記錄，不要反覆重啟或清空資料。

## 2. 系統架構與實機清單

### 2.1 架構

```mermaid
flowchart LR
    U[使用者電腦／核准網路] -->|HTTP 3000| G[Gitea server\n1.23.5-rootless]
    U -->|Git SSH 2222| G
    A[維運人員] -->|Linux SSH 22| H[Ubuntu 主機 coffee\n10.253.114.160]
    G -->|db:5432\nDocker 私有網路| P[PostgreSQL 14.18]
    G --> D[/home/Gitea/data 與 config]
    P --> Q[/home/Gitea/postgres]
    D -.同一顆磁碟上的歷史備份.-> B[/var/backups/coffee]
    Q -.一致性未驗證.-> B
    G -.部分專案推送失敗.-> M[10.253.114.250:3000\n鏡像目的端，未登入盤點]
```

圖中的網路連線仍受防火牆及上游網路限制。本次只確認本機服務回應正常，沒有從所有使用者網段進行可達性測試。

### 2.2 主機與資源

| 項目 | 已確認現況 |
|---|---|
| 主機名稱／作業系統 | `coffee`／Ubuntu 24.04.2 LTS（`/etc/os-release` 回報） |
| 執行中的核心 | `7.0.0-31-generic`；套件來源與選版理由待管理員核對 |
| CPU | Intel Core i7-3540M，4 個邏輯 CPU |
| 記憶體／Swap | 約 3.7 GiB／3.7 GiB；盤點時 Swap 未使用 |
| 磁碟 | 一顆 `sda` 約 476.9 GiB；沒有觀察到 Linux software RAID |
| 根目錄 | `/dev/sda2`，ext4，約 468 GiB；已用 57 GiB、可用 388 GiB、13% |
| EFI | `/dev/sda1`，約 1.1 GiB；另有 `/swap.img` |
| Gitea 檔案資料／DB | `data` 約 4.0 GiB；資料庫邏輯大小約 22 MB，不等於 postgres 資料目錄占用量 |
| 日誌空間 | systemd journal 約 1.3 GB |
| 時區／RTC | Asia/Taipei；硬體時鐘採本地時間 |
| 時間同步 | NTP 服務有啟動，但 `System clock synchronized: no` |
| Docker／Compose | Docker Engine 29.1.3；Compose v2.38.2 |

時間問題會影響備份名稱、日誌排序、憑證及雙因素驗證。一次近乎同時的比較：主機 UTC 為 `03:45:44`，盤點工作站 UTC 為 `02:55:20`，約相差 50 分鐘。這證明兩台時鐘不一致，**不能單憑工作站時間認定哪個是標準時間**；需對照可信任的公司 NTP。手冊中主機日誌與檔案時間均保留原值。

### 2.3 容器與相關服務

| 容器 | 版本／用途 | 狀態與啟動政策 |
|---|---|---|
| `gitea-server-1` | `docker.gitea.com/gitea:1.23.5-rootless` | 執行中；`restart: always`；UID:GID 為 `1000:1000` |
| `gitea-db-1` | `postgres:14`；實際 PostgreSQL 14.18 | 執行中；`restart: always`；資料庫行程帳號 UID:GID 為 `999:999` |
| `mariadb` | `mariadb:latest`，屬於 myxampp | 2026-03-03 起停止；不自動重啟 |
| `myxampp-php-apache-1` | `myxampp-php-apache` | 2026-03-03 起停止；不自動重啟 |

Gitea 的 Compose 專案名稱為 `gitea`，服務名稱是 `server` 與 `db`。兩個執行中的容器未設定 Docker healthcheck，也未設定記憶體／CPU 上限。`Up` 只代表行程存活，要另外驗證網站與資料庫。

Gitea 映像的 `rootless` 指容器內的 Gitea 以非 root 使用者運作。本機 Docker 是系統層 daemon，不能把它解讀為整個 Docker 都是 rootless。

主機另有 apt-cacher-ng、chrony、桌面環境、CUPS、Avahi、Bluetooth 等服務。`fwupd-refresh.service` 顯示失敗；不等於 Gitea 故障。當日 `last -x` 有多筆啟動及 `crash` 標記，原因尚未確認，應查電力、關機排程及開機日誌，不能直接宣稱是硬體故障。

### 2.4 專案規模與管理現況

以下為唯讀資料庫統計，沒有擷取帳號名單或原始碼：

| 項目 | 數量 |
|---|---:|
| 個人使用者／啟用使用者 | 17／17 |
| 站台管理員 | 1 |
| 組織／團隊 | 2／3 |
| 儲存庫 | 93 |
| 私有／非私有儲存庫 | 6／87 |
| 已設定雙因素驗證的帳號 | 0 |
| 分支保護規則 | 0 |
| 外部認證來源／註冊 Runner | 0／0 |

非私有不代表已在 Internet 公開，但目前 `REQUIRE_SIGNIN_VIEW=false`，應由專案負責人確認可連到網站的人是否都應看見這些專案。

## 3. 網路、連線與防火牆

### 3.1 網路設定現況

| 項目 | 已確認值 |
|---|---|
| 使用中的實體網卡 | `eno1`，1 Gbps full duplex，MTU 1500 |
| 主要 IP | `10.253.114.160/24` |
| 同網卡第二個 IP | `192.168.1.2/24` |
| 預設閘道 | `10.253.114.254`，經 `eno1` |
| DNS | `10.36.1.1`、`10.254.1.1`；盤點時使用後者 |
| 第二張網卡 | `enp5s0`，DOWN |
| IPv6 | `eno1` 有 link-local 位址；未看到 global IPv6 位址 |
| Gitea 網路 | `gitea_default`，`172.18.0.0/16`；目前 server `.2`、db `.3` |
| 其他 Docker 網路 | `docker0`：`172.17.0.0/16`；myxampp：`172.19.0.0/16` |
| IPv4／IPv6 forwarding | `1`／`0` |
| 網路管理 | NetworkManager 與 systemd-networkd 均 active；`eno1` 由 Netplan 產生的 networkd 設定管理 |
| 設定檔 | `/etc/netplan/coffee_config.yaml`；root:root、600，本次未讀取內容 |
| 交換器線索 | `networkctl` 顯示連到 `GS2210` port 1；實體位置及 VLAN 待確認 |

`192.168.1.2` 與主 IP 在**同一張網卡**，不代表有兩條獨立網路備援。容器 IP 可能重建後改變，Gitea 連資料庫應維持 `db:5432`，不要改成目前的 `172.18.0.3`。

### 3.2 對外監聽埠

| 埠 | 用途 | 盤點時綁定位址 | 維運重點 |
|---|---|---|---|
| TCP 22 | Linux SSH | IPv4／IPv6 全介面 | 只給維運人員；與 Docker 白名單分開檢查 |
| TCP 3000 | Gitea HTTP | IPv4／IPv6 全介面 | 應限核准來源，規劃 HTTPS |
| TCP 2222 | Gitea 內建 Git SSH | IPv4／IPv6 全介面 | 使用個人 Gitea 公鑰 |
| TCP 5432 | PostgreSQL | 僅容器內，沒有發布主機埠 | 不應為方便而直接對外開放 |
| TCP 3142 | apt-cacher-ng 對應服務 | IPv4／IPv6 全介面 | 核對實際使用者及允許來源 |
| UDP 123 | NTP | IPv4 全介面 | chrony 允許 `192.168.1.0/24` 使用；需確認需求 |
| UDP 5353 | mDNS／Avahi | IPv4／IPv6 全介面 | 評估伺服器是否需要區網探索 |
| TCP 631 | CUPS | loopback | 列印用途待確認 |
| TCP／UDP 53 | systemd-resolved | loopback | 本機 DNS stub |

監聽不代表所有來源都能連入；反過來，UFW inactive 也不代表完全沒有防火牆。

### 3.3 已存在的 Gitea 白名單

現有 `/home/Gitea/gitea-access-rules.sh` 使用 `iptables` 的 `DOCKER-USER` 鏈，允許指定 IP 連入 3000／2222，最後對其他來源 DROP，並執行 `netfilter-persistent save`。本次**只閱讀，沒有執行**。

腳本中的有效 IPv4 清單如下；這是**檔案內容，不是已驗證的生效規則**：

```text
10.253.114.250  10.253.114.117  10.253.111.129
10.253.114.174  10.253.114.175  10.253.111.155
10.253.114.177  10.253.114.157  10.253.114.195
10.253.114.186  10.253.114.194  10.253.114.136
10.253.114.206  10.253.114.210  10.253.114.139
10.253.111.124  10.253.114.198  10.253.114.158
10.253.114.149  10.253.114.129  10.253.114.128
10.253.114.204  172.0.20.162    10.253.111.135
```

`172.0.20.162` 不在 RFC1918 的 `172.16.0.0/12` 私有網段中；這可能是現場規劃，也可能需更正，先找網管確認，不自行修改。

已確認 `netfilter-persistent` enabled 且本次開機載入成功，並存在 `/etc/iptables/rules.v4`、`rules.v6`。但本次無法讀取這兩個檔案及核心內的規則，故不能保證白名單完整、IPv6 有同等限制，或重開機後 Docker 規則順序正確。

Docker 發布埠的封包路徑與一般主機服務不同，不能只看 UFW。現有 iptables 架構下，應檢查 `DOCKER-USER` 與 FORWARD/NAT；不要自行關閉 Docker 的防火牆管理。[Docker 防火牆文件](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

**原腳本的維護風險：**它會清空整條 `DOCKER-USER`，可能刪掉其他專案規則；規則只依目的埠、未限入口網卡與目的容器，可能影響其他同埠流量；而且腳本本身為 777，可被其他本機帳號修改。應先限制腳本寫入權，再由網管重構成專屬鏈，禁止新手直接照舊 README 執行。

### 3.4 新增使用者連線需求

1. PM 記錄申請人、用途、來源 IP、預計到期日及專案。
2. 網管確認是否經 NAT／VPN；真正抵達主機的來源 IP 才是白名單應使用的值。
3. 先由管理員備存**現行**規則、確認 22 埠管理通道及現場主控台可用。
4. 經審核後只加入需要的來源及埠；同時考慮 IPv4、IPv6 與持久化。
5. 從一台允許來源、一台不允許來源分別測 3000／2222；管理用 22 要另外測。
6. 維護時段內驗證重啟 Docker／重開機後效果，保存測試結果與申請單。

只有白名單仍不夠，還須另做第 5 章的 Gitea 帳號及專案授權。

### 3.5 唯讀網路排查

Windows 使用者端：

```powershell
Test-NetConnection 10.253.114.160 -Port 22
Test-NetConnection 10.253.114.160 -Port 3000
Test-NetConnection 10.253.114.160 -Port 2222
```

Linux 主機端：

```bash
ip -br address
ip route
resolvectl status
ss -lntup
networkctl status eno1 --no-pager
```

由有 sudo 權限的人補查，輸出僅存於限制存取的維運紀錄：

```bash
sudo cat /etc/netplan/coffee_config.yaml
sudo iptables -S
sudo iptables -t nat -S
sudo ip6tables -S
sudo nft list ruleset
sudo ufw status verbose
```

### 3.6 IP／DNS 變更與 NAT、NTP 的關聯

**以下為規劃流程，不是目前已執行的變更。**變更 IP 前需同步檢查 Netplan、閘道、DNS、上游 ACL、Gitea `DOMAIN`／`SSH_DOMAIN`／`ROOT_URL`、Git remote、Webhook、鏡像目的端及所有使用者文件。

先取得現場主控台，備存原設定，由管理員檢查 YAML 後使用 `netplan try --timeout 120` 做限時驗證。新連線及原連線都正常才確認保留；超時回復仍需從主控台確認，不能把自動回復當作絕對保障。[Netplan try 說明](https://netplan.readthedocs.io/en/stable/netplan-try/)

另外找到 `/home/coffee/scripts/enable-nat.sh`，內容規劃把 `192.168.1.0/24` 經 `eno1` 做 NAT；目前 IP forwarding 確實為 1，但 NAT 規則未能讀取。主機可能還承擔其他設備的出口或校時功能，移機前要確認，不能只搬 Gitea 就關機。

chrony 設有多個上游 NTP，盤點時全部來源為 `^?`／Reach 0，且啟用 `local stratum 10`。這會在沒有上游時仍以本地時鐘提供時間；`Leap status: Normal` 不等於已對準外部標準。先查公司 NTP、DNS、UDP 123 與網路政策，再於維護時段處理校時及 RTC 設定，避免突然跳時影響服務。

## 4. Docker 與 Gitea 設定管理

### 4.1 重要檔案與資料位置

| 主機路徑 | 容器內路徑／用途 | 備份要求 |
|---|---|---|
| `/home/Gitea/docker-compose.yml` | 啟動定義、映像、埠、DB 環境變數 | 必備；包含密碼，不能貼到公開文件 |
| `/home/Gitea/config/app.ini` | `/etc/gitea/app.ini`，Gitea 設定與機密 | 必備；必須保留原機密值 |
| `/home/Gitea/data` | `/var/lib/gitea`，Git、LFS、附件等 | 完整備份，不要只挑 repositories |
| `/home/Gitea/data/git/repositories` | Git repositories | 必備，包含可能存在的 wiki Git 倉庫 |
| `/home/Gitea/data/git/lfs` | LFS 大型檔案 | 必備 |
| `/home/Gitea/postgres` | `/var/lib/postgresql/data`，PostgreSQL 實體資料 | 一致性實體備份或合格邏輯備份 |
| `/home/Gitea/gitea-access-rules.sh` | Gitea 防火牆維護腳本 | 保存供審閱，不可盲目執行 |
| `/home/Gitea/docs/Gitea-Access-Rules-Readme.md` | 舊有白名單操作說明 | 參考文件，不是生效證據 |
| `/home/coffee/scripts/B_generate_backups.sh` | 現有通用備份腳本 | 保存版本，需改善後才可當可靠備份流程 |
| `/etc/netplan`、`/etc/iptables`、`/etc/chrony`、`/etc/ssh` | 主機連線、安全、校時 | 加密備份；還原時依新主機環境調整 |

`/home/Gitea` 裡另有 2025-04-07 的 `config0407.tar`、`data0407.tar`、`postgres0407.tar`、`gitea0407.tar.gz`。年代久且用途未完整驗證，不能當最新還原點。

### 4.2 已確認的應用設定

| 設定 | 現況與意義 |
|---|---|
| `ROOT_URL` | `http://10.253.114.160:3000/` |
| `RUN_USER`／`RUN_MODE` | `git`／`prod` |
| Git SSH | 內建 SSH 開啟，對外與內部均 2222 |
| 資料庫 | PostgreSQL，`db:5432`，DB 與帳號皆 `gitea` |
| DB TLS | `SSL_MODE=disable`，目前在同機 Docker 網路；跨主機時需重新設計 |
| SQLite PATH | 設定中留有 `gitea.db` 路徑，但實際 DB_TYPE 是 postgres，不要誤備份 SQLite 檔就以為完成 |
| 註冊 | `DISABLE_REGISTRATION=false`；允許自行註冊 |
| 匿名檢視 | `REQUIRE_SIGNIN_VIEW=false` |
| 郵件 | mailer disabled，註冊驗證與通知郵件關閉 |
| CAPTCHA | 關閉 |
| OpenID | 登入與註冊開關為 true；是否實際使用待確認 |
| 組織建立 | 一般使用者預設可建立組織 |
| LFS／離線模式 | LFS 開啟；`OFFLINE_MODE=true`，不代表完全沒有外部連線 |
| 日誌 | console、info；由 Docker 收集 |
| Proxy 信任 | `REVERSE_PROXY_TRUSTED_PROXIES=*`；實際代理與認證設計需收斂及驗證 |

Gitea 的 `GITEA__...` 環境變數在容器啟動時可套用設定；本機 DB 設定由 Compose 提供。只改 `app.ini` 的 DB 密碼，可能在下一次啟動被環境變數覆蓋。[Gitea 1.23 rootless Docker 文件](https://docs.gitea.com/1.23/installation/install-with-docker-rootless/)

### 4.3 日常只讀管理

```bash
cd /home/Gitea
docker compose -p gitea -f docker-compose.yml ps -a
docker compose -p gitea -f docker-compose.yml config --quiet
docker logs --since 30m --tail 100 gitea-server-1
docker logs --since 30m --tail 100 gitea-db-1
docker stats --no-stream gitea-server-1 gitea-db-1
```

`config --quiet` 只做驗證；不要把完整 `docker compose config` 或未篩選的 `docker inspect` 輸出貼進工單，因為可能含環境變數密碼。日誌也要先遮蔽 URL 認證資訊、權杖及個資。

### 4.4 設定變更的標準流程

1. 建立變更單，寫明目的、影響範圍、維護時間、備份及回復方式。
2. 保存原 Compose、app.ini 與實際映像 digest；機密放密碼庫或受限備份。
3. 一次只改一類設定；在測試環境驗證。
4. 執行 `docker compose ... config --quiet` 檢查 YAML；它不保證所有應用參數都正確。
5. Compose 設定變動需要重建容器才會套用；單純 `restart` 不會重新讀入新的 Compose 定義。
6. 用網站、healthz、Git 與權限驗收；紀錄結果並更新本手冊。

## 5. 帳號、權限與專案治理

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

## 6. 每日巡檢與例行維護

### 6.1 五分鐘巡檢

在 Linux 主機執行，均為唯讀：

```bash
hostname
date -Is
uptime
df -h /
df -ih /
free -h
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl --max-time 10 -fsS http://127.0.0.1:3000/api/healthz
chronyc tracking
chronyc sources -n
systemctl --failed --no-pager
```

判讀：Gitea 與 DB 應 Running；healthz 應為 `pass`，且 database/cache 檢查通過；磁碟及 inode 不應接近滿；NTP 應有可信任且已選用的來源。最後仍要由使用者端確認網站與 Git 存取，因為 localhost 檢查不會驗證外部白名單。

### 6.2 維護週期與告警建議

以下是建議門檻，需由 PM 與維運確認，尚未部署自動監控。

| 頻率 | 工作 | 判斷／交付 |
|---|---|---|
| 每日 | healthz、磁碟、時間、容器、最新備份與鏡像結果 | 失敗需派單，不只記「檢查完成」 |
| 每週 | 受限來源外部連線測試、異地備份抽驗、日誌錯誤、更新清單 | 留存結果及負責人 |
| 每月 | 權限清冊、停用帳號、token 到期、容量趨勢 | PM 與管理員共同簽核 |
| 每季 | 隔離環境完整還原、代理管理員演練 | 量測 RTO、確認 RPO、更新手冊 |
| 每次變更後 | 網站、Git、LFS、權限、備份及網路限制 | 全部通過才結案 |

建議磁碟使用率 80% 預警、90% 緊急；新備份超過 26 小時未完成（採每日備份時）告警；healthz 連續失敗約 5 分鐘告警；NTP 長時間無有效來源、鏡像失敗、管理員登入異常也要通知指定人員。

### 6.3 日誌與容量

```bash
docker logs --since 1h --tail 200 gitea-server-1
docker logs --since 1h --tail 200 gitea-db-1
journalctl -u docker -b --no-pager -n 100
journalctl -u ssh -b --no-pager -n 100
journalctl --disk-usage
```

目前兩個容器使用 `json-file` 且 log options 為空，未見輪替上限。建議在 Compose 的兩個 service 分別設定例如 `max-size: 10m`、`max-file: "5"`，經測試重建後驗證，並依保留需求把重要日誌送到外部系統。不要直接 truncate Docker 正在寫入的檔案。[Docker 日誌建議](https://docs.docker.com/engine/install/linux-postinstall/)

### 6.4 服務範圍與電力

由管理員確認 apt-cacher-ng、NAT、NTP、CUPS、Avahi、桌面與遠端桌面功能是否仍有需求，再排程縮減；本次沒有停用任何服務。確認 UPS、硬碟 SMART、備機規格、機房位置及開機後服務自動恢復，這些不能從「容器 restart: always」推論為已具備。

## 7. 備份現況與改善

### 7.1 已找到的備份

| 位置／日期 | 內容 | 限制 |
|---|---|---|
| `/var/backups/coffee/20260919` | etc 約 1.65 MB、home 約 9.05 GB、docker-volumes 約 4.12 MB | 最新看到的資料夾；未驗證壓縮完整性與還原成功 |
| `/var/backups/coffee/20260829` | 同類型三個壓縮檔 | 第二組歷史備份 |
| `/var/backups/coffee/image/20250618/rootfs.fsa` | 約 1.60 GB 的系統映像檔 | 舊映像，不等於目前 Gitea 資料 |
| `/home/Gitea/*0407.tar*` | 2025 年的歷史檔 | 不可作最新還原點 |

本機資料與上述備份都位於同一根分割區，磁碟壞掉會一起失去。未發現目前掛載的 NFS/CIFS 備份磁碟；不能排除外部系統另行拉取備份，但本次沒有證據可確認。

### 7.2 現有備份腳本的實際行為

`/home/coffee/scripts/B_generate_backups.sh` 依序打包 `/etc`、`/home`、`/var/lib/docker/volumes`，保存至日期資料夾，最後刪掉排序後較舊的資料夾，只保留 **2 組**。

應注意：

1. 註解寫「每日／最近 2 天」，實際上沒有保證每日執行；現在兩組日期相隔 21 天。
2. 腳本沒有停 Gitea／PostgreSQL，也沒有 `pg_dump` 或一致性快照程序。若執行時資料庫運作中，直接 tar postgres 目錄不能保證可還原；若外部排程另外停機，本次未能確認。
3. Gitea 用 bind mount，核心資料在 `/home/Gitea`，不在 `/var/lib/docker/volumes`。只拿 docker-volumes 壓縮檔去還原會缺少 Gitea。
4. 腳本未逐步檢查成功狀態，壓縮失敗後仍可能顯示完成並進行舊檔清理；應改善為全部驗證成功後才清理。
5. 備份含其他 home 資料與機密；不要放到所有人可下載的位置。

PostgreSQL 的一般檔案拷貝備份需要資料庫停止，或採用具一致性保證的快照／專用備份機制；不能把運作中目錄的普通 tar 當成可用備份。[PostgreSQL 14 檔案備份要求](https://www.postgresql.org/docs/14/backup-file.html)

`coffee` 沒有個人 crontab；可讀系統 timer 未見專用 Gitea 備份；rsnapshot 的 cron 行全被註解，設定只指向 `/home/foo/bar/`。**root crontab 尚未讀取，所以排程觸發來源仍待確認。**

### 7.3 建議備份政策

下列為待核准目標，不是目前已達成的承諾：

| 項目 | 建議 |
|---|---|
| 目標 RPO | 24 小時；重要專案若要求更低，需重新設計頻率及容量 |
| 目標 RTO | 4 小時，須以實際演練驗證 |
| 保留 | 每日 7 組、每週 4 組、每月 6 組，依容量與公司政策調整 |
| 存放 | 本機暫存＋不同主機／儲存設備的加密副本＋離線或不可變副本 |
| 成功條件 | 命令成功、檔案完整、checksum 通過、外部副本完成、可還原演練通過 |
| 責任 | 維運負責執行，代理人覆核，PM 追蹤異常及演練 |

若不能每天停機，規劃停止 Gitea 寫入後的 DB 邏輯備份與檔案備份，或由熟悉 PostgreSQL 的人設計一致性快照／PITR。`pg_dump` 只保證資料庫本身的一致性，不能自動協調 Git、LFS 與附件。[pg_dump 文件](https://www.postgresql.org/docs/14/app-pgdump.html)

## 8. 一致性備份作業程序

### 8.1 適用條件

這是**建議的停機冷備份程序，尚未在正式機執行或演練**。適合目前單機、資料量不大的架構。備份期間網站、Git 與資料庫會停止；由管理員在核准時段逐段執行，不要把整章一次貼上。

事前要有：可用 sudo、現場／第二條管理通道、足夠暫存空間、外部加密儲存、值班聯絡人。記錄使用者可接受的停機時間；若超過時限，優先恢復原服務並把本次備份標記失敗。

### 8.2 準備：仍未停服務

以下切換 root 是未來由人員執行的維護程序，不是本次 SSH 盤點操作。

```bash
sudo -i
umask 077
cd /home/Gitea
docker compose -p gitea -f docker-compose.yml config --quiet
df -h /var/backups
du -sh config data postgres
```

確認沒有錯誤後，在**同一個 root shell**建立獨立目錄。此新目錄不同於舊腳本的自動清理目錄：

```bash
BACKUP_DIR="/var/backups/gitea-approved/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
printf '%s\n' "$BACKUP_DIR"
docker image inspect docker.gitea.com/gitea:1.23.5-rootless postgres:14 \
  --format '{{.Id}} {{json .RepoDigests}}' > "$BACKUP_DIR/images.txt"
```

映像名稱要依當次實際版本調整。建議將**當時正在執行的精確 image ID**用 `docker image save` 另存至受控外部儲存，記錄對應版本，避免災難時 registry 不可用。不要只記浮動的 `postgres:14` 標籤。

### 8.3 停止並確認

```bash
docker compose -p gitea -f docker-compose.yml stop -t 60 server
docker compose -p gitea -f docker-compose.yml stop -t 60 db
docker inspect --format '{{.Name}} {{.State.Status}} exit={{.State.ExitCode}}' \
  gitea-server-1 gitea-db-1
docker logs --tail 30 gitea-db-1
```

兩個容器必須都停止，並確認 PostgreSQL 日誌有正常完成 shutdown。如果超時強制終止、退出狀態異常或資料庫沒有正常關閉，停止備份流程，交管理員處理；不要把 crash 狀態直接當成合格冷備份。

### 8.4 打包、驗證、恢復原服務

```bash
tar --acls --xattrs --numeric-owner -czpf "$BACKUP_DIR/gitea-cold.tar.gz" \
  -C /home/Gitea docker-compose.yml config data postgres gitea-access-rules.sh docs
```

立即檢查退出碼：

```bash
echo $?
```

只有 `0` 才能標記「打包成功」；非 0 要記錄錯誤。無論備份是否成功，都要依下列順序及健康檢查恢復原服務，避免因備份失敗讓正式站一直停機：

```bash
docker compose -p gitea -f docker-compose.yml start db
docker exec gitea-db-1 pg_isready -U gitea -d gitea
```

等到資料庫回報 `accepting connections`，再執行：

```bash
docker compose -p gitea -f docker-compose.yml start server
curl --max-time 10 -fsS http://127.0.0.1:3000/api/healthz
docker compose -p gitea -f docker-compose.yml ps
```

服務恢復後，對已成功的備份做完整性檢查：

```bash
gzip -t "$BACKUP_DIR/gitea-cold.tar.gz"
tar -tzf "$BACKUP_DIR/gitea-cold.tar.gz" > "$BACKUP_DIR/file-list.txt"
cd "$BACKUP_DIR"
sha256sum gitea-cold.tar.gz images.txt > SHA256SUMS
sha256sum -c SHA256SUMS
```

每一步都須成功。壓縮與 checksum 驗證只證明檔案傳輸／格式完整，**不是還原成功證明**。另存必要主機設定；將備份以公司核准工具加密傳到不同設備，在目的端再驗 checksum。所有工作完成前不刪上一份合格備份。

### 8.5 備份紀錄格式

```text
備份編號／操作人／覆核人：
正式主機與應用版本／映像 digest：
可信時間來源、停機起訖、資料截止時間：
打包命令結果／檔案大小／SHA-256：
外部副本位置（不填密碼）與驗證結果：
網站、DB、Git 恢復結果：
隔離還原演練日期與結果：
異常、處理單號、下次改善：
```

## 9. 異機還原與備援切換

### 9.1 目前是否已經有備援？

**尚無足夠證據確認有可接手的整站備援。**本機只有一顆可見磁碟；PostgreSQL 沒有連線中的 replication standby，`archive_mode=off`，本次也沒看到完整切換流程或外部一致性備份。

近期 Gitea 日誌顯示 `cjw/ECMU` 與 `cjw/myXAMPP` 的 push mirror 連到 `10.253.114.250:3000` 失敗，訊息為無法連線；這是已確認的故障症狀，不足以判定是對方停機、防火牆或路由問題。本次未登入、掃描或修改 `.250`。

即使 Git mirror 修好，也不會自動備份完整的使用者、權限、Issue、PR、附件、Packages、機密及主機設定；LFS 與其他 Git 擴充內容也要另外驗證。鏡像同步、備份、整站備援須分別管理。

### 9.2 建議的備援形態

先建立**可還原的冷備機**：準備相容 Linux、Docker／Compose、足夠磁碟及離線映像，每日取得已驗證的加密備份，至少每季演練。尚未需要自動切換前，不必急著做多台同時寫入同一份資料。

若 PM 要求更短 RPO/RTO，再評估 DB replication、Git/LFS 檔案一致性、共享儲存、故障判斷與避免雙主寫入的機制，另立專案；不能只複製 Compose 就稱為高可用。

### 9.3 先做隔離還原演練

以下程序只適用第 8 章產出的 `gitea-cold.tar.gz`，**不直接適用舊的 home-backup 或 rootfs.fsa**。

1. 在隔離新主機安裝相容 Docker／Compose；正式機保持不動。使用新 IP，不占用 `.160`。
2. 防火牆只讓演練人員連入，並限制演練機對外連線，避免還原後的鏡像、Webhook、排程或郵件碰到正式系統。
3. 複製備份與 checksum，驗證全部通過；檢查 archive 檔案清單沒有非預期路徑。
4. 使用備份記錄的精確映像版本／digest，或載入保留的映像；不要直接拉取 latest。
5. 以 root 在**空的新主機目標目錄**還原；若 `/home/Gitea` 已存在，停止並由管理員確認，不覆蓋。

範例（`RESTORE_DIR` 必須改為新主機上已驗證的備份位置）：

```bash
sudo -i
RESTORE_DIR=/srv/restore-input/請替換成備份編號
cd "$RESTORE_DIR"
sha256sum -c SHA256SUMS
test ! -e /home/Gitea
```

**確認最後一個命令退出碼為 0 才繼續**：

```bash
mkdir -p /home/Gitea
tar --acls --xattrs --numeric-owner -xzpf "$RESTORE_DIR/gitea-cold.tar.gz" \
  -C /home/Gitea
cd /home/Gitea
docker compose -p gitea -f docker-compose.yml config --quiet
```

6. 核對數字 UID/GID。Gitea 使用 1000；postgres 原目錄 UID 999。保留原始擁有者，不因新主機顯示不同使用者名稱就遞迴改權限。
7. 在演練副本調整 `ROOT_URL`、`DOMAIN`、`SSH_DOMAIN`、監聽埠及精確映像引用；不要改正式機。恢復相同 Gitea／PostgreSQL 版本，先驗證成功再談升級。
8. 先啟動 DB，待可連線後再啟動應用：

```bash
docker compose -p gitea -f docker-compose.yml up -d db
docker compose -p gitea -f docker-compose.yml exec -T db pg_isready -U gitea -d gitea
```

DB 就緒後：

```bash
docker compose -p gitea -f docker-compose.yml up -d server
curl --max-time 10 -fsS http://127.0.0.1:3000/api/healthz
```

啟動時維持外連隔離；由管理員停用演練副本中的 mirror／Webhook 等背景整合，再逐項驗證。保留原 app.ini 的機密及 SSH host key，可維持相容性；但演練機也因此含正式機密，完成後要受控封存或銷毀。

### 9.4 還原驗收清單

- [ ] Gitea 及 DB 正常啟動，沒有反覆重新啟動。
- [ ] healthz 的 database/cache 通過。
- [ ] 管理員及一般帳號登入正常；MFA、復原途徑可用。
- [ ] 使用者／組織／儲存庫數量與該次備份清冊一致。
- [ ] 抽驗重要專案的分支、Tag、Commit、Issue、PR、Wiki、附件、Release、LFS、Packages。
- [ ] 從核准測試電腦 clone，並在**測試專案** push／建立 PR。
- [ ] Read 帳號無法寫入，受保護分支規則正確。
- [ ] SSH host key 變更有正式核對，不要求使用者盲目接受陌生指紋。
- [ ] 鏡像、Webhook、郵件及排程未誤觸正式外部系統。
- [ ] 記錄實際還原耗時、資料截止點及未恢復項目，由 PM 簽核。

### 9.5 正式切換與回切

PM 宣布維護開始，停止使用者寫入；取得最後一致性備份並驗證。先確保原服務不再接受寫入，才由網管切換 IP／DNS／入口。**不能讓舊機與新機同時持有 `.160`，也不能讓兩邊各自接受新提交。**

新站驗收通過後才宣布恢復；舊站保留為隔離的回復來源。若新站已有使用者寫入後才要回切，需先規劃資料回收與一致性處理，不能直接開啟舊站而丟掉新資料。NAT、NTP、apt proxy 等附帶功能須另外列入切換清單。

## 10. 更新、重啟與回復程序

### 10.1 版本管理優先事項

目前 Gitea 1.23.5、PostgreSQL 14.18 都應納入更新評估。PostgreSQL 官方版本政策列出 14 的終止支援日期為 **2026-11-12**，須提前安排大版本遷移，不只更新容器標籤。[PostgreSQL 支援政策](https://www.postgresql.org/support/versioning/)

先在隔離副本驗證 Gitea 支援的升級路徑、DB 相容性及重大變更，再排正式升級。本機 Docker 為 Ubuntu 套件來源的 `docker.io`，不要未評估就混裝另一套來源。`unattended-upgrades` enabled 也不代表 Gitea 映像會自動更新。

### 10.2 一般重啟

**維護變更：**先確認沒有備份、還原或使用者關鍵操作，再於核准時間執行。僅應用異常且 DB 正常時，先處理 Gitea，不要整台主機重開。

```bash
cd /home/Gitea
docker compose -p gitea -f docker-compose.yml restart server
curl --max-time 10 -fsS http://127.0.0.1:3000/api/healthz
docker logs --since 5m --tail 100 gitea-server-1
```

需整組重啟時，先停 server，再停 db；先啟動 db 並確認就緒，再啟動 server，順序同第 8 章。`depends_on` 目前只要求 DB service 已啟動，不保證資料庫已就緒。

### 10.3 Gitea 升級

1. PM 核准維護時段、目標版本及回復時限。
2. 完成一致性備份與隔離還原驗證，記錄原映像 digest。
3. 僅調整 `server` 的映像至已驗證版本；維持 rootless 系列，避免無意改變資料路徑。
4. 驗證 Compose 後，只更新應用服務，避免順便拉動 `postgres:14`。

```bash
# 僅限已完成備份、測試及修改目標版本後的維護時段
cd /home/Gitea
docker compose -p gitea -f docker-compose.yml config --quiet
docker compose -p gitea -f docker-compose.yml pull server
docker compose -p gitea -f docker-compose.yml up -d --no-deps server
```

5. 檢查 migration 日誌、網站、Git、LFS、權限及整合功能。
6. 若失敗，先停止新版本寫入。資料庫若已遷移，不能只換回舊映像；應用第 9 章還原同時間點的設定、檔案與 DB，並告知可能遺失升級後資料。[Gitea 升級說明](https://docs.gitea.com/1.23/installation/upgrade-from-gitea/)

### 10.4 PostgreSQL 更新

同一 major 的小版本與跨 major 是不同工作。`postgres:14` 是浮動標籤，下一次 pull 可能取得新小版本；應測試後固定精確版本／digest。跨到 15、16 等不能只改映像標籤後直接沿用舊資料目錄，需依 PostgreSQL 正式升級方法與 Gitea 相容性規劃遷移。

資料庫應用帳號 `gitea` 目前 `rolsuper=true`、可建角色及 DB，權限偏高。降低權限要先盤點物件擁有者及 Gitea migration 需求，先在測試副本驗證，不可直接剝奪權限造成升級失敗。

## 11. 常見故障排查

### 11.1 排查原則

先確認影響範圍：只有一人、一個網段、一個專案，還是所有服務？記錄發生時間與時區；目前主機時鐘有偏差，與其他設備對照時要註明。收集最少必要證據後再決定是否變更。

| 症狀 | 先查 | 下一步 |
|---|---|---|
| 網頁打不開 | Windows 3000 埠測試；主機 localhost healthz | 本機正常而遠端失敗，查白名單／路由；本機也失敗再查容器與 DB |
| Linux SSH 登入失敗 | 是否用 22、正確帳號／金鑰、本機私鑰可讀 | 伺服器接受公鑰但簽署失敗時先查用戶端，不急著重編 authorized_keys |
| Git SSH 失敗 | 是否用 2222 及 `git`；公鑰是否加在 Gitea | 查看實際 clone URL 與 repository 權限；不把 Linux 公鑰授權當成 Gitea 授權 |
| DB 無法連線 | `docker ps`、DB 日誌、磁碟、`pg_isready` | 檢查 `db:5432` 與 Compose／app.ini 設定，禁止直接改資料表試運氣 |
| 磁碟接近滿 | `df -h`、`df -ih`、journal、備份與容器日誌容量 | 管理員确认保留政策後清理，不刪 DB/WAL 或未確認用途的 volume |
| 備份有檔案卻不能還原 | 命令退出碼、壓縮檢查、checksum、是否一致性備份 | 用隔離環境演練；不要在正式資料上試解壓 |
| 鏡像同步失敗 | 目的端服務、來源到目的端路由／ACL、時間 | 先排可達性，再查認證；不要重設密碼掩蓋連線問題 |
| TOTP／token 時效異常 | NTP、時區、主機與使用者時間 | 先核對可信時間，再處理帳號復原 |
| 開機後 Gitea 未恢復 | Docker service、容器 restart policy、DB readiness、網路 | 依 DB → server 次序檢查，不連續硬重開 |

### 11.2 PostgreSQL 只讀確認

```bash
docker exec gitea-db-1 pg_isready -U gitea -d gitea
docker exec -e PGOPTIONS='-c default_transaction_read_only=on -c statement_timeout=5000' \
  gitea-db-1 psql -X -U gitea -d gitea \
  -c 'SELECT current_database(), current_user, pg_size_pretty(pg_database_size(current_database()));'
```

此命令沿用容器既有本地認證，不把密碼寫到命令列。如果認證策略日後改變，透過正式機密管理方式處理，不要臨時改成無密碼信任。

### 11.3 本次已觀察到的日誌事件

Gitea 近期抽樣有 4 筆 error，對應兩個儲存庫各兩筆推送鏡像失敗；另有 5 筆啟動時 schema default 差異 warning。當時 localhost 首頁 HTTP 200、healthz pass，DB 近期抽樣沒有 ERROR/FATAL/PANIC。這是有限時間窗的結果，不代表全部歷史日誌都沒有問題。

schema warning 要在升級測試時追蹤，不手工改 DB 預設值。鏡像失敗應另開事件單，指派 `.160` 維運、`.250` 負責人及網管共同排查。

### 11.4 事件回報格式

```text
發生／發現時間（含時區與時鐘偏差說明）：
影響對象與功能：
來源 IP、服務埠、專案（必要時遮蔽）：
錯誤訊息與有限範圍日誌：
網站／healthz／容器／磁碟／DB 狀態：
最近變更及備份時間：
已做的檢查、是否有執行變更：
事件負責人、下一次回報時間、結案條件：
```

## 12. 交接、責任分工與改善清單

### 12.1 專案責任表

姓名、代理人與聯絡方式由 PM 補齊；不要只寫「資訊人員」。

| 角色 | 責任 | 正／代理人 |
|---|---|---|
| PM／服務負責人 | 需求、權限核准、維護公告、RPO/RTO、風險排序 | 待填 |
| Linux／Docker 管理員 | 主機、容器、備份、還原、更新、事件處理 | 待填 |
| Gitea 站台管理員 | 帳號、組織、機密、應用設定、權限稽核 | 待填；目前只確認 1 個管理員帳號 |
| 網管 | IP、DNS、VLAN、ACL、防火牆、NTP、切換 | 待填 |
| 各專案維護者 | 程式碼審查、分支保護、專案文件及驗收 | 每個專案各自指定 |
| 備機／鏡像端負責人 | `.250` 角色、容量、同步及接手測試 | 待填，不預設其已是合格備機 |

### 12.2 優先改善項目

建議時程以交接開始日計，需依團隊資源核准，沒有在本次自動套用。

| 優先級／建議期限 | 項目 | 驗收標準 |
|---|---|---|
| P1／1 週內 | 建立可信、異機保存的一致性備份 | 完成一次隔離完整還原；可量測 RPO/RTO |
| P1／1 週內 | 處理 NTP 無上游與時間差 | 有可信 selected source；主機與標準時間差符合政策 |
| P1／1 週內 | 調查 `.250` 推送鏡像失敗 | 兩個已知專案成功同步；確認鏡像涵蓋範圍與責任人 |
| P1／1 週內 | 收斂防火牆腳本與機密檔權限 | 非核准帳號不可改寫；Gitea/DB 啟動及備份仍正常 |
| P1／1 週內 | 確認公開範圍、註冊與管理員代理 | 87 個非私有儲存庫分類核准；至少有可用代理管理流程 |
| P1／2 週內 | 校時後啟用管理員 MFA，保護關鍵分支 | MFA 復原演練成功；關鍵分支禁止未審核寫入 |
| P1／2 週內 | 驗證防火牆、IPv6、重開機持久化 | 允許來源通過、拒絕來源失敗，並保存證據 |
| P1／終止支援前 | PostgreSQL 14 遷移計畫 | 2026-11-12 前完成受支援版本切換及還原演練 |
| P2／1 個月內 | HTTPS、Gitea 更新與 DB 最小權限 | 測試通過、核准維護、可回復 |
| P2／1 個月內 | 自動監控、日誌輪替、備份失敗告警 | 模擬失敗時指定人收到通知 |
| P2／1 個月內 | 確認頻繁開機原因與 UPS／磁碟健康 | 有事件結論與電力／硬碟檢查紀錄 |
| P3／1 個月內 | XAMPP 遺留資源及多用途服務整頓 | 找到 owner、依資料保留政策處理，不直接清掉 |

### 12.3 新人第一天檢核

- [ ] 已知道 PM、管理員、代理人及緊急聯絡方式。
- [ ] 能區分 Linux SSH 22、Git SSH 2222、Web 3000。
- [ ] 能用個人帳號看到應看的專案，不能看到不應看的資料。
- [ ] 開發者能 clone 測試專案、建立分支及 PR。
- [ ] 維運人員能執行第 6 章唯讀巡檢並解釋結果。
- [ ] 知道最新**驗證成功**的備份位置及還原負責人。
- [ ] 知道機密在哪裡申請，不在聊天、Git 或手冊貼密碼。
- [ ] 已讀取所屬專案的建置、部署、測試及回復文件。

### 12.4 交接完成條件

只有「能登入」不代表交接完成。代理人必須獨立完成一次巡檢、一次測試專案權限驗證及一次隔離還原；PM 確認服務範圍、維護公告流程、RPO/RTO 與事件責任已有人承擔。

## 13. 盤點證據、限制與官方參考

### 13.1 證據範圍

| 證據類別 | 本次已完成 | 未完成／原因 |
|---|---|---|
| 主機 | OS、CPU、RAM、磁碟、掛載、啟用服務、近期開機紀錄 | SMART、UPS、BIOS／實體機房未驗證 |
| 網路 | 位址、路由、DNS、監聽、networkctl、forwarding | Netplan 原文、核心防火牆、上游 ACL／VLAN 需額外權限或網管證據 |
| Docker | 全部容器清單、掛載、映像、重啟政策、網路、資源及日誌設定 | 未啟停容器、未更新映像 |
| Gitea | 遮蔽機密後的設定、localhost 首頁／healthz、版本 | 未登入網站逐項操作、未讀程式庫內容、未提交測試資料 |
| PostgreSQL | 強制唯讀 session 的統計、角色旗標、replication／archive 狀態 | 未匯出業務資料、未改權限或 schema |
| 備份 | 腳本與有限日誌、目錄及檔案大小、可讀排程 | 未解壓大檔、未作完整性與還原演練；root 排程不可讀 |
| 備援 | 從本機日誌觀察到鏡像目的端連線失敗 | `.250` 與其他設備不在本次登入範圍 |

每次實際送至本機的 SSH 指令已在盤點工作區保留時間戳、主機、命令與結果紀錄。原始稽核可能含內部路徑與網路資訊，沒有直接附入可廣泛散發的手冊；需要稽核時由文件負責人受控提供。敏感設定採白名單輸出或遮蔽，未把完整機密檔收進本文件。

### 13.2 管理員補查清單

在主機本地或核准 SSH 管道自行輸入 sudo 密碼，不把密碼提供到聊天。以下是**唯讀命令**，輸出需遮蔽敏感內容後才轉交：

```bash
sudo crontab -l
sudo cat /etc/netplan/coffee_config.yaml
sudo iptables -S
sudo iptables -t nat -S
sudo ip6tables -S
sudo nft list ruleset
sudo sshd -T
```

另確認：備份觸發來源與最後成功退出碼、是否有外部副本、完整還原記錄、主機每日關機政策、可信 NTP、`.250` 的角色及狀態、具名管理員、通知窗口、維護時段。若 SSH 有 Match 規則，`sshd -T` 還要配合指定連線條件核對，不能只看一般輸出。

### 13.3 官方文件

操作前以當次採用的版本文件為準；本手冊的現況數值來自實機，下面文件用於支援操作方法，不能取代現場證據。

- [Gitea 1.23：rootless Docker 安裝與資料路徑](https://docs.gitea.com/1.23/installation/install-with-docker-rootless/)
- [Gitea 1.23：備份與還原](https://docs.gitea.com/1.23/administration/backup-and-restore/)
- [Gitea 1.23：權限](https://docs.gitea.com/1.23/usage/permissions/)
- [Gitea 1.23：升級](https://docs.gitea.com/1.23/installation/upgrade-from-gitea/)
- [Docker：防火牆與封包路徑](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [Docker：iptables／DOCKER-USER](https://docs.docker.com/engine/network/firewall-iptables/)
- [Docker：Linux 權限與日誌管理](https://docs.docker.com/engine/install/linux-postinstall/)
- [PostgreSQL 14：檔案系統備份](https://www.postgresql.org/docs/14/backup-file.html)
- [PostgreSQL 14：pg_dump](https://www.postgresql.org/docs/14/app-pgdump.html)
- [PostgreSQL：版本支援政策](https://www.postgresql.org/support/versioning/)
- [Netplan：try 與限時確認](https://netplan.readthedocs.io/en/stable/netplan-try/)

### 13.4 文件維護紀錄

| 日期 | 版本 | 變更 |
|---|---|---|
| 2026-09-21 | 1.0 | 依唯讀實機盤點建立；備份／還原程序為待演練方案，sudo 與外部設備缺口明列 |

後續每次修改 IP、版本、資料路徑、帳號政策、備份排程或備援方式，都要更新本手冊、記錄核准單號，並由另一位人員覆核。
