# Yisheng AI 助理 - 系統架構與開發技能總結
**日期：** 2026-04-03
**分支：** `feature-web-menu-upgrade` (基於 `feature-auto-slide`)

---

## 一、 最新系統架構與流程分析

### 1. 核心架構：中樞驅動模型 (Hub-and-Spoke)
系統已演進為以 `06_line_webhook.py` 為核心中樞，透過嚴謹的分層架構處理多平台請求：

*   **中樞層 (Controller)**：`06_line_webhook.py` 
    *   負責接收 Line Webhook 事件與 Web Dashboard 的 API 請求。
    *   維護全域的非同步會話狀態（Sessions）與待處理狀態（Pending）。
*   **路由層 (Router)**：`webhook_command_router.py` 
    *   統一管理超過 50 種指令前綴。
    *   實作嚴格的優先權陣列（例如：課程邀約 > 夥伴陪伴 > 市場開發 > 行事曆），確保 Web 端與 Line 端的操作邏輯 100% 同步，且不會發生意圖誤判。
*   **執行層 (Agents)**：20+ 個獨立的業務 Agent（如 `13_followup_agent.py`, `16_course_invite_agent.py`）
    *   專注於特定業務邏輯（CRUD、資料處理、格式化）。
    *   透過類別化（Class-based）設計提供標準的 `handle_command` 接口。
*   **基礎層 (Runtime)**：`common_runtime.py` 
    *   提供統一的底層服務，包含跨平台 AI 調用（如 Codex CLI 環境變數解析）、日誌記錄（Log）與環境設定（Config）讀取。

### 2. 指令執行生命週期
1.  **輸入觸發**：使用者透過 Web Dashboard 填寫表單送出，或在 Line 傳送文字指令。
2.  **預處理攔截**：中樞層優先攔截快速選擇（如數字編號）、特殊狀態（如等待上傳圖片）或通用系統指令。
3.  **精確分流**：指令進入 `webhook_command_router`，透過 `_starts_with_any` 與指令前綴比對，將請求導向專屬的 Agent。
4.  **AI 策略生成**：Agent（如 `FollowupAgent`）收集本地資料庫（CSV/JSON）中的原始數據，呼叫 `AIPromptManager` 取得外部化範本，並傳入 `Codex CLI` 進行深度邏輯推理與文案生成。
5.  **回饋渲染**：結果透過 Flask API 立即回傳至 Web 端，並觸發動態 UI 變化（如顯示資料詳情、管理按鈕），或透過 Line API 推播給使用者。

---

## 二、 維護修改系統的開發技能 (Skills) 總結

在穩定系統架構與升級 Web 操作體驗的過程中，累積並驗證了以下關鍵的工程準則與開發技能：

### 1. 外科手術式修正 (Surgical Edits & Micro-Refactoring)
*   **實踐**：在處理動輒千行的舊有程式碼（如 `webhook_web_views.py`）時，嚴格避開全檔案重構。採用精確的 `replace` 策略進行局部邏輯補強。
*   **價值**：保留了其他開發者在不同分支中的手動微調（例如特定的 CSS 樣式或 HTML 排版），有效防止因大範圍改動引入未知的語法錯誤 (Syntax Error)，降低回歸測試成本。

### 2. 強韌的跨語言數據交換 (Robust Data Injection)
*   **實踐**：放棄直接在 JavaScript 中使用 `const data = {json_string};` 嵌入 JSON。改用 `<script id="data-id" type="application/json">` 標籤存放後端注入的數據，並在 JS 端使用 `JSON.parse(document.getElementById('data-id').textContent || "[]")` 讀取。
*   **價值**：徹底解決了 Python 的 f-string 轉義、引號衝突以及換行符號導致的 JavaScript 解析中斷（Fatal Error），確保即便資料損毀，前端介面（如左側選單）依然能正常渲染。

### 3. 模組載入自愈機制 (Dynamic Module Resolution)
*   **實踐**：針對以數字開頭的檔案（如 `20_ai_prompt_manager.py`），Python 無法直接使用 `import` 語法（會觸發 `invalid decimal literal`）。改用 `importlib.util.spec_from_file_location` 實現動態載入。
*   **價值**：突破了舊有檔案命名規範的限制，並在 Agent 內部實作雙重路徑檢查（相對路徑與絕對路徑 fallback），確保系統在不同執行環境下皆能正確定位模組。

### 4. 高互動性 UI 表單連動 (Reactive Form Hydration)
*   **實踐**：在原生 JavaScript 環境下實作了複雜的表單連動邏輯（如「修改課程文宣」、「跟進報告」）。
    *   **動態下拉選單**：使用 `_hydrate...Select` 攔截特定表單，將純文字輸入框動態轉換為帶有詳細資訊的下拉選單。
    *   **即時預覽與防覆寫**：掛載 `onchange` 事件，選取 ID 後透過異步 API 獲取資料，即時生成「【目前內容預覽】」區塊，並利用 `dataset.userEdited` 標記防止覆寫使用者已修改的內容。
*   **價值**：將 Web Dashboard 的操作體驗從「單向指令發送」提升為「雙向資料互動」，大幅降低使用者的操作認知負擔。

### 5. AI 邏輯外部化與容錯架構 (Decoupled Prompts & AI Fallbacks)
*   **實踐**：
    *   **Prompt 管理**：將原本硬編碼在 Agent 內的 AI 提示詞（如跟進報告的診斷邏輯）抽離至 `ai_prompts.json`，並透過 `AIPromptManager` 統一調度。
    *   **CLI 自愈**：在 `common_runtime.py` 的 `run_codex_cli` 中實作 Windows 路徑解析邏輯（動態尋找 `node.exe` 與 `codex.js`），解決 `WinError 2`。
    *   **優雅降級**：在呼叫 AI 時加入 `try-catch`，當 AI 服務不可用時，自動回傳預設的基礎關懷建議。
*   **價值**：實現了系統邏輯的熱更新（Hot-Reload），使用者可直接透過網頁端「修改AI提示詞」調整系統行為，同時保證了核心業務的高可用性。

---

**狀態快照**：
系統目前運行穩定，已成功排除 `AttributeError`、`SyntaxError` 以及路由誤判等問題，並在 Web 端提供了極具彈性且高效率的「表單導向」操作介面。