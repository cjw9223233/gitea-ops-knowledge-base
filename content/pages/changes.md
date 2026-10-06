## 版本時間線

| 日期 | 變更 | 狀態 |
|---|---|---|
| 9/21 | 主機盤點，設計冷備份與受保護關機 | 基礎文件快照 |
| 9/22 | 安裝新版 root 排程，暫緩備機檢查 | 已部署 |
| 9/22–10/2 | 9 次 daily 在 SSH 階段失敗 | 已找到歷史錯誤；不能全部追溯為同一原因 |
| 10/2 | daily 恢復服務後 SSH 失敗 | 本機發布依程式流程推論，檔案仍需核對 |
| 10/3 | weekly 記錄 SUCCESS，約 292 秒 | 本機成功，不是異機成功 |
| 10/5 | 改成 coffee SSH 傳輸；Linux 23 項測試通過 | 已安裝，正式傳輸待驗收 |

## 部署識別

正式程式：`/usr/local/lib/gitea-maintenance/gitea_maintenance.py`

```text
83513d0e3420b856b794fd6ace8a5bdaa0c75116c7b90849ec64f1be91deef0b
```

本次回復程式：

```text
/var/backups/gitea-cron-changes/20261005T103208Z-coffee-ssh-857242/gitea_maintenance.py.before
```

10/5 實際安裝套件在主機多一層同名資料夾，並不影響正式程式位置。更新器未修改三項 crontab，也未在安裝時觸發停機或備份。

## 未完成事項

1. 新版正式傳輸與遠端 SHA-256 驗收。
2. 隔離還原演練與 RPO／RTO 確認。
3. 歷史補傳、可重試傳輸與 partial 處理。
4. weekly 異機外送與復原設定包。
5. 備機保留、容量告警與值班通知。
6. NTP、22:00 再開機與硬體故障排查。

## 完整報告

[下載 10/5 排程再稽核報告（Markdown）](downloads/cron-review-20261005.md)

本網站整理讀者需要的現行操作，完整報告保留修正前證據及後續補證。舊的 root 建立金鑰方案已撤回，不應再執行。
