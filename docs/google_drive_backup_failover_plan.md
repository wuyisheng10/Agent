# 兩台一般電腦 + Google Drive 備援方案

## 目的

這份說明文件提供目前系統在低成本條件下的正式運作方案：

- 主機 A 正式運行系統
- 主機 B 作為備援待命機
- Google Drive 負責異地同步與資料備份

這個方案適合目前約 5 人使用的規模。

## 適用情境

適合：

- 需要降低硬體成本
- 可接受故障時手動切換
- 想保有異地備份
- 目前主要是單一 LINE/Web 系統服務

不適合：

- 要求完全無縫自動切換
- 要求雙活架構
- 要求資料庫等級即時一致性

## 架構角色

### 主機 A

正式運行主機，負責：

- `python agents/06_line_webhook.py`
- LINE Webhook
- 網頁 `/web`
- 每日排程
- AI 相關流程
- 檔案歸檔與寄信

### 主機 B

備援主機，平時負責：

- 保持程式碼同步
- 保持必要資料同步
- 故障時手動接手運行

### Google Drive

用途：

- 異地備份
- 備援主機同步副本
- 歷史資料保留

不建議拿來做：

- 即時雙活同步
- 執行期狀態共享
- 高頻寫入狀態管理

## 建議同步內容

建議同步到 Google Drive 的內容：

- `output/training/`
- `output/calendar/`
- `output/classified/`
- `output/partners/`
- `output/nutrition_reports/`
- `config/ai_prompts.json`
- `config/ai_skills.json`
- `docs/`
- `logs/`（可選）

## 不建議同步內容

不建議直接同步到 Google Drive 作為正式即時資料來源：

- `__pycache__/`
- `.git/`
- 執行中的暫存檔
- session 狀態暫存
- lock / pid 類檔案
- 測試暫存目錄
- 高頻寫入的執行期 cache

## 程式碼與資料分工

### 程式碼同步

建議使用：

- `git`

原則：

- 主機 A、B 都從同一個 git branch 更新
- 每次部署前先 pull 最新版本

### 資料同步

建議使用：

- Google Drive for desktop

原則：

- 同步重要輸出資料與設定檔
- 不把 Google Drive 當成即時資料庫

## 建議資料夾配置

### 正式系統目錄

主機 A、B 均保留：

- 專案主目錄
- `output/`
- `config/`
- `.env`

### 同步策略

- 程式碼：用 `git`
- 資料：用 Google Drive
- 設定：以 `.env` 本機維護為主

## 備援切換流程

當主機 A 故障時：

1. 到主機 B 確認 Google Drive 已同步完成
2. 檢查 `.env` 是否完整
3. 啟動系統：

```powershell
python agents/06_line_webhook.py
```

4. 啟動對外入口（例如 ngrok 或其他固定入口）
5. 更新 LINE Webhook URL（若入口變更）
6. 驗證以下功能：

- LINE 可正常回訊
- 網頁 `/web` 可開啟
- 寄信功能正常
- 排程功能正常
- 歸檔資料可讀取

## 日常維運建議

### 每天

- 確認 Google Drive 是否同步正常
- 確認主機 A 是否正常運行

### 每週

- 在主機 B 手動測一次啟動
- 檢查最近的資料是否都有同步到位

### 每次更新功能後

- 主機 A 更新程式碼
- 主機 B 同步更新程式碼
- 確認 `.env`、`config/ai_prompts.json`、`config/ai_skills.json`

## 優點

- 成本低
- 可做到異地備份
- 可在主機故障時人工接手
- 對目前 5 人使用規模足夠

## 缺點

- 不是即時雙活
- 不是自動 HA
- 故障切換需要人工操作
- Google Drive 有同步延遲風險

## 最終建議

對目前這套系統，最務實的方案是：

- 主機 A 正式運行
- 主機 B 備援待命
- Google Drive 做異地同步與備份
- 故障時手動切換

這個方案比雙 NAS 或雙 VM 便宜很多，對目前使用規模足夠，而且可逐步升級。
