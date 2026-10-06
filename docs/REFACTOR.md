# 網站重構紀錄

日期：2026-10-06；維運事實基準：2026-10-05 18:33。

## 問題與改善

舊版把完整舊報告直接放進頁面，9/22 的「備機未開機」狀態也留在首頁。新版本將現在的操作指南與歷史證據分開，讓接手者直接查排程、讀 log、找備份、處理故障。

- 保留原 7 個 HTML 路徑，新增 logs、hardware、changes 共 10 頁。
- root 排程與 coffee SSH 身分分開解釋；撤回建立 root 金鑰的舊建議。
- 納入正式程式 SHA-256、安裝結果、Linux 23 項測試及回復檔位置。
- 明確標示異機正式傳輸／還原待驗收、weekly 尚未外送、歷史失敗尚不補傳。
- 增加 logrotate 後空日誌的解讀、SUCCESS／REMOTE_SUCCESS／partial 差異與 UTC 命名說明。
- 納入 SSD 與開機問題證據，避免把其他 ATA 通道錯誤當成系統 SSD 損壞。
- 內容、模板與樣式分離；同一 build 輸出根目錄與 dist，修復原始 generator 固定寫 dist 卻 repo 只使用根目錄的維護落差。

## 驗證

10 頁的站內連結、錨點、單一 h1、目前導覽標記、繁體中文語言、文件快照提醒與 root/dist 檔案一致性由 validate_site.py 驗證。JavaScript 使用 node --check；本機 HTTP 首頁回覆 200。

未執行正式主機命令或修改維運排程；未推送 GitHub。實際浏览器視覺檢查與 Sites 正式發佈若未完成，應於交付時明確說明，不把靜態驗證當作瀏覽器驗證。

## 後續更新

取得正式 daily.log 與備機 checksum 後，才更新異機驗收狀態。更新證據日期時同步修改共用模板、首頁及相關指南，不只替換首頁日期。新內容先放 content/pages，重新 build 與 validate，再提交來源及產生檔。
