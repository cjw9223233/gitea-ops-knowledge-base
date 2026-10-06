每個症狀固定四步：**症狀**（你看到什麼）→ **先看**（唯讀檢查）→ **判讀**（輸出代表什麼）→ **升級**（找誰、何時）。除非特別標示，指令都是唯讀。

!!! warning "共通原則"
    先蒐集證據再動手；不要刪鎖檔、`.partial`、`recovery-required.json`；不要在上班時段重開機或手動跑備份。需要變更時，回到 [權限與交接](access.html) 的變更流程，先備份、再改、再驗收。

## R1 Gitea 網站打不開

**症狀**：瀏覽器連不到、很慢，或回應 502／逾時。

**先看**（在正式主機執行）：

```bash-ro
curl --max-time 10 -fsS http://127.0.0.1:3000/api/healthz
```

```bash-ro
docker ps -a --format '{{.Names}} {{.Status}}'
```

**判讀**：

- 發生在主機時間 **20:30–20:35** 或 **22:00–22:02**：屬於正常的備份停機與每晚重開機，幾分鐘後恢復。
- `healthz` 通過但使用者連不上：多半是網路或白名單，改看 [R2](#r2-git-pushclone-失敗)。
- `healthz` 失敗且容器是 `Exited`：看 `docker logs --since 30m --tail 100 gitea-server-1`，並確認是否有 `recovery-required.json`（備份中途失敗會留下）。

**升級**：容器停止且無法自行啟動、或有復原標記，立即找 Linux 管理員；不要自行 `docker compose down`。

## R2 Git push／clone 失敗

**症狀**：`git clone`、`push` 逾時、被拒絕，或要求登入。

**先看**（在使用者電腦，Windows PowerShell）：

```powershell-ro
Test-NetConnection 10.253.114.160 -Port 3000
```

```powershell-ro
Test-NetConnection 10.253.114.160 -Port 2222
```

**判讀**：

- `TcpTestSucceeded: False`：來源 IP 不在白名單、或中間網路擋住，找網管，並提供**使用者實際來源 IP**（經 NAT 時以抵達主機的位址為準）。
- 埠通但被拒絕：帳號、權限或個人金鑰問題，找 Gitea 管理員；確認公鑰已加入個人帳號，且使用 `2222` 而不是主機的 `22`。

**升級**：多人同時失敗，先看 [R1](#r1-gitea-網站打不開)。

## R3 Git SSH（2222）不通但網站可開

**症狀**：網頁正常，`git clone ssh://…:2222` 失敗。

**先看**（在正式主機）：

```bash-ro
ss -lnt | grep -E ':(22|2222)\b'
```

**判讀**：2222 未監聽代表 Gitea 容器的 SSH 沒啟動，看 `docker logs gitea-server-1`；已監聽則是白名單或使用者金鑰問題，流程同 R2。注意 **22** 是 Linux 維運 SSH，**2222** 才是 Git。

**升級**：Linux 管理員（容器）或網管（白名單）。

## R4 備份失敗：`ssh exit=255`

**症狀**：`daily.log` 出現 `FAILED: Command failed: /usr/bin/ssh exit=255`。

**先看**：

```bash-ro
sudo tail -n 40 /var/log/gitea-maintenance/daily.log.1
```

要模擬排程的環境（清空環境變數，沒有 ssh-agent）：

```bash-ro
sudo runuser -u coffee -- /usr/bin/env -i HOME=/home/coffee USER=coffee LOGNAME=coffee PATH=/usr/bin:/bin /usr/bin/ssh -v -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 coffee@192.168.1.3 'hostname; date'
```

**判讀**：`255` 是 SSH 連線或認證層失敗。逐一確認備機是否開機、路由與 TCP 22、`known_hosts`、備機 `authorized_keys`。你在互動終端機手動 `ssh` 成功**不代表排程會成功**，因為排程沒有 ssh-agent。

**升級**：Linux 管理員；備機本身電源或網路找備機管理員。外送失敗期間，本機備份不會被清理，需追蹤容量（見 [R6](#r6-磁碟快滿)）。

## R5 `daily.log` 是空的

**症狀**：`sudo tail daily.log` 沒有任何輸出。

**先看**：

```bash-ro
sudo ls -lh /var/log/gitea-maintenance/
```

```bash-ro
sudo tail -n 100 /var/log/gitea-maintenance/daily.log.1
```

**判讀**：日誌每天 00:00 輪替；午夜後當前檔案就是空的，前一天內容在 `.log.1`，更早的是 `.log.2.gz` 之後（用 `zcat` 讀）。**空白不代表沒執行**。

**升級**：連 `.log.1` 與 `.gz` 都沒有紀錄，才查 `sudo crontab -l` 與 `systemctl is-active cron`。

## R6 磁碟快滿

**症狀**：`df` 使用率升高、備份失敗、容器寫入錯誤。

**先看**：

```bash-ro
df -h / /home
```

```bash-ro
sudo du -sh /var/backups/gitea-maintenance/daily /var/backups/gitea-maintenance/weekly
```

```bash-ro
ls -lh /var/log/syslog /var/log/syslog.1
```

**判讀**：常見三個來源——①外送連續失敗使本機 `daily/` 累積（沒有 `REMOTE_SUCCESS` 的不會被自動清理）；②weekly 每份都含完整冷備份與系統檔；③`syslog` 因 `snapd-desktop-integration` 約每 2 秒重啟一次，每天約 170 MB。

**升級**：Linux 管理員。**不要為了騰空間刪掉唯一一份備份**；先確認備機已有校驗過的副本。

## R7 系統時間不對

**症狀**：日誌時間與實際差約 50 分鐘、雙因素驗證碼無效、憑證警告。

**先看**：

```bash-ro
date -u
```

```bash-ro
timedatectl show -p NTPSynchronized -p TimeUSec
```

**判讀**：對照可信任的標準時間。目前主機比標準時間快約 50 分鐘，且為**固定偏移**；chrony 六個來源全部連不上，`Leap status: Normal` 只代表自己跟自己對時。

**升級**：網管（先查內網 NTP 與 UDP 123，見 [網路與連線](network.html)）。**不要在服務運行時直接 `date -s` 手動跳時**，會影響日誌、憑證與雙因素驗證。

## R8 22:00 之後機器立刻重開／隔天 07:00 沒有開機

**症狀**：以為機器已關機，實際整夜在線；或相反，機器真的沒開起來。

**先看**：

```bash-ro
uptime -s
```

```bash-ro
last -x -n 10 reboot shutdown
```

**判讀**：目前已知 22:00 關機後數秒就被喚醒（自 9/22 起），所以 `uptime -s` 約為前一晚 22:00 屬於**目前的已知行為**，原因與驗證步驟見 [排程與電源](schedule.html)。若機器完全沒起來，才是 RTC 鬧鐘或電源問題。

**升級**：機器離線需要現場人員按電源鈕並檢查 BIOS；不要遠端反覆強制重開。

## R9 備機連不到

**症狀**：外送失敗、`ssh` 逾時、`No route to host`。

**先看**（在正式主機）：

```bash-ro
ip route get 192.168.1.3
```

```bash-ro
ssh -o BatchMode=yes -o ConnectTimeout=10 coffee@192.168.1.3 hostname
```

**判讀**：路由應經 `eno1`、來源 `192.168.1.2`（與主要 IP 同一張網卡）。`No route`／逾時先查備機電源、線材、交換器；`Permission denied` 則是金鑰或帳號問題（回到 R4）。

**升級**：備機管理員或網管。

## R10 忘記 Gitea 密碼

**症狀**：使用者無法登入。

**先看**：Gitea 目前**沒有啟用 SMTP**，不會寄出重設信，不要承諾「點忘記密碼就會收到信」。

**判讀**：必須由 Gitea 管理員先確認使用者身分，再於管理介面重設密碼並要求使用者登入後立即更改。

**升級**：Gitea 管理員；不得共用密碼，也不得把密碼貼進聊天或工單。
