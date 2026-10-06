# root 排程再檢視與優化報告

> 日期：2026-10-05（Asia/Taipei）｜主機：coffee@10.253.114.160｜備機：coffee@192.168.1.3
> 最新狀態（2026-10-05 18:33 Asia/Taipei）：使用者已安裝 coffee SSH 傳輸修正版；Linux 23 項測試全部通過，SSH 唯讀核對正式程式雜湊與權限一致，cron active、Gitea healthz pass。root crontab 時段未變；正式傳輸、歷史補傳與還原仍待驗收。以下早期稽核段落為修正前證據，部署完成結果見第 10 節。

## 1. 管理結論

網路已恢復到「鄰居可解析、TCP 22 回應 SSH banner」，但不能宣告異機備份恢復。2026-09-22～10-02 共 9 次平日工作，在 20:30 觸發後約 3 分 40 秒至 4 分 12 秒，均記錄 `/usr/bin/ssh exit=255`。今天 10/05 的 20:30 工作在本次約 17:54 的檢查時尚未到執行時間。

上次版本的保護機制仍在，但**我先前交付的程式缺少失敗補傳、異機保留與週備份外送功能**。網路恢復不會自動把歷史待傳備份補齊。這次應優先修復 root 使用的 SSH 認證及完成最新異機副本驗收，再處理歷史積壓、告警及還原完整性。

## 2. 已確認證據

| 項目 | 本次結果 | 可證明與限制 |
|---|---|---|
| cron 服務 | active | 排程引擎運作，不代表工作成功 |
| 平日工作 | 9 次 20:30 daily 觸發，9 次 SSH 錯誤 | 09/22、23、24、25、28、29、30、10/01、02；255 不足以區分認證、host key 或網路問題 |
| 週備份 | 09/26、10/03 09:00 有觸發 | 未讀到受保護日誌，不能判定成功 |
| 關機工作 | 每日 22:00 有觸發 | 近期每晚又迅速開機，不符合整夜關機的預期 |
| 正式程式 SHA-256 | `477a639f0b6154df6eee47bebf30c49dc099e33fc2c92daf3a4444dadffcdfc8` | 與上次交付一致，可用本機相同程式審查行為 |
| logrotate SHA-256 | `ea954f35ab6cb0f8790f24623874d4681debd7f69542eecd65d33c20b509c9fb` | 每日輪替、14 組、copytruncate |
| 磁碟 | 根分割區 468G、已用 107G、可用 338G、24%；inode 2% | 09/21 已用約 57G，增加約 50G；尚不能把增量全部歸因備份 |
| 備機網路 | eno1，來源 192.168.1.2；鄰居 REACHABLE；TCP 22 回應 OpenSSH 9.6p1 | 使用者後續測試確認 root 的 SSH 認證失敗；尚未執行到遠端目錄與容量檢查 |
| 應用 | Gitea／PostgreSQL 執行中，healthz pass | 現在服務正常，不代表備份可還原 |
| 其他容器 | MariaDB、myxampp 均已停止 | 本次未見會觸發 weekly「其他容器執行中」拒絕條件 |
| 時間 | Asia/Taipei，NTP active 但 synchronized=no | chrony reference 為 7F7F0101，所有外部來源 Reach=0，未取得外部校時 |
| 其他排程 | coffee 無個人 crontab；rsnapshot 範例全為註解 | 使用者後續提供完整 root crontab，僅有修正版三項工作 |

依程式流程，SSH 傳輸位於冷備份完成、服務恢復、gzip 檢查及本機發布之後，因此這 9 次很可能已留下本機成功備份；**這是程式順序推論，仍須以檔案清單和 SUCCESS／REMOTE_SUCCESS 驗證**。20:30 至錯誤的時間不是精確停機時間。

## 3. 問題、優先度與改善方案

