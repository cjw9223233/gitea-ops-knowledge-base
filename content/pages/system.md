## 一頁摘要

| 面向 | 重點 | 資料日期 |
|---|---|---|
| 服務 | Docker 內的 Gitea 1.23.5-rootless 與 PostgreSQL 14；對外 3000／2222 | 2026-09-21／10-05 |
| 主機 | 單一台 Ubuntu 24.04，單顆 SSD、沒有 RAID | 2026-09-21 |
| 資料位置 | `/home/Gitea`（compose、config、data、postgres） | 2026-09-21 |
| 已知異常 | 校時失敗、22:00 後被喚醒、syslog 洗版、TCP 9090 未確認 | 2026-10-06 |
| 網路設定 | 已獨立成 [網路與連線](network.html) | — |

## 主機與資源

| 項目 | 現況 | 資料日期 |
|---|---|---|
| 主機名稱／系統 | `coffee`／Ubuntu 24.04.2 LTS | 2026-10-05 |
| 核心 | **`7.0.0-34-generic`**（9/25 自動升級；`unattended-upgrades` 為 active） | 2026-10-06 |
| CPU／記憶體 | Intel Core i7-3540M（4 個邏輯 CPU）／約 3.7 GiB，Swap 約 3.7 GiB | 2026-09-21 |
| 磁碟 | 一顆 `sda` 約 476.9 GiB；沒有 software RAID；系統碟曾有 BIOS 偶爾找不到的現象，見 [硬碟與開機排查](hardware.html) | 2026-09-21 |
| 根目錄 | `/dev/sda2` ext4，468G，已用 107G、可用 338G（24%） | 2026-10-05 |
| EFI／swap | `/dev/sda1` 約 1.1 GiB；另有 `/swap.img` | 2026-09-21 |
| Gitea 檔案資料／資料庫 | `data` 約 4.0 GiB；資料庫邏輯大小約 22 MB | 2026-09-21 |
| systemd journal | 約 1.3 GB | 2026-09-21 |
| 時區／RTC | Asia/Taipei；硬體時鐘採**本地時間** | 2026-10-06 |
| 時間同步 | 服務啟動但 `System clock synchronized: no`，見 [網路與連線](network.html) | 2026-10-06 |
| Docker／Compose | Docker Engine 29.1.3；Compose v2.38.2 | 2026-09-21 |
| BIOS | 2012 年 AMI 4.6.5；OEM 欄位不足以選擇可刷入的更新檔 | 2026-10-05 |

系統時鐘錯誤會影響備份名稱、日誌排序、憑證與雙因素驗證。

## 服務與容器

| 名稱 | 版本／用途 | 狀態與政策 | 資料日期 |
|---|---|---|---|
| `gitea-server-1` | `docker.gitea.com/gitea:1.23.5-rootless`；容器內 UID:GID 1000:1000 | 執行中；`restart: always` | 2026-10-05（healthz pass） |
| `gitea-db-1` | `postgres:14`（實際 14.18）；行程 UID:GID 999:999 | 執行中；`restart: always` | 2026-10-05 |
| `mariadb`、`myxampp-php-apache-1` | myXAMPP 專案的資料庫與 Web | 9/21 為停止、不自動重啟；**現況待確認**：`/home/myXAMPP` 於 10/6 有異動，同日出現未確認的 TCP 9090 | 2026-10-06 |
| `apt-cacher-ng` | APT 套件快取，TCP 3142 | 運行中 | 2026-10-06 |
| `chrony` | NTP 客戶端／伺服器 | 運行中但沒有有效來源 | 2026-10-06 |
| `cron`、`ssh` | 排程與維運 SSH | active | 2026-10-06 |
| `ufw`、`fail2ban` | 防火牆前端／暴力破解防護 | **inactive** | 2026-10-06 |
| `netfilter-persistent` | 載入 iptables 規則 | active | 2026-10-06 |
| 桌面環境、CUPS、Avahi、Bluetooth | 一般桌面主機附帶 | 運行中；伺服器多半不需要 | 2026-09-21 |

Gitea 的 Compose 專案名是 `gitea`，服務名稱是 `server` 與 `db`。兩個執行中的容器**沒有** Docker healthcheck，也沒有記憶體或 CPU 上限，`Up` 只代表行程存活，要另外驗證網站與資料庫。映像的 `rootless` 指容器內的 Gitea 用非 root 使用者運作；主機上的 Docker daemon 仍是系統層、root 執行。

## Gitea 設定重點

| 設定 | 現況 | 風險或建議 |
|---|---|---|
| `ROOT_URL` | `http://10.253.114.160:3000/` | 明文 HTTP；規劃 HTTPS 與正式網域，改網址要同步 Webhook、鏡像、文件 |
| `RUN_USER`／`RUN_MODE` | `git`／`prod` | 正常 |
| Git SSH | 內建，對外與內部皆 2222 | 使用個人 Gitea 公鑰 |
| 資料庫 | PostgreSQL `db:5432`，DB 與帳號皆 `gitea` | 設定檔中留有 SQLite 路徑但實際是 PostgreSQL，別誤備份 SQLite 以為完成 |
| DB TLS | `SSL_MODE=disable` | 同機 Docker 網路尚可；跨主機要重新設計 |
| 註冊 | `DISABLE_REGISTRATION=false`，可自行註冊 | 評估是否關閉，改為管理員建立 |
| 匿名檢視 | `REQUIRE_SIGNIN_VIEW=false` | 能連到網站的人都看得到非私有專案；請專案負責人確認 |
| 郵件 | mailer disabled | 不會寄註冊驗證、通知與重設信 |
| CAPTCHA／OpenID | CAPTCHA 關閉；OpenID 登入註冊開關為 true | OpenID 是否實際使用待確認 |
| 組織建立 | 一般使用者預設可建立 | 視治理需求收斂 |
| LFS／離線模式 | LFS 開啟；`OFFLINE_MODE=true` | 離線模式不代表完全沒有外部連線 |
| 日誌 | console、info，由 Docker 收集 | — |
| Proxy 信任 | `REVERSE_PROXY_TRUSTED_PROXIES=*` | 全部信任，需配合實際代理與認證設計收斂 |

