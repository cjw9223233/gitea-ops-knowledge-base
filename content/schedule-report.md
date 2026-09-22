# root 排程檢視、修正與優化報告

> 主機：`coffee@10.253.114.160`  
> 盤點日期：2026-09-21；更新：2026-09-22；版本：1.2  
> **狀態：正式 root 排程已安裝，程式與設定雜湊核對一致，cron 及 Gitea 健康檢查正常。15 項 Linux 測試通過；首次正式備份、備機傳輸與還原仍待驗收。**

## 1. 結論

原排程包含每日 22:00 關機、週六 09:00 備份，以及平日 20:30 同步 Gitea 至 `192.168.1.3`。已完成逐行檢查、修正套件、回復程序及測試；使用者已同意平日 20:30 可短暫停止 Gitea／PostgreSQL，以製作一致性備份。

最明確的錯誤是原同步指令含未跳脫的 `%`，會被 cron 截斷。其他問題包括資料庫熱複製、管線掩蓋錯誤、失敗後仍刪舊備份，以及 22:00 關機可能中斷尚未結束的備份。

修正後保留原時段，但不再直接覆寫備機的 `/home/Gitea`。改成先建立一致性封存檔、恢復服務，再傳到備機獨立備份目錄並驗證 checksum。

**2026-09-22 首次安裝在備機檢查階段停止。使用者隨後確認備機尚未開機，指示先假設其正常；因此新增 `--defer-standby-check`，允許先完成本機安裝。這是部署前提假設，不是備機已驗證。使用者已執行修訂版並回報 Installed；安裝器完成排程安裝與讀回比對。**

## 2. 本次實際完成與未完成

| 項目 | 狀態 |
|---|---|
| 取得原 root 排程 | 完成；來源為使用者提供的 `sudo crontab -l` 輸出 |
| 讀取既有備份腳本與相關狀態 | 完成 |
| 修正排程及必要程式 | 完成 |
| Linux 測試 | 15／15 通過；模擬服務操作，不停止正式容器 |
| 套件上傳與 SHA-256 驗證 | 完成 |
| 使用者執行安裝器 | 已成功執行修訂版，明確延後備機前置檢查 |
| 正式排程安裝 | **完成；安裝器回報 Installed，已完成讀回比對** |
| 正式備份／傳輸／還原演練 | **未執行** |

已由使用者透過 sudo 安裝正式程式、root 排程、日誌輪替與受限資料目錄，並備存原排程。沒有以 Docker 繞過 sudo，也沒有在安裝與驗證時修改網路、停止服務或執行關機。

## 3. 原排程審查

### 3.1 每日 22:00 關機

```cron
00 22 * * * sudo /sbin/shutdown -h now >> /var/log/shutdowm_at.log 2>&1
```

時間有效，`00` 與 `0` 相同。但 root crontab 不需要 sudo；日誌名稱 `shutdowm` 拼字不一致；沒有保護正在執行的備份或傳輸。平日 20:30 工作若超過 90 分鐘，會與關機衝突。

**修正：**保留 22:00；與備份共用互斥鎖，存在進行中的工作或待復原標記時跳過關機並記錄。跳過後不自動補關機，由值班人處理。

### 3.2 週六 09:00 備份

```cron
0 9 * * 6 sudo /home/coffee/scripts/B_generate_backups.sh >> /home/coffee/scripts/B_generate_backups.log 2>&1
```

這是每週六，不是原腳本註解的「每日」。原腳本依序打包 `/etc`、`/home`、`/var/lib/docker/volumes`，最後只保留兩個日期資料夾。

| 缺陷 | 影響 |
|---|---|
| 未逐步檢查 tar 退出碼 | 備份失敗仍可能印出完成 |
| 未以新備份成功作為清理前提 | 可能刪除仍有價值的舊備份 |
| 註解寫兩天，實際保留兩組 | 保留政策容易誤解 |
| 同一天重跑共用檔名 | 可能覆寫同日先前備份 |
| `/home` 含運作中的 PostgreSQL 實體目錄 | 沒有一致性保證 |
| 缺乏互斥、校驗與輪替 | 工作重疊、損毀與日誌成長較難控制 |

