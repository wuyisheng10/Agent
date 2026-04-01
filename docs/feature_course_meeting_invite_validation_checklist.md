# feature/course-meeting-invite validation checklist

Use this checklist after switching back to the refactor branch.

## LINE functions

| No. | Feature | Input command / action | Expected reply action |
| --- | --- | --- | --- |
| 1 | 新增潛在家人 | `interactive flow` | Reply should show a copyable command template only. |
| 2 | 查詢培訓進度 | `interactive flow` | Reply should show a copyable command template only. |
| 3 | 跟進報告 | `跟進報告` | Reply should execute immediately and show result. |
| 4 | 激勵夥伴 | `interactive flow` | Reply should show a copyable command template only. |
| 5 | 里程碑記錄 | `interactive flow` | Reply should show a copyable command template only. |
| 6 | 查詢所有夥伴 | `查詢夥伴` | Reply should execute immediately and show result. |
| 7 | 查詢待跟進夥伴 | `查詢待跟進夥伴` | Reply should execute immediately and show result. |
| 8 | 查詢今日行事曆 | `查詢行事曆` | Reply should execute immediately and show result. |
| 9 | 查詢過往行事曆 | `查詢過往行事曆` | Reply should execute immediately and show result. |
| 10 | 新增行事曆事件 | `interactive flow` | Reply should show a copyable command template only. |
| 11 | 查詢目前歸類模式 | `歸類模式` | Reply should execute immediately and show result. |
| 12 | 設定歸類模式 | `interactive flow` | Reply should show a copyable command template only. |
| 13 | 設定人員＋歸類模式 | `interactive flow` | Reply should show a copyable command template only. |
| 14 | 關閉歸類模式 | `關閉歸類模式` | Reply should execute immediately and show result. |
| 15 | 查詢所有歸檔 | `查詢歸檔` | Reply should execute immediately and show result. |
| 16 | 查詢指定人員歸檔 | `interactive flow` | Reply should show a copyable command template only. |
| 17 | 整理今日培訓記錄 | `整理` | Reply should execute immediately and show result. |
| 18 | 新增夥伴 | `interactive flow` | Reply should show a copyable command template only. |
| 19 | 跟進夥伴 | `interactive flow` | Reply should show a copyable command template only. |
| 20 | 顯示所有指令 | `指令集` | Reply should execute immediately and show result. |
| 21 | 💊 營養保健歸檔 (Nutrilite) | `營養保健歸檔` | Reply should execute immediately and show result. |
| 22 | 💄 美容保養歸檔 (Artistry) | `美容保養歸檔` | Reply should execute immediately and show result. |
| 23 | 🧹 居家清潔歸檔 (Home) | `居家清潔歸檔` | Reply should execute immediately and show result. |
| 24 | 🪥 個人護理歸檔 (Glister) | `個人護理歸檔` | Reply should execute immediately and show result. |
| 25 | 🍳 廚具與生活用品歸檔 | `廚具生活歸檔` | Reply should execute immediately and show result. |
| 26 | 💧 空氣與水處理設備歸檔 | `空水設備歸檔` | Reply should execute immediately and show result. |
| 27 | ⚖️ 體重管理與運動營養歸檔 | `體重管理歸檔` | Reply should execute immediately and show result. |
| 28 | 🌸 香氛與個人風格歸檔 | `香氛風格歸檔` | Reply should execute immediately and show result. |
| 29 | 🛠️ 事業工具與教育系統歸檔 | `事業工具歸檔` | Reply should execute immediately and show result. |
| 30 | 👤 人物故事歸檔 | `menu 30 -> input person name` | Reply should ask for person name, then enter story archive mode. |
| 31 | 📖 產品故事歸檔 | `產品故事歸檔` | Reply should execute immediately and show result. |
| 32 | 查詢潛在家人 | `查詢潛在家人` | Reply should execute immediately and show result. |
| 33 | 加入潛在家人資訊 | `menu 33 -> select person / upload file` | Reply should enter prospect-file flow and wait for file/text. |
| 34 | 查詢課程會議 | `查詢課程會議` | Reply should execute immediately and show result. |
| 35 | 新增課程會議 | `interactive flow` | Reply should show a copyable command template only. |
| 36 | 從行事曆加入課程 | `interactive flow` | Reply should show a copyable command template only. |
| 37 | 刪除課程會議 | `interactive flow` | Reply should show a copyable command template only. |
| 38 | 查詢課程文宣 | `查詢課程文宣` | Reply should execute immediately and show result. |
| 39 | 新增課程文宣 | `interactive flow` | Reply should show a copyable command template only. |
| 40 | 優化課程文宣 | `interactive flow` | Reply should show a copyable command template only. |
| 41 | 邀約文宣－潛在家人 | `interactive flow` | Reply should show a copyable command template only. |
| 42 | 邀約文宣－跟進夥伴 | `interactive flow` | Reply should show a copyable command template only. |
| 43 | 查詢已產生的邀約文宣 | `查詢已產生的今日之後會議邀約文宣` | Reply should execute immediately and show result. |
| 44 | 修改已產生的邀約文宣 | `interactive flow` | Reply should show a copyable command template only. |
| 45 | 📧 寄送每日報告 | `寄送每日報告` | Reply should execute immediately and show result. |
| 46 | 📊 查詢營養素標準 | `interactive flow` | Reply should show a copyable command template only. |
| 47 | 🔬 營養素運作原理 | `interactive flow` | Reply should show a copyable command template only. |
| 48 | 📋 列出所有營養素 | `列出營養素` | Reply should execute immediately and show result. |
| 49 | 📥 更新官方營養素標準 | `下載營養素標準` | Reply should execute immediately and show result. |
| 50 | 🍽️ 開始飲食評估 | `interactive flow` | Reply should show a copyable command template only. |
| 51 | 🥗 執行飲食評估 | `interactive flow` | Reply should show a copyable command template only. |
| 52 | 📷 設定下一張餐別 | `interactive flow` | Reply should show a copyable command template only. |
| 53 | 📈 飲食評估狀態 | `飲食評估狀態` | Reply should execute immediately and show result. |
| 54 | 🗑️ 清除飲食評估 | `清除飲食評估` | Reply should execute immediately and show result. |
| 55 | 🏷️ 設定歸檔對象 | `interactive flow` | Reply should show a copyable command template only. |

