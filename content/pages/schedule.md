## 現行 root crontab

這是 root 的使用者 crontab，時間後不要額外加 root 欄位。

```cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 22 * * * /usr/bin/python3 /usr/local/lib/gitea-maintenance/gitea_maintenance.py shutdown >> /var/log/gitea-maintenance/shutdown.log 2>&1
0 9 * * 6 /usr/bin/python3 /usr/local/lib/gitea-maintenance/gitea_maintenance.py weekly >> /var/log/gitea-maintenance/weekly.log 2>&1
30 20 * * 1-5 /usr/bin/python3 /usr/local/lib/gitea-maintenance/gitea_maintenance.py daily >> /var/log/gitea-maintenance/daily.log 2>&1
```

只查看排程：

```bash
sudo crontab -l
```

## 執行身分與流程

1. root 檢查空間、服務與互斥鎖。
2. 停止 Gitea，再停止 PostgreSQL，確認正常退出後製作冷備份。
3. 恢復 PostgreSQL、Gitea；healthz 通過後移除復原標記。
4. root 讀取受保護封存檔，以 stdin 交給 **runuser coffee 的 SSH**。
5. coffee 使用既有金鑰登入備機 coffee，先寫入 .partial，再校驗並發布。

不建立 root 登入金鑰、不搬移 coffee 私鑰、不放寬本機備份目錄權限。root 排程並沒有搬到 coffee crontab。

## 保護與例外

| 情況 | 行為 |
|---|---|
| daily／weekly 已占鎖 | 另一工作退出；22:00 當次關機跳過 |
| recovery-required.json 存在 | 新備份與關機被阻止，須先確認服務復原 |
| 備機不可達／傳輸失敗 | 保留本機副本，不標記 REMOTE_SUCCESS |
| 主機在排程時間關機 | cron 不會自動補跑錯過的工作 |
| 週備份無合格冷備份 | 失敗退出，不回退為資料庫熱複製 |

## 10/5 部署驗證

- 正式程式：/usr/local/lib/gitea-maintenance/gitea_maintenance.py，root:root，644。
- 備份與狀態目錄仍為 root:root，700。
- Linux 23 項回歸測試全部通過；cron active、healthz pass。
- 尚未取得新版正式傳輸與還原結果。

完整雜湊、回復路徑與稽核證據見 [變更與驗收](changes.html)。不要重跑 9/21 舊安裝器；新版已安裝，無需再建立 root SSH 金鑰。