**修正：**保留週六 09:00，不增加週六停機。使用最近 72 小時內成功的 Gitea 冷備份，再備份系統檔案；系統 tar 排除 live `/home/Gitea` 與 coffee 的 `.cache`。Gitea 資料截止點是該冷備份時間，不宣稱為週六 09:00。

若沒有合格冷備份，或有其他未納入設計的容器執行中，工作失敗退出，不回退為不一致的熱複製。系統檔案仍是 live 檔案備份，並非整機映像或所有服務的一致性快照；tar 非零退出時不標記成功。

### 3.3 平日 20:30 同步

原排程將 scp 輸出送入 awk，其時間格式為：

```text
strftime("[%Y-%m-%d %H:%M:%S] ")
```

cron 會在 shell 解析之前處理未跳脫的 `%`：第一個 `%` 截斷命令，後方內容送到標準輸入。雙引號不能阻止這個行為。[cron 手冊](https://manpages.debian.org/bookworm/cron/crontab.5.en.html)

本次查到原指定日誌 `/home/coffee/coffee_log/gitea_backup_config_data_postgres.log` 不存在，與解析錯誤相符；未取得完整歷史 cron 日誌，故不宣稱已確認每次觸發結果。

另有以下問題：

- 沒有 pipefail 的管線通常回傳最後一個命令狀態，awk 成功不代表 scp 成功。
- root 排程使用 root 的 SSH 金鑰與 known_hosts，不能以 coffee 手動能連線代替驗證。
- 沒有明確的 BatchMode、連線存活及傳輸逾時控制。
- 直接複製運作中的 Git、設定、PostgreSQL 目錄，不能保證同一時間點。
- scp 不是完整刪除同步機制；直接覆寫備機資料目錄也可能影響正在運作的服務。

普通 PostgreSQL 檔案備份需要停止 DB，或使用具一致性保證的專用機制；不能把普通熱複製當作合格備份。[PostgreSQL 14 備份要求](https://www.postgresql.org/docs/14/backup-file.html)

**修正：**保留平日 20:30，停止 Gitea → 停止 DB → 確認正常退出 → 冷備份 → 恢復 DB → 恢復 Gitea → healthz → 壓縮驗證／checksum → 傳送備機。服務不必為整段傳輸時間持續停止。

原本被 `#` 註解的另一條 scp 命令不會執行，修正版沒有重新啟用它。

## 4. 修正後 root crontab

這是 root 的**使用者 crontab**，時間後不額外加入 `root` 欄位。主機時區仍為 Asia/Taipei。

```cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 每日 22:00：工作進行中或待復原時跳過關機
0 22 * * * /usr/bin/python3 /usr/local/lib/gitea-maintenance/gitea_maintenance.py shutdown >> /var/log/gitea-maintenance/shutdown.log 2>&1

# 週六 09:00：系統檔案＋最近成功的 Gitea 冷備份
0 9 * * 6 /usr/bin/python3 /usr/local/lib/gitea-maintenance/gitea_maintenance.py weekly >> /var/log/gitea-maintenance/weekly.log 2>&1

# 週一至週五 20:30：冷備份、恢復服務、傳送備機
30 20 * * 1-5 /usr/bin/python3 /usr/local/lib/gitea-maintenance/gitea_maintenance.py daily >> /var/log/gitea-maintenance/daily.log 2>&1
```

不再把日期格式或 awk 管線放在 crontab，避免 `%` 及巢狀引號問題。沒有假設此 cron 版本支援 `CRON_TZ`，也沒有把未知郵件傳送能力寫成已建置告警。

## 5. 修正套件與保護措施

主機保留的安裝套件位置：`/home/coffee/gitea-cron-fix-20260921`；正式程式已安裝到 `/usr/local/lib/gitea-maintenance`。

| 檔案 | 用途 |
|---|---|
| `root.crontab` | 新排程 |
| `gitea_maintenance.py` | 備份、復原、傳輸、清理及關機保護 |
| `install.sh` | 前置檢查、備存原排程、安裝及讀回比對 |
| `original-active.crontab` | 使用者提供的原三行，用於防止覆蓋後續變更 |
| `logrotate.conf` | 日誌每日輪替、保留 14 組 |
| `test_cron_fix.py` | 邏輯與安全測試 |
| `README.md`、`SHA256SUMS` | 操作說明及套件完整性核對 |

主要保護如下：

| 機制 | 行為 |
|---|---|
| 互斥 | daily／weekly／shutdown 共用 flock；第二個工作退出並記錄 |
| 權限 | 正式工作須 Linux root；資料目錄須 root 持有、700 |
| 空間 | 本機備份前及異機傳輸前檢查空間，不先刪舊備份騰空間 |
| 原服務狀態 | 兩個容器原先必須都在執行，否則不擅自啟動後備份 |
| 冷備份一致性 | 正常停止 Gitea 與 DB 後才打包；異常退出不發布成功 |
| 復原 | 打包失敗仍嘗試恢復；healthz 通過才移除待復原標記 |
| 發布 | `.partial` 完成校驗後才轉為正式備份目錄 |
| 傳輸 | BatchMode、嚴格 host key、keepalive、逾時及遠端 checksum |
| 清理 | 僅處理新工具管理的成功目錄；不碰舊 `/var/backups/coffee` |
| 關機 | 工作占鎖或待復原標記存在即跳過，不強制打斷備份 |

程式有逾時控制，但斷電、SIGKILL、OS 崩潰與磁碟故障無法保證自動復原；需要依殘留標記人工處理。冷備份打包上限 60 分鐘是防止無限等待的上限，**不是預期停機時間**，實際長度需首次維護量測。

## 6. 資料位置、保留及備援意義

| 位置 | 用途 |
|---|---|
| `/var/backups/gitea-maintenance/daily` | 新 Gitea 冷備份 |
| `/var/backups/gitea-maintenance/weekly` | 系統檔案＋最近一次合格冷備份 |
| `/var/lib/gitea-maintenance/recovery-required.json` | 服務需人工確認復原的標記 |
| `/var/log/gitea-maintenance` | daily／weekly／shutdown 日誌 |
| `/var/backups/gitea-cron-changes/執行編號` | 原排程、舊腳本、新排程與驗證紀錄 |
| 備機 `/home/coffee/gitea-backups` | 經校驗的封存備份，不是運作中資料目錄 |

本機保留最近 7 組已完成異機校驗的平日備份、最近 2 組成功週備份。失敗 `.partial` 與尚未完成異機傳送的本機備份不自動刪除，值班人須追蹤容量。原備份與舊腳本保留不刪。

備機目錄須由 coffee 持有且權限 700；先傳到 `.partial`，遠端 SHA-256 通過後才發布。沒有自動刪除備機舊資料，保留政策由備機管理員另行建立。

**不再直接覆寫備機 `/home/Gitea`，也不代表備機已還原或能即時接手。**若其他流程依賴舊的 live 目錄覆寫，需重新設計切換／還原程序。備份透過 SSH 加密傳輸，但套件未另做檔案靜態加密，應由儲存及機密政策補足。

## 7. 測試結果

在 coffee 主機以一般帳號執行，正式服務命令皆以模擬取代；只有暫存檔與 POSIX 鎖實際運作。**15 項全數通過**：

1. 排程時段保持、沒有 `%` 或多餘 sudo。
2. 待復原標記阻止新備份。
3. 遠端 checksum 失敗不標記成功。
4. healthz 必須為 JSON `status=pass`。
5. 不擅自啟動原本停止的容器。
6. 本機空間不足中止。
7. 真正的 Linux POSIX 鎖阻止第二個工作。
8. 備機空間不足保留本機備份。
9. 恢復失敗保留待復原標記。
10. 清理範圍限合格、受管理的新備份。
11. 待復原標記阻止關機。
12. 成功流程恢復服務後才發布備份。
13. tar 失敗仍嘗試恢復，不發布成功。
14. DB 非正常退出拒絕備份。
15. 週備份缺少合格冷備份來源時中止。

另通過 `bash -n` 安裝腳本語法檢查，以及上傳後套件 SHA-256 核對。未測試正式停機長度、真實備份傳輸及還原，不將模擬測試等同正式驗收。

## 8. 安裝失敗的實際診斷

使用者執行安裝器，所有檔案 checksum 通過，接著回覆：

```text
ssh: connect to host 192.168.1.3 port 22: No route to host
```

本次隨後從 `.160` 再做定點檢查：

```text
ip route get 192.168.1.3
192.168.1.3 dev eno1 src 192.168.1.2

ip neigh show 192.168.1.3
192.168.1.3 dev eno1 FAILED

TCP 22 connect
[Errno 113] No route to host
```

已確認 `eno1` UP、同時持有 `10.253.114.160/24` 與 `192.168.1.2/24`，`enp5s0` DOWN。

**判讀：有到該網段的路由，但未能解析到備機鄰居。**問題尚未進到 SSH 金鑰認證階段，不能據此要求重設密碼或重裝 authorized_keys。可能原因包括備機未開機、IP 已變更、實體接線／VLAN 不一致，或網路設備的阻擋；尚無證據指定唯一根因。

由網管或備機管理員確認：

1. 備機已開機，且實際 IP／mask 仍是 `192.168.1.3/24`。
2. 備機與 `.160` 的 `eno1` 所在二層網路可互通；若接在另一張網卡或隔離 VLAN，先核對設計。
3. 備機 SSH 服務正常；先恢復網路可達，再查認證。
4. 若備機位址已變更，先提供正確位址以更新並重測套件，不直接用陌生主機替代。

第一次安裝中止時尚未安裝正式程式或排程；當時確認 `/usr/local/lib/gitea-maintenance`、`/var/backups/gitea-cron-changes`、`/etc/logrotate.d/gitea-maintenance` 都不存在，與前置檢查中止一致。

## 9. 已完成的本機套用程序

使用者已成功執行以下命令，將備機連線與認證列為待驗證。以下保留作為部署紀錄，**目前不需重複安裝**：

```bash
sudo bash /home/coffee/gitea-cron-fix-20260921/install.sh --defer-standby-check
```

安裝器會比對目前 root 有效排程是否仍與提供的三行相同。若有其他人新增或修改工作，會停止，不覆蓋未知變更。

此旗標只略過安裝前的備機連線測試，並把 `standby_preflight_deferred=1` 記錄在安裝紀錄中；正式排程仍使用 root 的 SSH 身分、嚴格 host key、遠端空間及 checksum 檢查。未帶旗標時仍維持原先嚴格前置檢查。備機開機後若認證失敗，再由管理員核對 root 的既有金鑰與已信任指紋，不關閉 host key 檢查，也不提供密碼到聊天。

成功後會備存原完整 crontab 及舊腳本，安裝 root 持有的程式、日誌輪替及新排程，再讀回比對。安裝不會立即執行備份、停服務或關機。

```bash
sudo crontab -l
sudo stat -c '%A %U:%G %n' /usr/local/lib/gitea-maintenance/gitea_maintenance.py
```

保存安裝器顯示的回復快照路徑。若檔案安裝階段發生錯誤，保留完整輸出供檢查，不能反覆略過檢查或直接宣稱成功。

## 10. 第一次執行驗收與回復

```bash
sudo tail -n 100 /var/log/gitea-maintenance/daily.log
sudo tail -n 100 /var/log/gitea-maintenance/weekly.log
sudo tail -n 100 /var/log/gitea-maintenance/shutdown.log
sudo journalctl -t gitea-maintenance --since today --no-pager
docker ps -a
curl --max-time 10 -fsS http://127.0.0.1:3000/api/healthz
```

日誌每日輪替、保留 14 組；copytruncate 在輪替瞬間可能有極少量訊息遺失，重要失敗另外寫入系統日誌。尚未建立 email／Slack 等通知，需指定人主動檢查。

若服務恢復失敗，待復原標記會保留，阻止新備份與排程關機。先確認 DB → Gitea 恢復及 healthz pass，保存事件紀錄後才人工移除標記，不能只刪標記掩蓋故障。

回復原排程需使用安裝器輸出的實際路徑：

```bash
sudo crontab /var/backups/gitea-cron-changes/20260922T011918Z-245434/root.crontab.before
sudo crontab -l
```

回復排程不會中止已執行的工作，也不會自動恢復容器。原排程仍含已知缺陷，僅作緊急回復方案。

## 11. PM 驗收與後續工作

| 項目 | 負責人角色 | 完成條件 |
|---|---|---|
| 備機連線 | 網管／備機管理員 | 鄰居可解析、TCP 22 可達、root SSH 前置檢查通過 |
| 套用排程 | Linux 管理員 | 安裝成功、讀回一致、回復快照可用 |
| 首次正式備份 | Linux 管理員 | 服務正常恢復、停機時間可量測、校驗成功 |
| 異機副本 | 備機管理員 | 遠端 checksum 成功、容量與存取受控 |
| 還原演練 | Linux／Gitea 管理員 | 隔離環境驗證登入、Git、LFS、Issue／PR 與權限 |
| 時間同步 | 網管／Linux 管理員 | 有可信 NTP，跨機日誌時間可對照 |
| 告警與保留 | PM／維運 | 明確接收人、回應時限、備機保留與加密政策 |

平日冷備份只在週一至週五觸發，不能承諾任何時點 RPO 都是 24 小時。週末、主機關機、失敗或錯過排程時資料落差可能更長；普通 cron 不會自動補跑關機期間錯過的工作。更嚴格的 RPO 需另行核准頻率及架構。

本次沒有更改 NTP、網路、防火牆或備機運作中的 Gitea。本機安裝已完成；下一個必要步驟是首次正式備份驗收，並在備機開機後補做 root SSH、正式傳輸及隔離還原驗收。在那之前，不代表異機備援已成功。

### 修訂紀錄

- 1.0：完整審查、15 項測試、首次安裝因備機無法連線中止。
- 1.1：使用者確認備機關機並指示先假設正常；新增安裝旗標以延後備機前置檢查，不放寬正式備份的驗證。

## 12. 部署完成驗證（2026-09-22）

使用者提供的安裝輸出顯示 `Installed`。安裝器會在 `crontab` 安裝後讀回並以 `cmp` 比對，成功後才輸出此訊息。本次工具無 sudo 密碼，root crontab 的安裝證據來自這份執行結果；其餘可讀部署檔與服務狀態另以 SSH 核對。

| 驗證項目 | 結果 |
|---|---|
| 原排程回復快照 | `/var/backups/gitea-cron-changes/20260922T011918Z-245434/root.crontab.before` |
| 正式程式 | root:root，644；父目錄 root:root，755 |
| logrotate 設定 | root:root，644；每日輪替、14 組 |
| 備份、狀態及日誌目錄 | root:root，700 |
| 程式與 logrotate SHA-256 | 與交付版本一致 |
| cron | active、enabled |
| Gitea／DB 容器 | 都在執行；驗證時 Up 6 hours |
| healthz | status=pass，cache 與 database 檢查通過 |
| 備機檢查 | 依使用者指示延後，尚未驗證 |
| 正式備份及還原 | 尚未觸發／演練 |

以上證明部署完成且現有服務正常，不能取代首次排程執行、傳輸及還原驗收。安裝時未觸發停機、備份或關機。

部署檔案 SHA-256：

```text
gitea_maintenance.py  477a639f0b6154df6eee47bebf30c49dc099e33fc2c92daf3a4444dadffcdfc8
logrotate.conf  ea954f35ab6cb0f8790f24623874d4681debd7f69542eecd65d33c20b509c9fb
```

- 1.2：使用者成功完成 sudo 安裝；已核對正式檔案權限、雜湊、cron 與應用健康狀態，保留備機及完整還原待驗收項目。