| 優先度 | 問題與證據 | 改善方案與驗收 |
|---|---|---|
| P0 | 尚無已驗證異機副本；已有 9 次傳輸階段失敗，加上曾有 BIOS 找不到 SSD 的事件 | 先驗證 **root→coffee@備機** 的非互動 SSH；再傳送最新已驗證備份並核對遠端 SHA-256，最後隔離還原。不得以 coffee 手動 SSH 成功代替 |
| P1 | `daily` 僅傳送當次新備份；歷史失敗不補傳 | 新增獨立 `transfer-pending`，不停止服務；先傳最新副本確保時效，再處理最舊積壓。與現行工作共用鎖，限制每輪時間／數量 |
| P1 | 遠端 `.partial` 已存在會令 mkdir 失敗；遠端發布後若本機標記寫入失敗，重試也會被既有正式目錄阻擋 | 以 job ID＋manifest checksum 做可重複執行的傳輸；既有正式目錄內容相同則重新確認並補本機標記，不同則停止；partial 僅在受管理目錄內核對後續傳，不能盲刪 |
| P1 | 本機 daily 只清除已 REMOTE_SUCCESS 的舊備份；未傳及 partial 無上限，備機完全不清理 | 先盤點積壓容量。完成補傳後才納入本機保留；備機另訂保留政策、空間告警及受管理範圍。不得為騰空間先刪唯一副本 |
| P1 | weekly 不呼叫 transfer，系統備份只存同一顆 SSD | 將週備份也納入傳輸佇列與 checksum 驗收；本機損壞時才能取得系統設定副本 |
| P1 | weekly 備份 `/etc`、`/home`、Docker volumes，漏掉 `/usr/local/lib/gitea-maintenance`、root crontab 所在的 `/var/spool/cron` 與位於 `/var/backups` 的變更快照 | 增加受控的復原設定包：維運程式、`crontab -l` 匯出、logrotate、版本及安裝說明。不要直接覆蓋新主機的 cron spool；審核後用 crontab 工具安裝 |
| P1 | 22:00 關機後約十幾秒又開機 | 例如 10/04 22:00:05 系統到達 poweroff 流程，22:00:22 已有新 boot。查 BIOS RTC alarm、WOL、AC recovery、外部電源及韌體。不能把 Docker restart policy 當成能開啟實體主機的原因；也不能直接斷言是硬碟故障 |
| P1 | 時間未外部同步 | 網管確認可用可信 NTP 與 UDP 123；驗收須有外部選中來源及 Reach，不能只看 chrony active／Leap normal。校時避開備份，避免年齡與保留順序判斷受跳時影響 |
| P1 | 冷備份打包前只確認容器停止一次；兩容器 restart=always | Docker daemon 若在打包期間重啟可能重新啟動容器。維護期間排除 daemon 更新／重啟，增加事件或狀態監控；偵測意外啟動則整份備份判定無效。不只在結尾檢查狀態，也不直接改 restart policy 造成開機服務不恢復 |
| P2 | 日誌只保留泛用 ssh exit=255，沒有通知 | 記錄工作 ID、階段、受控錯誤分類、各階段耗時、最後本機／異機成功時間；root 私有日誌保留經遮蔽的必要 stderr。另建立指定值班人接收的告警，不能僅寫 logger 當通知已送達 |
| P2 | `/home/Gitea/docker-compose.yml` coffee 持有且 group/other 可寫；data 777、access-rules.sh 777 | root 工作依賴的 Compose 與控制腳本應由管理者控制，資料目錄則按容器數字 UID/GID 設定。父目錄遍歷權限影響實際可存取範圍，不能僅憑檔案 mode 宣稱任何使用者皆可利用；不可整棵 chmod/chown 破壞 DB 權限 |
| P2 | 停機期間直接 gzip 壓縮，時間隨資料量增長 | 先量測真實停機時間；若超出目標，再改為停機時製作一致性本機副本、恢復服務後壓縮，須重新估算暫存空間。更短 RPO／RTO 再另設計快照或資料庫原生備份 |

### 既有設計應保留

- 共用互斥鎖、復原標記、正常停機檢查、恢復服務後 healthz、嚴格 SSH host key、遠端 SHA-256、partial 發布機制。
- 尚未修好的 root 認證不應阻止仍可完成的本機冷備份；新增 preflight 應記錄降級狀態，不能讓備機離線造成兩邊都沒新備份。
- `SUCCESS` 只代表本機檔案驗證；`REMOTE_SUCCESS` 代表工具記錄的遠端驗證，不等於隔離還原成功。

### 補充：傳輸頻寬與喚醒證據

