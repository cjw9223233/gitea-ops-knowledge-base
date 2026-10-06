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

```bash-ro
sudo crontab -l
```

2026-10-05 已讀取確認內容與上方一致；syslog 顯示三項工作都依時間觸發。

## 執行身分與流程

1. root 檢查空間、服務與互斥鎖。
2. 停止 Gitea，再停止 PostgreSQL，確認正常退出後製作冷備份。
3. 恢復 PostgreSQL、Gitea；healthz 通過後移除復原標記。
4. root 讀取受保護封存檔，以 stdin 交給 **runuser coffee 的 SSH**。
5. coffee 使用既有金鑰登入備機 coffee，先寫入 `.partial`，再校驗並發布。

不建立 root 登入金鑰、不搬移 coffee 私鑰、不放寬本機備份目錄權限。root 排程並沒有搬到 coffee crontab。

## 保護與例外

| 情況 | 行為 |
|---|---|
| daily／weekly 已占鎖 | 另一工作退出；22:00 當次關機跳過 |
| `recovery-required.json` 存在 | 新備份與關機被阻止，須先確認服務復原 |
| 備機不可達／傳輸失敗 | 保留本機副本，不標記 `REMOTE_SUCCESS`（失敗時本機備份不會被清理，見 [備份與還原](backup.html)） |
| 主機在排程時間關機 | cron 不會自動補跑錯過的工作 |
| 週備份無合格冷備份 | 失敗退出，不回退為資料庫熱複製 |

## 電源與喚醒：22:00 關機後立刻被叫醒

!!! warning "目前行為與設計不同"
    設計是「22:00 關機，隔天約 07:00 由 BIOS 的 RTC 鬧鐘開機」。實際上自 **2026-09-22** 起，13 個夜晚的關機都在**數秒後**又開機，機器整夜在線，隔天 07:00 沒有開機。

### 已確認（資料日期 2026-10-06）

| 項目 | 證據 |
|---|---|
| 關機是真的斷電 | `journalctl -b -1` 結尾為 `System Power Off`、`Shutting down`、`Journal stopped`，時間 22:00:05 |
| 斷電後很快被喚醒 | 下一次開機的核心在 22:00:22–26 開始，扣掉開機自檢，電源在斷電後數秒內被重新打開 |
| 9/17–9/19 正常 | `last -x`：22:00 關機、關機持續 9 小時，隔天 07:00 開機 |
| 9/22 起全部異常 | `last -x` 的 `shutdown` 與下一個 `reboot` 同為 22:00，間隔 0 分鐘 |
| RTC 鬧鐘設定還在 | `/proc/driver/rtc` 的 `alrm_time` 為 07:00:00；RTC 為本地時區 |
| 網路喚醒已開啟 | `eno1` 為 `Wake-on: g`（收到 magic packet 就開機）且連線中；`enp5s0` 同為 `g` 但沒有連線 |
| 其他喚醒來源也開啟 | ACPI 喚醒清單中 `GLAN`、`EHC1`、`EHC2`、`XHC`、`PS2K`、`PWRB` 皆為 enabled |

### 已排除

不是 cron 沒觸發（每晚都有紀錄）、不是 RTC 鬧鐘消失、不是新核心（問題比 9/25 升級更早）、不是關機失敗或被韌體重開（日誌是正常的 ACPI 斷電）。

### 候選原因與驗證

| # | 候選 | 為什麼可疑 |
|---|---|---|
| H1 | 區網內有設備在偵測到主機離線後送出 Wake-on-LAN | `Wake-on: g` 已開啟且網路線連著；開機總在斷電後數秒內；備機與主機在同一個二層網段 |
| H2 | 9/22 凌晨 02:22–03:29 現場操作時 BIOS 設定被改動 | 當晚有多次短開機與一次 0 秒開機，是進 BIOS 的典型樣態；9/22 22:00 就是第一個立即開機的夜晚 |
| H3 | USB 裝置（鍵盤、滑鼠、KVM、UPS 訊號線）在斷電時產生喚醒事件 | USB 控制器喚醒為 enabled；但 9/17–9/19 同樣設定下沒有發生 |

**驗證 A（可逆）：暫時關掉 eno1 的 WoL，重開機後自動還原。**

```bash-chg
sudo ethtool -s eno1 wol d
```

```bash-ro
sudo ethtool eno1 | grep -i 'wake-on'
```

接著等下一次自動關機。維持關機到隔天 07:00 才開機，代表是 H1（網路喚醒）；仍在 22:00 立即開機，代表不是 WoL，改查 BIOS 與 USB。**風險：**若 07:00 的 RTC 開機也失敗，Gitea 會一直離線到有人按電源鈕，請確保當天早上有人在場。

**驗證 B：在備機抓 WoL 封包，找出誰送的。**於主機時間 21:59–22:02 之間，在備機執行：

```bash-ro
sudo timeout 240 tcpdump -i any -nn -e -c 20 'ether proto 0x0842 or udp port 9 or udp port 7'
```

輸出會顯示 magic packet 的來源 MAC 與 IP。

**驗證 C：備機上是否有「主機離線就喚醒」的腳本。**

```bash-ro
sudo grep -rniE 'wakeonlan|etherwake|ether-wake|wol' /etc/cron* /var/spool/cron /etc/systemd /home/coffee 2>/dev/null | head -n 30
```

**驗證 D（現場）：**進 BIOS 確認 RTC 鬧鐘仍是 07:00、「Restore on AC Power Loss」為 Power Off，並關閉不需要的 Wake on LAN、PCI-E 與 USB 喚醒。

### 找到原因之後

關閉喚醒來源後要**持久化**（`ethtool` 設定重開機會還原）：用 NetworkManager 連線設定、`systemd .link`（`WakeOnLan=off`）或開機執行的 systemd unit，並在重開機後再確認 `Wake-on: d`。目前網路設定在 `/etc/netplan/coffee_config.yaml`，需 root 才能讀，要先確認使用 networkd 或 NetworkManager 再選方式。驗收標準：連續 7 晚，22:00 後 6 小時內沒有開機紀錄，且隔天 07:00 前後有開機紀錄。

若 24 小時運轉其實可以接受，也可以改為取消每日關機、改成每週重開，不再依賴 2012 年的 BIOS。這是業務決定。

## 10/5 部署驗證

- 正式程式：`/usr/local/lib/gitea-maintenance/gitea_maintenance.py`，root:root，644。
- 備份與狀態目錄仍為 root:root，700。
- Linux 23 項回歸測試全部通過；cron active、healthz pass。
- 10/5 20:30 的 daily 是修正版第一次正式外送：備機出現完整目錄；日誌確認見 [Log 與產出物](logs.html)。

完整雜湊、回復路徑與稽核證據見 [變更與驗收](changes.html)。不要重跑 9/21 舊安裝器；新版已安裝，無需再建立 root SSH 金鑰。
