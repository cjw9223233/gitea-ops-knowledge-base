## 2026-10-05 補驗證

| 項目 | 結果 |
|---|---|
| 備機路由 | 192.168.1.3 經 eno1，來源為 192.168.1.2 |
| 備機網路 | 鄰居可解析、TCP 22 可達 |
| SSH | coffee 非互動登入成功；新版透過 runuser 使用相同身分 |
| eno1 | 協商 100 Mb/s、全雙工；若預期千兆，另查線材與交換器 |
| 本機磁碟 | 468G 分割區，可用 338G（盤點快照） |
| 備機磁碟 | /home/coffee 所在分割區可用約 202 GiB（盤點快照） |
| 校時 | chrony 沒有有效外部來源，尚待修復 |

## 原始架構盤點（2026-09-21）

以下版本、位址與數值是當日紀錄；有後續更新時以本頁上方與變更紀錄為準。

### 2. 系統架構與實機清單

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



### 3. 網路、連線與防火牆

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

```powershell-ro
Test-NetConnection 10.253.114.160 -Port 22
Test-NetConnection 10.253.114.160 -Port 3000
Test-NetConnection 10.253.114.160 -Port 2222
```

Linux 主機端：

```bash-ro
ip -br address
ip route
resolvectl status
ss -lntup
networkctl status eno1 --no-pager
```

由有 sudo 權限的人補查，輸出僅存於限制存取的維運紀錄：

```bash-ro
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



### 4. Docker 與 Gitea 設定管理

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

```bash-ro
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
