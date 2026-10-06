## 每日五分鐘

在正式主機 coffee 執行；以下只讀取狀態。

```bash-ro
date -Is
```

```bash-ro
systemctl is-active cron
```

```bash-ro
docker ps --format '{{.Names}} {{.Status}}'
```

```bash-ro
curl --max-time 10 -fsS http://127.0.0.1:3000/api/healthz
```

```bash-ro
df -h / /home
```

healthz 預期 `status: pass`。再補兩項（唯讀）：

```bash-ro
uptime -s
```

`uptime -s` 是上次開機時間。目前每晚 22:00 後會重開機，預期落在前一晚約 22:00；若不是，查 [排程與電源](schedule.html)。

```bash-ro
timedatectl show -p NTPSynchronized
```

目前預期為 `no`（校時尚未修復）；變成 `yes` 才代表校時修好，但仍要用 `chronyc tracking` 確認 Reference ID。

接著查看 [daily 工作日誌](logs.html)，確認最近的異機備份，而不只是容器仍在執行。

## 依症狀處理

| 症狀 | 下一步 |
|---|---|
| Permission denied (publickey,password) | 確認本機 SSH 執行帳號與既有金鑰，不能只看遠端 coffee 帳號 |
| No route to host／timeout | 先查備機電源、路由、鄰居與 TCP 22 |
| Another backup/shutdown job is active | 查目前工作，不移除鎖檔來強行執行 |
| RECOVERY REQUIRED | 確認 DB、Gitea 與 healthz，保留紀錄後依復原程序處理 |
| 空白 daily.log | 日誌每天 00:00 輪替；查 .log.1 或 .gz；不直接判定沒執行 |
| 22:00 後機器立刻重開 | 屬已知問題，見 [排程與電源](schedule.html)；不要反覆強制重開 |
| syslog 很大、訊息被淹沒 | 見 [系統與網路](system.html) 的 snap 重啟迴圈 |
| BIOS 看不到 SSD | 依 [硬碟與開機排查](hardware.html) 保全備份、安排硬體檢查 |

## 需要交接的資訊

記錄事件時間與時區、工作 ID、原始錯誤、最後本機／異機成功時間，以及操作前後服務狀態。不要將密碼、私鑰或資料庫連線密碼貼入交接紀錄。
