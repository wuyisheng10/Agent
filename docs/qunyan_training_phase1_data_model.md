# Qunyan Training Phase 1 Data Model

這份文件定義第一期培訓系統建議的資料結構，對應前一份規劃：

- `docs/qunyan_training_system_plan.md`

第一期目標只聚焦在：

- 培訓模組中心
- 培訓課程/場次
- 課後 `悟到 / 學到 / 做到 / 目標`
- 個人培訓進度
- 團隊培訓總表

這一版優先採用目前系統已經習慣的 JSON/檔案式儲存方式，方便先上線，不先強推資料庫。

## 一、建議資料夾

```text
output/
  training_system/
    modules.json
    sessions.json
    reflections.json
    progress.json
```

## 二、資料物件

## 1. Training Module

代表一個培訓模組，例如：

- 四個勇於
- 七天法則
- 2689 帶線系統
- 市場實戰案例

### 欄位

```json
{
  "id": "TM-FOUR-COURAGE",
  "title": "四個勇於",
  "category": "領導人特質",
  "goal": "建立領導人思維與承擔觀念",
  "summary": "勇於學習、勇於認錯、勇於改變、勇於承擔",
  "keywords": ["學習", "認錯", "改變", "承擔"],
  "attachments": [
    {
      "type": "pptx",
      "path": "output/classified/一般歸檔/20260330/files/悟到學到做到目標 群雁培訓教材.pptx"
    }
  ],
  "created_at": "2026-04-02T22:00:00+08:00",
  "updated_at": "2026-04-02T22:00:00+08:00"
}
```

### 說明

- `id`: 模組唯一識別碼
- `category`: 模組分類
- `goal`: 學習目標
- `summary`: 核心摘要
- `keywords`: 用來搜尋或推薦
- `attachments`: 可掛教材、逐字稿、講義

## 2. Training Session

代表一次實際開課或培訓場次。

### 欄位

```json
{
  "id": "TS-20260405-001",
  "module_id": "TM-FOUR-COURAGE",
  "title": "領導人特質｜四個勇於",
  "speaker": "鐘老師",
  "date": "2026-04-05",
  "time": "19:30",
  "location": "台南教室",
  "audience": "夥伴",
  "description": "建立領導人思維與內在觀念",
  "materials": [
    "output/classified/一般歸檔/20260330/files/悟到學到做到目標 群雁培訓教材.pptx"
  ],
  "status": "scheduled",
  "participants": [],
  "created_at": "2026-04-02T22:00:00+08:00",
  "updated_at": "2026-04-02T22:00:00+08:00"
}
```

### `status` 建議值

- `scheduled`
- `completed`
- `cancelled`

## 3. Training Reflection

代表某個人對某一場培訓的課後反思。

### 欄位

```json
{
  "id": "TR-20260405-001",
  "session_id": "TS-20260405-001",
  "module_id": "TM-FOUR-COURAGE",
  "person_name": "王小美",
  "person_type": "partner",
  "insight": "真正的領導人不是技巧強，而是先願意承認自己還沒改變。",
  "learned": "四個勇於的順序不能亂，學習、認錯、改變、承擔是連動的。",
  "action": "這週主動每天做一次市場回報，並重新檢查自己的態度。",
  "goal": "本月內建立穩定回報習慣，讓自己能承擔更多帶線責任。",
  "coach_feedback": "",
  "created_at": "2026-04-05T21:30:00+08:00",
  "updated_at": "2026-04-05T21:30:00+08:00"
}
```

### 說明

- `person_type`: 可先分 `partner` / `prospect`
- `coach_feedback`: 上線或講師後續回饋

## 4. Training Progress

代表某位學員在培訓模組上的累積進度。

### 欄位

```json
{
  "person_name": "王小美",
  "person_type": "partner",
  "completed_modules": [
    "TM-FOUR-COURAGE"
  ],
  "completed_sessions": [
    "TS-20260405-001"
  ],
  "last_session_id": "TS-20260405-001",
  "last_reflection_id": "TR-20260405-001",
  "next_recommended_modules": [
    "TM-SEVEN-DAY-RULE",
    "TM-2689"
  ],
  "action_status": "active",
  "updated_at": "2026-04-05T21:40:00+08:00"
}
```

### `action_status` 建議值

- `active`
- `paused`
- `followup_needed`

## 三、實際檔案結構

## modules.json

```json
{
  "modules": [
    {
      "...": "Training Module"
    }
  ]
}
```

## sessions.json

```json
{
  "sessions": [
    {
      "...": "Training Session"
    }
  ]
}
```

## reflections.json

```json
{
  "reflections": [
    {
      "...": "Training Reflection"
    }
  ]
}
```

## progress.json

```json
{
  "progress": [
    {
      "...": "Training Progress"
    }
  ]
}
```

## 四、第一期必要索引規則

因為目前走 JSON 檔案模式，建議讀寫時固定做這些索引：

- `module_id -> module`
- `session_id -> session`
- `person_name -> reflections[]`
- `person_name -> progress`

## 五、第一期必要功能與資料對應

## 1. 新增培訓模組

寫入：

- `modules.json`

## 2. 新增培訓課程/場次

寫入：

- `sessions.json`

## 3. 填寫悟到學到做到目標

寫入：

- `reflections.json`

同步更新：

- `progress.json`

## 4. 查詢個人培訓進度

讀取：

- `progress.json`
- `reflections.json`
- `sessions.json`

## 5. 團隊培訓總表

讀取：

- `progress.json`
- `sessions.json`
- `reflections.json`

## 六、和現有系統的對接建議

### 1. 與夥伴系統對接

沿用既有夥伴姓名與類型：

- 夥伴：`partner`
- 潛在家人：`prospect`

### 2. 與行事曆系統對接

培訓場次可同步建立成行事曆活動。

### 3. 與歸檔系統對接

教材、講義、課後錄音、逐字稿可歸到：

- `一般歸檔`
- `培訓資料`
- `整理會議心得`

### 4. 與 AI prompt / skill 系統對接

課後摘要與反思建議可交給既有 prompt / skill 管理。

## 七、第二期可擴充欄位

雖然第一期先不做，但欄位設計要預留：

- `attendance_status`
- `homework_required`
- `homework_submission_paths`
- `coach_score`
- `leadership_score`
- `seven_day_rule_status`
- `tracking_2689_status`

## 八、實作建議

第一期先新增一個獨立 agent，例如：

- `agents/23_training_system_agent.py`

先做這四件事：

1. 新增模組
2. 新增場次
3. 填寫課後反思
4. 查詢個人進度

這樣最容易和現有系統整合，也最不會一開始就做太重。