`eno1` 目前協商為 **100 Mb/s、全雙工**，備機路由也走此介面。理論最高 12.5 MB/s，實際還有 SSH、協定、CPU 與磁碟開銷；90 分鐘理論最多約 67.5 GB（十進位），不能當作保證傳輸量。應量測單份封存大小及實際吞吐量，再決定重試配額；若原設計預期 1 Gb/s，核對交換器埠與線材，不直接強制速率。

本次 `/sys/class/rtc/rtc0/wakealarm` 無輸出；ACPI 顯示部分網卡／USB 喚醒路徑 enabled。這不證明 S5 關機後的實際喚醒來源，也不能排除 BIOS 自有排程。一般帳號的 ethtool 部分資訊權限不足，未取得完整 Wake-on 設定，不能斷言 WOL 已開或已關。

使用者第一次補貼的 sudo 檢查因四個指令黏成一行、未加分號，crontab 解析失敗；沒有取得 root 資料，也沒有修改排程。已提供含分號的單行唯讀檢查，等待結果。

## 4. 排程建議

現行主時段先維持：週一至週五 20:30 daily、週六 09:00 weekly、每日 22:00 受保護關機。**此處不是新的可直接安裝 crontab。**

建議先完成傳輸補償功能，再加入不造成停機的傳輸重試，初始建議每日 10:00、18:00，每輪最多 45 分鐘。工作占鎖便跳過並可辨識記錄；已錯過的停機備份不得於上班時間自行補停。重試時段、容量預算及備機保留天數須依實測完成部署設定。

22:00 的互斥只防止同工具工作重疊，不能阻止外部關機／重啟。備份或傳輸超時占鎖會跳過當日關機，不會補關；應列為告警事件。未取得遠端副本不會自動阻止所有關機，若要改成「無異機副本不關機」，需 PM 明確訂出最大延後時間與人工處置，避免無限等待。

週末仍無新的 daily 冷備份，weekly 重用既有冷備份，因此不能承諾全年任意時點 RPO 24 小時。RTO 尚未由還原實測取得，不能把備機可連線稱為即時備援。

## 5. 待補的唯讀驗證

本次 SSH 的 `sudo -n` 回覆需要密碼，沒有讀到以下 root 資訊；沒有透過 Docker 繞過權限。請由管理員在主機執行，不把密碼貼入聊天。

```bash
sudo crontab -l
sudo tail -n 60 /var/log/gitea-maintenance/daily.log
sudo tail -n 40 /var/log/gitea-maintenance/weekly.log
sudo tail -n 40 /var/log/gitea-maintenance/shutdown.log
sudo find /var/backups/gitea-maintenance -maxdepth 3 -type f \( -name SUCCESS -o -name REMOTE_SUCCESS -o -name manifest.json \) -printf '%TY-%Tm-%Td %TH:%TM %p\n'
sudo du -sh /var/backups/gitea-maintenance/daily /var/backups/gitea-maintenance/weekly
sudo ls -la /var/lib/gitea-maintenance
sudo ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 coffee@192.168.1.3 'hostname; id; df -h /home/coffee; ls -ld /home/coffee/gitea-backups'
```

SSH 失敗時保留原始錯誤：Host key verification failed、Permission denied、timeout 等應分別處理。不關閉 host key 驗證，不共用或傳出 root 私鑰。如果 SSH 成功但備份目錄不存在，不等於認證失敗；傳輸程式會另行建立受管理目錄。上述檢查不測試實際寫入／傳輸，正式驗收仍需維護程序。

日誌每天輪替，當日日誌可能尚空；必要時再讀最近輪替檔，不以空檔判定工作從未執行。

## 6. PM 分工及驗收

| 項目 | 負責角色 | 驗收條件 |
|---|---|---|
| 異機認證與最新副本 | Linux／備機管理員 | root 非互動 SSH 成功、遠端校驗一致、目錄權限符合設計 |
| 傳輸補償與保留 | 維運程式維護者 | 不停 Gitea 即可補傳；斷線可重試；已發布同一工作不重覆覆蓋；保留不刪唯一副本 |
| 週備份完整性 | Linux 管理員 | 週備份遠端可得，還原包包含實際使用的排程與程式 |
| 關機後重新開機 | 硬體／網管 | 在有人值守時驗證正常關機維持斷電狀態；確認預期自動開機時間；不以遠端盲測冒險 |
| NTP | 網管／Linux 管理員 | 使用可信外部／內部標準源，時間偏差可量測、跨機紀錄可比對 |
| 災難還原 | Gitea 管理員／PM | 隔離環境還原 DB、Git、LFS、附件、Issue／PR、權限；記錄資料截止點及耗時，訂出 RPO／RTO |
| 通知 | PM／值班人 | 測試失敗事件能送達指定人並有人確認；不可只有本機 log |