資料日期 2026-09-21。Gitea 的 `GITEA__…` 環境變數會在容器啟動時套用；只改 `app.ini` 的資料庫密碼可能在下次啟動被環境變數覆蓋。[Gitea 1.23 rootless Docker 文件](https://docs.gitea.com/1.23/installation/install-with-docker-rootless/)

## 專案規模（唯讀資料庫統計，2026-09-21）

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

統計只含數量，沒有擷取帳號名單或原始碼。非私有不等於已在 Internet 公開。

## 重要檔案與備份要求

| 主機路徑 | 容器內路徑／用途 | 備份要求 |
|---|---|---|
| `/home/Gitea/docker-compose.yml` | 啟動定義、映像、埠、DB 環境變數 | 必備；含密碼，不能貼到公開文件 |
| `/home/Gitea/config/app.ini` | `/etc/gitea/app.ini`，Gitea 設定與機密 | 必備；必須保留原機密值 |
| `/home/Gitea/data` | `/var/lib/gitea`，Git、LFS、附件 | 完整備份，不要只挑 repositories |
| `/home/Gitea/data/git/repositories` | Git 儲存庫（含 wiki） | 必備 |
| `/home/Gitea/data/git/lfs` | LFS 大型檔案 | 必備 |
| `/home/Gitea/postgres` | `/var/lib/postgresql/data`，資料庫實體資料 | 一致性實體備份 |
| `/home/Gitea/gitea-access-rules.sh` | 白名單腳本 | 保存供審閱，不可盲目執行 |
| `/etc/netplan`、`/etc/iptables`、`/etc/chrony`、`/etc/ssh` | 連線、安全、校時 | 加密備份；還原到新主機時要依環境調整 |

`/home/Gitea` 內另有 2025-04-07 的 `config0407.tar`、`data0407.tar`、`postgres0407.tar`、`gitea0407.tar.gz`，年代久且用途未完整驗證，**不能當成最新還原點**。

## 容量與趨勢

| 項目 | 數值 | 資料日期 |
|---|---|---|
| 主機根目錄 | 已用 24%，可用 338G | 2026-10-05 |
| 備機 `/` | 457G，已用 236G（55%），可用 199G | 2026-10-06 |
| 每日備份大小 | 約 3 GiB（由備機可用空間變化**估算**；精確值請用 `du -sh`） | 2026-10-06 |
| syslog | 約 170 MB／天（洗版，見下節） | 2026-10-04 |
| 本機備份累積 | `/var/backups/gitea-maintenance` 大小未讀取（root 專用）；外送失敗期間會累積 | — |

## 已知問題：日誌被 snap 重啟迴圈洗版

**症狀**：`/var/log/syslog` 每天約 170 MB，開關機訊息被淹沒。
**證據**：`snapd-desktop-integration` 約每 2 秒重啟一次，`restart counter` 在 10/4 06:00 為 12786、21:56 為 38292（16 小時約 2.5 萬次）；原因訊息為缺少 `gpu-2404-provider-wrapper` 內容 snap。`firmware-updater` 通知器也有同類訊息。
**影響**：磁碟與 CPU 浪費，也讓排查開關機問題更困難。
**建議**：先確認這台主機是否真的需要桌面整合；確認不需要再由管理員停用或移除該 snap（變更，需先確認用途）。

唯讀確認：

```bash-ro
ls -lh /var/log/syslog /var/log/syslog.1
```

```bash-ro
grep -c 'snapd-desktop-integration' /var/log/syslog
```

## 每晚 22:00 重開機對服務的影響

目前每晚約 22:00 機器會關機再立刻開機，Gitea 與 PostgreSQL 因 `restart: always` 會自動回來，使用者感受是**約 1–2 分鐘不可用**。起因與驗證步驟見 [排程與電源](schedule.html)。若有人在這個時段推送程式碼，可能失敗，請提醒使用者重試。

## 日常只讀管理

```bash-ro
cd /home/Gitea && docker compose -p gitea -f docker-compose.yml ps -a
```

```bash-ro
cd /home/Gitea && docker compose -p gitea -f docker-compose.yml config --quiet
```

```bash-ro
docker logs --since 30m --tail 100 gitea-server-1
```

```bash-ro
docker logs --since 30m --tail 100 gitea-db-1
```

```bash-ro
docker stats --no-stream gitea-server-1 gitea-db-1
```

`config --quiet` 只做語法驗證。**不要**把完整的 `docker compose config` 或未篩選的 `docker inspect` 輸出貼進工單，裡面可能有資料庫密碼；日誌也要先遮蔽 URL 認證資訊、權杖與個資。

## 設定變更的標準流程

1. 建立變更單，寫明目的、影響範圍、維護時間、備份與回復方式。
2. 保存原 Compose、`app.ini` 與實際映像 digest；機密放密碼庫或受限備份。
3. 一次只改一類設定；先在測試環境驗證。
4. 執行 `docker compose … config --quiet` 檢查 YAML；它不保證所有應用參數正確。
5. 用網站、`healthz`、Git 操作與權限驗收；記錄結果並更新本手冊。

!!! warning "新手注意：restart 不會重新讀入新的 Compose 設定"
    Compose 設定變動需要**重建容器**才會套用，單純 `restart` 不會。重建屬於中斷服務操作，只在核准的維護時段、有備份與回退方案時進行。
