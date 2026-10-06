## 路徑速查

| 工作 | 日誌 | 產出物 |
|---|---|---|
| 平日 20:30 | /var/log/gitea-maintenance/daily.log | 本機 /var/backups/gitea-maintenance/daily/ |
| 每週六 09:00 | /var/log/gitea-maintenance/weekly.log | 本機 /var/backups/gitea-maintenance/weekly/ |
| 每日 22:00 | /var/log/gitea-maintenance/shutdown.log | 僅日誌，沒有備份檔 |
| daily 異機副本 | daily.log 內有遠端校驗結果 | 備機 /home/coffee/gitea-backups/ |

**weekly 目前不會傳到備機。** 主機上的備份與狀態目錄由 root 持有、權限 700，查看時需要 sudo。

## 讀取當前與輪替日誌

```bash
sudo tail -n 100 /var/log/gitea-maintenance/daily.log
```

```bash
sudo tail -n 100 /var/log/gitea-maintenance/weekly.log
```

```bash
sudo tail -n 100 /var/log/gitea-maintenance/shutdown.log
```

```bash
sudo ls -lh /var/log/gitea-maintenance/
```

若當前檔案是空的，查看最近輪替檔；檔名依清單為準。

```bash
sudo tail -n 100 /var/log/gitea-maintenance/daily.log.1
```

```bash
sudo zcat /var/log/gitea-maintenance/daily.log.2.gz
```

## 查本機備份與容量

```bash
sudo ls -lh /var/backups/gitea-maintenance/daily/
```

```bash
sudo ls -lh /var/backups/gitea-maintenance/weekly/
```

```bash
sudo du -sh /var/backups/gitea-maintenance/daily /var/backups/gitea-maintenance/weekly
```

```bash
sudo find /var/backups/gitea-maintenance -maxdepth 3 -type f -printf '%p  %s bytes
'
```

## 查備機（coffee 執行，不加 sudo）

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes coffee@192.168.1.3 'ls -lh /home/coffee/gitea-backups/'
```

如果目錄不存在，可能尚未進入首次正式傳輸，請對照 daily.log；不等於 SSH 認證失敗。

## 檔案與成功標記

| 名稱 | 意義 |
|---|---|
| gitea-cold.tar.gz | Gitea 設定、Git 資料與 PostgreSQL 冷備份 |
| system-files.tar.gz | 週備份的系統檔案 |
| images.txt | 備份當時的容器映像參考 |
| manifest.json | 備份型別與來源資訊 |
| SHA256SUMS | 檔案完整性校驗值 |
| SUCCESS | 本機備份完成，不等於還原演練 |
| REMOTE_SUCCESS | 本機記錄該份備份已通過備機校驗 |
| .partial 結尾資料夾 | 執行中或失敗未完成，先查日誌，不直接刪除 |

同一次正式 daily 應看到下列三種訊息：

```text
Services restored and health check passed
Remote checksum verified: ...
SUCCESS daily
```

單元測試也會輸出模擬的 Remote checksum verified，不能當成正式傳輸證據。資料夾名稱的 Z 為 UTC，例如 20261005T123000Z 對應台灣 10/5 20:30。
