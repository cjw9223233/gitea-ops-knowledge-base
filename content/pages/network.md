## 先看這張圖

{{diagram:network}}

!!! tip "白話說明"
    把主機想成一棟大樓：**IP** 是地址、**埠（port）** 是各個窗口、**白名單** 是警衛手上的名單。連得上要同時通過三關——網路上游放行、主機防火牆放行、Gitea 認得你的帳號。**NTP** 是校準大樓時鐘的服務；**NAT** 是讓內部機器共用一個出口。

## 位址與連線資訊

| 項目 | 現況 | 資料日期 |
|---|---|---|
| 使用中網卡 | `eno1`；9/21 記錄 1 Gbps，10/5 補驗證記錄協商 **100 Mb/s** 全雙工，若預期千兆需查線材與交換器 | 2026-10-05 |
| 主要 IP | `10.253.114.160/24` | 2026-10-05 |
| 同網卡第二個 IP | `192.168.1.2/24`（通往備機） | 2026-10-05 |
| 預設閘道 | `10.253.114.254`，經 `eno1` | 2026-10-05 |
| DNS | `10.36.1.1`、`10.254.1.1`；解析正常 | 2026-10-06 |
| 第二張網卡 | `enp5s0`，沒有連線；Wake-on-LAN 仍為 `g` | 2026-10-06 |
| IPv6 | 只有 link-local，沒有 global 位址 | 2026-09-21 |
| 網路管理 | NetworkManager 與 systemd-networkd 皆 active；`eno1` 由 Netplan 產生的 networkd 設定管理；設定檔 `/etc/netplan/coffee_config.yaml` 為 root:root、600 | 2026-09-21 |
| 交換器線索 | `networkctl` 顯示連到 `GS2210` port 1；實體位置與 VLAN 待確認 | 2026-09-21 |
| IP forwarding | IPv4 為 1、IPv6 為 0 | 2026-09-21 |

`192.168.1.2` 與主 IP 在**同一張網卡**，並不是兩條獨立網路的備援。容器 IP 重建後可能改變，Gitea 連資料庫要維持 `db:5432`，不要改成目前看到的 `172.18.0.3`。

## 對外監聽埠與建議

資料日期 2026-10-06（`ss -lntu` 唯讀）。「監聽」不代表所有來源都能連入；反過來，UFW inactive 也不代表沒有防火牆。

| 埠 | 用途 | 綁定位址 | 建議 |
|---|---|---|---|
| TCP 22 | Linux SSH（維運） | 全介面（IPv4／IPv6） | 只給維運來源；長期要關閉 root 與密碼登入，見 [權限與交接](access.html) |
| TCP 3000 | Gitea HTTP | 全介面 | 限核准來源；規劃 HTTPS（目前為明文 HTTP） |
| TCP 2222 | Gitea 內建 Git SSH | 全介面 | 限核准來源；使用個人 Gitea 公鑰 |
| **TCP 9090** | **未確認** | 全介面 | **新出現**：9/21 盤點沒有。先確認行程與用途，再決定開放或關閉；可能與 `/home/myXAMPP` 的容器有關，未證實 |
| TCP 3142 | apt-cacher-ng | 全介面 | 確認實際使用者；沒人用就停用，或限制來源 |
| TCP 5432 | PostgreSQL | 不發布到主機 | 維持現狀，不要為了方便對外開放 |
| UDP 123 | NTP（chrony） | IPv4 全介面 | chrony 允許 `192.168.1.0/24`；確認有人需要，見下方校時 |
| UDP 5353 | mDNS／Avahi | 全介面 | 伺服器通常不需要區網探索，評估停用 |
| TCP 631 | CUPS 列印 | 只有 loopback | 用途待確認 |
| TCP／UDP 53 | systemd-resolved | 只有 loopback | 本機 DNS stub，正常 |

要確認 9090 是什麼（需要 sudo，唯讀）：

```bash-ro
sudo ss -lntp | grep ':9090'
```

## 防火牆的三層

