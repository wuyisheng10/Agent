# Development Skill Library

這份文件整理目前這套系統開發過程中，最值得沉澱成可重複使用 skill 的 6 類能力。

目標不是記錄功能，而是記錄「之後再做類似任務時，應該如何開工、如何拆解、如何驗證」。

## 1. `line-webhook-modularization`

### 何時使用
- 單一 webhook 檔案過大
- LINE、web、API、state、router 混在同一檔
- 改一個功能容易牽動整體

### 主要目標
- 把大檔拆成組裝層 + 模組層
- 讓 command routing、web views、api routes、state、runtime、line events 分離
- 保持重構過程中功能不中斷

### 標準做法
1. 先盤點主檔責任
2. 優先抽常數、文字、state、helper
3. 再抽 command router
4. 再抽 web views / api routes
5. 最後抽 line media / line events / runtime
6. 每一批拆完都跑快速全測

### 驗證重點
- `py_compile`
- LINE 指令主流程
- `/web` 和 `/api/*`
- 歸檔、課程邀約、營養評估等跨模組流程

## 2. `staged-archive-flow`

### 何時使用
- 使用者先上傳檔案，再選分類
- 需要兩階段或三階段歸檔
- LINE / web 都可能發生競態與晚到事件

### 主要目標
- 檔案先暫存
- 再選分類
- 再輸入目錄名稱
- 避免背景 thread、晚到檔案覆蓋狀態

### 標準做法
1. 建立 pending state
2. 定義 `collecting / awaiting_choice / awaiting_folder_name`
3. 選項確認後鎖定 `selected_option`
4. 晚到事件只能追加項目，不能重設流程
5. 取消時清掉狀態與暫存檔

### 驗證重點
- LINE 選數字後輸入目錄名
- web 上傳後輸入目錄名
- 延遲選單 thread 不可覆蓋現有狀態
- 同一批素材追加上傳不應洗掉已選選項

## 3. `line-web-full-validation`

### 何時使用
- LINE `5168` 執行選單持續擴大
- web 按鈕與表單越來越多
- 需要避免入口有功能但沒接上

### 主要目標
- 建立完整入口驗證矩陣
- 把 LINE 選單、web 直達按鈕、web 表單按鈕全部跑過
- 對新增功能做回歸保護

### 標準做法
1. 建立執行選單樣本
2. 建立 web 直達按鈕樣本
3. 建立 web form 樣本
4. 為假 agent / fake module 補最小可用回應
5. 新增功能時同步補進驗證矩陣

### 驗證重點
- LINE 選單數字對應指令正確
- web form 組字串正確
- 長流程按鈕要確認是否進入正確 state

## 4. `prompt-skill-management`

### 何時使用
- AI 功能越來越多
- 需要調 prompt，但又不想改程式
- 需要把「生成文字」和「流程策略」分開管理

### 主要目標
- 提供 prompt 預覽、查詢、更新
- 提供 skill 預覽、查詢、更新
- web / LINE 都能操作

### 標準做法
1. 建 prompt manager
2. 建 skill manager
3. 把配置存成 JSON
4. API 提供 list / get / update
5. web 端修改前先預覽現有內容
6. 把實際 agent 接到 manager

### 驗證重點
- 查詢全部
- 查詢單一 key
- 更新後 agent 是否真的讀到新內容
- 修改前預覽是否正確

## 5. `multi-step-selection-flow`

### 何時使用
- 使用者不是直接輸入完整指令
- 需要先選分類、再選人、再選活動
- 同一功能需要 LINE 與 web 共用流程

### 主要目標
- 把複雜輸入變成分段式選擇
- 降低格式輸入錯誤
- 讓生成文宣、跟進建議等功能可控

### 標準做法
1. 先定義 step state
2. 每一步只接受當前必要輸入
3. 明確處理 `NA`
4. 正式指令可以中斷舊流程
5. 最後一步才觸發內容生成

### 驗證重點
- 分類 -> 人名 -> 活動 是否完整走通
- 中途取消是否正確清 state
- 中途輸入別的正式指令是否能中斷

## 6. `partner-status-workflow`

### 何時使用
- 夥伴資料需要狀態管理
- 不同功能依狀態篩人
- `待跟進`、`激勵中`、`觀望中` 等需要統一

### 主要目標
- 建立明確狀態定義
- 所有會改狀態的地方使用一致清單
- web 用下拉，不讓使用者亂打

### 標準做法
1. 在資料層定義正式狀態
2. 做相容映射處理舊用語
3. API 提供狀態清單
4. web 表單一律改下拉
5. 查詢列表依狀態篩選

### 驗證重點
- 更新夥伴狀態是否受控
- 待跟進名單是否正確出現
- 激勵功能是否只抓激勵狀態

## 新功能如何判斷要用哪一個 skill

- 如果問題是「單檔太大、責任混亂」：用 `line-webhook-modularization`
- 如果問題是「先收檔案再分類」：用 `staged-archive-flow`
- 如果問題是「新增入口很多，怕漏掛」：用 `line-web-full-validation`
- 如果問題是「AI 內容要可調整」：用 `prompt-skill-management`
- 如果問題是「使用者要分段選分類/人/活動」：用 `multi-step-selection-flow`
- 如果問題是「夥伴狀態需要統一與下拉控制」：用 `partner-status-workflow`

## 建議落地方式

後續若真的要把這些 skill 做成可重複利用的 skill folder，建議每個 skill 至少有：

- `SKILL.md`
- 必要時的 `references/`
- 必要時的 `scripts/`

而這份文件就是 skill 清單總覽。