## Web buttons

### 🎯 市場開發

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 新增潛在家人 | form | `新增潛在家人` | Click should open dialog; submit should build command and show result block. |
| 查詢潛在家人 | exec | `查詢潛在家人` | Click should immediately show result block. |
| 加入潛在家人資訊 | form | `加入潛在家人資訊` | Click should open dialog; submit should build command and show result block. |

### 📚 培訓系統

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 查詢培訓進度 | form | `查詢培訓進度` | Click should open dialog; submit should build command and show result block. |

### 🤝 夥伴陪伴

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 跟進報告 | exec | `跟進報告` | Click should immediately show result block. |
| 激勵夥伴 | form | `激勵夥伴` | Click should open dialog; submit should build command and show result block. |
| 里程碑記錄 | form | `里程碑記錄` | Click should open dialog; submit should build command and show result block. |
| 查詢所有夥伴 | exec | `查詢夥伴` | Click should immediately show result block. |
| 查詢待跟進夥伴 | exec | `查詢待跟進夥伴` | Click should immediately show result block. |
| 新增夥伴 | form | `新增夥伴` | Click should open dialog; submit should build command and show result block. |
| 更新夥伴 | form | `更新夥伴` | Click should open dialog; submit should build command and show result block. |
| 跟進夥伴 | form | `跟進夥伴` | Click should open dialog; submit should build command and show result block. |

### 🗓️ 行事曆

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 查詢今日行事曆 | exec | `查詢行事曆` | Click should immediately show result block. |
| 查詢過往行事曆 | exec | `查詢過往行事曆` | Click should immediately show result block. |
| 查詢全部行事曆 | exec | `查詢全部行事曆` | Click should immediately show result block. |
| 新增行事曆事件 | form | `新增行事曆事件` | Click should open dialog; submit should build command and show result block. |

### 📂 歸類模式

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 查詢目前歸類模式 | exec | `歸類模式` | Click should immediately show result block. |
| 設定歸類模式 | form | `設定歸類模式` | Click should open dialog; submit should build command and show result block. |
| 關閉歸類模式 | exec | `關閉歸類模式` | Click should immediately show result block. |
| 查詢所有歸檔 | exec | `查詢歸檔` | Click should immediately show result block. |
| 查詢指定人員歸檔 | form | `查詢指定人員歸檔` | Click should open dialog; submit should build command and show result block. |

### 📖 培訓記錄

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 整理今日培訓記錄 | exec | `整理` | Click should immediately show result block. |
| 整理指定日期記錄 | form | `整理指定日期記錄` | Click should open dialog; submit should build command and show result block. |
| 再次整理（強制覆蓋） | exec | `再次整理` | Click should immediately show result block. |
| 查詢培訓記錄 | form | `查詢指定日期培訓記錄` | Click should open dialog; submit should build command and show result block. |