回歸測試至少涵蓋：備機離線但本機備份保留、root 認證失敗、傳輸中斷與 partial 重試、遠端 checksum 不符、遠端完成但本機未寫標記、兩工作搶鎖、磁碟不足、服務恢復失敗、打包中 Docker 重啟、時間跳動、週備份傳輸及復原設定包。

## 7. 稽核範圍與參考

本次未觸發服務停止、備份、傳輸、刪除、套件安裝、重開機或排程更新。審查來源為正式程式與交付版雜湊一致、cron journal、系統 journal、狀態／權限查詢與定點 TCP 22 banner。SSH 指令及結果均保存在本機 work/gitea-audit.jsonl，個別結果為 cron_reaudit*_20261005-result.txt。

- [chrony：7F7F0101 表示 local mode，並未同步外部來源](https://chrony-project.org/doc/3.3/chronyc.html)
- [Docker：手動停止與 daemon 重啟時的 restart policy 行為](https://docs.docker.com/engine/containers/start-containers-automatically/)

此報告提供已驗證現況與可實施改善方案；**不是已部署新版程式的完成證明**。待 root 輸出與首次成功異機／還原驗收補齊後，再更新狀態。


## 8. 使用者補證：root SSH 認證失敗（2026-10-05）

使用者提供完整 `sudo crontab -l`，確認仍為每日 22:00 shutdown、週六 09:00 weekly、平日 20:30 daily，且使用正式維運程式。沒有看到原始 scp 排程重新啟用。

同次執行的非互動 SSH 回覆：

```text
coffee@192.168.1.3: Permission denied (publickey,password).
```

這證明本次連線已進到 SSH 使用者認證，現階段不是無路由或 TCP 22 不通。嚴格 host key 檢查亦未阻止本次進入認證。備機的 hostname/id/df/ls 指令未獲執行，所以備機路徑與空間仍未知。

root crontab 的 SSH 是以主機 root 的客戶端設定與金鑰登入備機 coffee，而非登入備機 root，也不是使用 coffee 個人手動登入時的金鑰。BatchMode 不會詢問登入密碼；看到 `(publickey,password)` 不表示已有可供排程使用的密碼認證。可能原因包括沒有適合金鑰、金鑰未被選用／未獲授權、加密金鑰無可用 agent、備機 authorized_keys 權限或 SSH 政策，尚未確認其中哪一項。

處理順序：先讀取 root SSH 有效設定、金鑰檔案名稱及必要的 SSH 認證診斷；只交換公鑰與指紋，不輸出或複製私鑰。若需新金鑰，採主機至備機專用身分，由備機管理員授權到 coffee，使用明確 IdentityFile、IdentitiesOnly 與已核對 host key。不得把本工作區的 Codex 金鑰挪作正式備份身分。後續私鑰路徑必須同時套用 ssh 與 scp，避免只修好前置測試。

修復驗收：從主機 root 執行同一組 BatchMode＋StrictHostKeyChecking 設定可登入；確認遠端目錄 owner/mode 與空間；補傳最新成功本機副本；核對遠端 checksum；再做隔離還原。

同次貼文沒有 daily.log 與 weekly.log 的內容，也沒有顯示讀檔錯誤，不能因此宣稱備份不存在或成功。日誌每日 copytruncate 輪替，本次是在今日 20:30 之前，需查 `.log.1` 或其他輪替檔。9 次歷史 255 仍不能全部追溯認定為相同認證根因。


## 9. 第二次補證：缺少 root 金鑰及週備份成功

### 已確認

- `/root/.ssh` 只有空的 authorized_keys、known_hosts 與 known_hosts.old，沒有 SSH 有效設定列出的 id_rsa、id_ed25519 等預設私鑰。`identitiesonly no`，未看到明確 identityagent 設定。結合 BatchMode 認證失敗，可確認預設檔案型金鑰認證尚未配置；沒有證據證明存在可供 cron 使用的其他有效 agent 身分。
- 空的 `/root/.ssh/authorized_keys` 只影響別人登入本機 root，與本機向備機發起連線無關，無須為本問題修改它。
- 10/02 daily：20:30:02 開始，20:33:01 服務恢復且 healthz 通過，20:33:49 在 SSH 階段失敗。開始至服務恢復約 179 秒，包含前置檢查，不是精確停機時間。結合已核對程式流程，可判定本次已走完本機發布流程，仍需核對封存檔與 checksum。
- 10/03 weekly：09:00:01 開始，09:04:54 SUCCESS，約 292 秒。確認程式回報週備份成功；不等於已傳備機或做過還原。
- 當前 daily.log 與 weekly.log 為零位元組，是可與週期執行及 logrotate 相符的現象；輪替檔有上述內容，不應再認定為沒有日誌。

### 修正決策：沿用 coffee 的既有 SSH 身分

使用者明確指定使用 coffee 既有金鑰，先前建立 root 金鑰的建議已撤回，不應執行。已確認一般 coffee SSH 成功，且以清除 agent 等環境的非互動方式重測成功。root 缺少金鑰是舊程式失敗的原因，修法改為調整傳輸身分，而不是新增 root 金鑰。

完整修正版與操作說明見 [coffee SSH 修正套件](gitea-coffee-ssh-fix-20261005/README.md)。root 維持管理備份及服務；只讓 SSH 以 coffee 執行，root 開啟受保護檔案後經 stdin 傳入，避免 coffee 無法讀取 root 700 目錄。三項排程時段與目錄權限不變。

2026-10-05 唯讀重測顯示備機剩餘約 202 GiB，備份管理目錄尚未存在。23 項本機測試中 22 通過、1 項 Linux 鎖測試略過；正式 runuser 傳輸、checksum 與還原仍待安裝後驗收。此段為套件交付時狀態；使用者後續已安裝，見第 10 節。

### 仍未解決

歷史失敗不會自動補傳；weekly 尚未異機傳送；遠端保留與還原演練待建立；22:00 關機後又開機及外部校時問題仍在。這次修復方案只解決 SSH 身分，不代表其他改善已部署。


## 10. coffee SSH 修正版部署驗證（2026-10-05 18:33）

使用者將 ZIP 解壓後實際套件位於 `/home/coffee/gitea-coffee-ssh-fix-20261005/gitea-coffee-ssh-fix-20261005`。初次從外層執行因找不到 SHA256SUMS 停止，尚未進行安裝；切至內層後套件 checksum 全部通過，Linux 上 23 項單元／回歸測試全部通過，包含 POSIX 互斥測試。

測試輸出的 `Remote checksum verified ...20261005T100000Z-123` 是 mock 測試訊息，不是實際備機傳輸紀錄。不能用此行作為異機副本驗收。

使用者執行 `sudo python3 ./install_update.py` 後回報 Installed coffee SSH transport。更新器在正式更新前以 root→runuser coffee→SSH 完成唯讀前置檢查，備存舊程式、取得維運鎖並原子替換程式，未改 crontab，也未觸發備份、傳輸、停止服務或關機。

| 驗證項目 | 結果 |
|---|---|
| 新程式 SHA-256 | `83513d0e3420b856b794fd6ace8a5bdaa0c75116c7b90849ec64f1be91deef0b`，與本機套件及安裝輸出一致 |
| 正式程式權限 | root:root，644 |
| 備份及狀態目錄 | root:root，700，未放寬 |
| cron | active |
| Gitea／PostgreSQL | 都在執行，Up 21 hours；healthz pass |
| 回復程式 | `/var/backups/gitea-cron-changes/20261005T103208Z-coffee-ssh-857242/gitea_maintenance.py.before` |
| 正式異機傳輸 | 尚未執行／驗收 |

以主機目前時間及既有排程，下一次 daily 預定為 2026-10-05（週一）20:30 Asia/Taipei。主機仍須保持開機、備機可達、服務健康且無復原標記或互斥衝突；不是保證一定成功。完成後讀取 daily.log，驗收服務恢復、遠端 checksum 及 SUCCESS daily，再確認備機正式目錄。跨午夜應讀輪替檔。

本次已修正生產程式的 SSH 執行身分，但不代表歷史未傳備份、週備份外送、遠端保留、NTP、22:00 再開機或還原演練已處理。暫不重裝套件，也不在上班時間手動執行 daily。