| 層 | 誰管 | 做什麼 |
|---|---|---|
| ① 上游 ACL | 網管 | 決定哪些網段能到達這台主機 |
| ② 主機 iptables | Linux 管理員 | `DOCKER-USER` 鏈裡的白名單，針對 3000／2222；`netfilter-persistent` 為 active |
| ③ Gitea 權限 | Gitea 管理員 | 帳號、組織、專案授權 |

UFW 為 inactive、fail2ban 為 inactive（2026-10-06）。Docker 發布的埠走的封包路徑與一般主機服務不同，不能只看 UFW，要看 `DOCKER-USER` 與 FORWARD／NAT；**不要自行關閉 Docker 的防火牆管理**。[Docker 防火牆文件](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

!!! warning "舊的白名單腳本不能直接執行"
    `/home/Gitea/gitea-access-rules.sh` 會清空整條 `DOCKER-USER`，可能刪掉其他專案的規則；規則只依目的埠、沒有限制入口網卡與目的容器；而且檔案權限是 777，任何本機帳號都能改。請先把寫入權限收回 root，再由網管重構成專屬鏈。新手禁止直接執行。檔案內容讀過，**但沒有執行**，也無法讀取核心裡實際生效的規則。

## 申請新使用者連線

1. PM 記錄申請人、用途、來源 IP、預計到期日與專案。
2. 網管確認是否經 NAT 或 VPN；**真正抵達主機的來源 IP** 才是白名單要用的值。
3. 管理員先備存**現行**規則，確認 22 埠管理通道與現場主控台可用。
4. 經審核後，只加入需要的來源與埠；同時考慮 IPv4、IPv6 與持久化。
5. 從一台允許來源、一台不允許來源分別測 3000／2222；管理用 22 另外測。
6. 維護時段內驗證重啟 Docker 或重開機後規則仍在，保存測試結果與申請單。

申請單欄位範本：

| 欄位 | 填寫 |
|---|---|
| 申請人／專案 | |
| 用途 | |
| 來源 IP（抵達主機時） | |
| 協定與埠 | 3000／2222 |
| 到期日 | |
| 核准人（PM／網管） | |
| 測試結果（允許來源／拒絕來源） | |

只有白名單還不夠，還要另做 [權限與交接](access.html) 的 Gitea 帳號與專案授權。

## 校時（NTP）：目前是壞的

!!! danger "已確認：時鐘比標準時間快約 50 分鐘，且全部時間來源連不上"
    2026-10-05 與 10-06 兩次量測，主機比這台盤點用電腦快 49 分 50 秒與 49 分 49 秒，14 小時內只差 1 秒，所以是**固定偏移**（曾被一次性設錯），不是時鐘漂移。chrony 的 6 個來源（`10.36.1.1`、hinet 三個、Google、NTU）全部 `Reach 0`。

**為什麼 `Leap status: Normal` 會騙人**：`chronyc tracking` 顯示 `Reference ID 7F7F0101`（就是 127.127.1.1，本機時鐘）與 `Stratum 10`，也就是 chrony 在跟自己比對。偏差顯示 0、狀態 Normal，但這不代表已對上標準時間。設定中的 `local stratum 10` 與 `allow 192.168.1.0/24` 還會把這個未校時的時間分給備機。

診斷步驟（皆唯讀）：

```bash-ro
chronyc tracking
```

```bash-ro
chronyc sources -v
```

```bash-ro
ping -c 3 10.36.1.1
```

```bash-ro
resolvectl status
```

```bash-ro
sudo journalctl -u chrony --since "2 days ago" --no-pager | tail -n 40
```

| 現象 | 代表 | 下一步 |
|---|---|---|
| `ping 10.36.1.1` 不通 | 路由或該 NTP 伺服器不接受此主機 | 找網管確認內網 NTP 位置與是否開放 |
| 能 ping 外網、解析網域正常，來源仍全是 Reach 0 | 多半是 **UDP 123 出站被擋** | 請網管開放，或改用內網可達的時間來源 |
| DNS 解析失敗 | DNS 問題 | 先修 DNS |
| 完全連不出去 | 沒有外網 | 需要內網時間來源，不要只換成公用來源 |

修復前建議：把 `local stratum 10` 改為 `local stratum 10 orphan` 或暫時移除 `allow 192.168.1.0/24`，避免把未校時的時間繼續分給備機（此為變更，需先備份 `/etc/chrony/chrony.conf`）。

驗收標準（三項都要成立）：`Reference ID` **不是** `7F7F0101` 且 `Stratum` 小於 10；`chronyc sources` 至少一個 `^*` 且 Reach 非 0；`timedatectl` 顯示 `NTPSynchronized=yes`；備機也一併確認。

!!! warning "修好之後會發生時間跳動"
    設定中有 `makestep 1 3`，校時成功時時鐘可能一次往回跳約 50 分鐘。往回跳會讓日誌時間不連續，也可能讓排程重複執行或錯過窗口。請在**非備份窗口**（避開主機時間 20:25–22:05）、確認沒有維護鎖與備份進行中、先通知使用者後再修；修完後檢查當天日誌與排程有沒有重複。雙因素驗證（TOTP）要等校時修好後再推行。

## 同網卡雙 IP 與 NAT

主機另有 `/home/coffee/scripts/enable-nat.sh`，內容規劃把 `192.168.1.0/24` 經 `eno1` 做 NAT；目前 IP forwarding 確實為 1，但 NAT 規則無法讀取確認。主機可能還替其他設備做出口或校時，**移機或關機前要先確認**，不能只搬 Gitea。備機傳輸走同一個二層網段，不經預設閘道，所以主機到備機的傳輸與 NTP 問題各自獨立。

## IP／DNS 變更清單

!!! warning "這是規劃流程，不是目前已執行的變更"
    變更 IP 前要同步檢查 Netplan、閘道、DNS、上游 ACL、Gitea 的 `DOMAIN`、`SSH_DOMAIN`、`ROOT_URL`、Git remote、Webhook、鏡像目的端與所有使用者文件。

前置：取得**現場主控台**（連線中斷時才能救）、備存原設定、由管理員檢查 YAML。以限時方式驗證：

```bash-stop
sudo netplan try --timeout 120
```

**驗收**：新連線與原連線都正常才按確認保留。**回退**：超時會自動回復，但仍要在主控台確認；原設定備份要先放在安全位置。[Netplan try 說明](https://netplan.readthedocs.io/en/stable/netplan-try/)

## 連不上時的排障

| 症狀 | 看哪裡 |
|---|---|
| 使用者連不上網站或 Git | [事件處理手冊 R1、R2、R3](runbook.html) |
| 備份外送失敗、備機連不到 | [事件處理手冊 R4、R9](runbook.html) |
| 時間不對 | 本頁「校時」與 [事件處理手冊 R7](runbook.html) |

使用者端（Windows PowerShell）：

```powershell-ro
Test-NetConnection 10.253.114.160 -Port 3000
```

主機端：

```bash-ro
ip -br address
```

```bash-ro
ip route
```

```bash-ro
ss -lntu
```

由有 sudo 權限的人補查，輸出只放在限制存取的維運紀錄：

```bash-ro
sudo iptables -S
```

```bash-ro
sudo cat /etc/netplan/coffee_config.yaml
```

## 附錄：白名單腳本中的 IP 清單

!!! note "這是檔案內容，不是生效證據"
    下列是 `gitea-access-rules.sh`（9/21 閱讀）裡的 IPv4 清單。無法確認核心裡實際生效的規則，也無法確認 IPv6 是否有同等限制。

```text
10.253.114.250  10.253.114.117  10.253.111.129
10.253.114.174  10.253.114.175  10.253.111.155
10.253.114.177  10.253.114.157  10.253.114.195
10.253.114.186  10.253.114.194  10.253.114.136
10.253.114.206  10.253.114.210  10.253.114.139
10.253.111.124  10.253.114.198  10.253.114.158
10.253.114.149  10.253.114.129  10.253.114.128
10.253.114.204  172.0.20.162    10.253.111.135
```

`172.0.20.162` 不在 RFC1918 的 `172.16.0.0/12` 私有網段內；可能是現場規劃，也可能需更正，先找網管確認，不自行修改。