### 🛍️ 安麗產品歸檔

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 💊 營養保健 (Nutrilite) | exec | `營養保健歸檔` | Click should immediately show result block. |
| 💄 美容保養 (Artistry) | exec | `美容保養歸檔` | Click should immediately show result block. |
| 🧹 居家清潔 (Home) | exec | `居家清潔歸檔` | Click should immediately show result block. |
| 🪥 個人護理 (Glister) | exec | `個人護理歸檔` | Click should immediately show result block. |
| 🍳 廚具與生活用品 | exec | `廚具生活歸檔` | Click should immediately show result block. |
| 💧 空氣與水處理設備 | exec | `空水設備歸檔` | Click should immediately show result block. |
| ⚖️ 體重管理與運動營養 | exec | `體重管理歸檔` | Click should immediately show result block. |
| 🌸 香氛與個人風格 | exec | `香氛風格歸檔` | Click should immediately show result block. |
| 🛠️ 事業工具與教育系統 | exec | `事業工具歸檔` | Click should immediately show result block. |

### 📝 故事分類

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 👤 人物故事歸檔 | form | `人物故事歸檔` | Click should open dialog; submit should build command and show result block. |
| 📖 產品故事歸檔 | exec | `產品故事歸檔` | Click should immediately show result block. |

### 🎓 課程邀約

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 查詢課程會議 | exec | `查詢課程會議` | Click should immediately show result block. |
| 新增課程會議 | form | `新增課程會議` | Click should open dialog; submit should build command and show result block. |
| 從行事曆加入課程 | form | `從行事曆加入課程` | Click should open dialog; submit should build command and show result block. |
| 修改課程會議 | form | `修改課程會議` | Click should open dialog; submit should build command and show result block. |
| 刪除課程會議 | form | `刪除課程會議` | Click should open dialog; submit should build command and show result block. |
| 查詢課程文宣 | exec | `查詢課程文宣` | Click should immediately show result block. |
| 新增課程文宣 | form | `新增課程文宣` | Click should open dialog; submit should build command and show result block. |
| 優化課程文宣（AI） | form | `優化課程文宣` | Click should open dialog; submit should build command and show result block. |
| 邀約文宣－潛在家人（AI） | form | `潛在家人邀約文宣` | Click should open dialog; submit should build command and show result block. |
| 邀約文宣－跟進夥伴（AI） | form | `跟進夥伴邀約文宣` | Click should open dialog; submit should build command and show result block. |
| 查詢已產生的邀約文宣 | exec | `查詢已產生的今日之後會議邀約文宣` | Click should immediately show result block. |
| 修改已產生的邀約文宣 | form | `修改已產生的邀約文宣` | Click should open dialog; submit should build command and show result block. |

### 📧 每日報告

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 寄送每日報告 | exec | `寄送每日報告` | Click should immediately show result block. |

### 🥗 營養評估

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 查詢營養素標準 | form | `查詢營養素標準` | Click should open dialog; submit should build command and show result block. |
| 營養素運作原理 | form | `查詢營養素運作原理` | Click should open dialog; submit should build command and show result block. |
| 列出所有營養素 | exec | `列出營養素` | Click should immediately show result block. |
| 更新官方標準 | exec | `下載營養素標準` | Click should immediately show result block. |
| 開始飲食評估 | form | `開始飲食評估` | Click should open dialog; submit should build command and show result block. |
| 設定歸檔對象 | form | `設定歸檔對象` | Click should open dialog; submit should build command and show result block. |
| 設定下一張餐別 | form | `設定餐別` | Click should open dialog; submit should build command and show result block. |
| 執行飲食評估 | form | `執行飲食評估（AI分析）` | Click should open dialog; submit should build command and show result block. |
| 飲食評估狀態 | exec | `飲食評估狀態` | Click should immediately show result block. |
| 清除飲食評估 | exec | `清除飲食評估` | Click should immediately show result block. |

### ❓ 說明

| Button | Type | Command / dialog | Expected action |
| --- | --- | --- | --- |
| 顯示所有指令 | exec | `指令集` | Click should immediately show result block. |

## Validation focus

- Multi-step LINE flows must be interruptible by explicit commands.
- Archive-mode actions must not fall back to intent-analysis replies.
- Web form dialogs must render select/date/time fields and submit successfully.
- Side-effect actions should be checked with real output: ??, ????, ??????, ???????.