# 群雁培訓系統資料模型

## 儲存位置

```text
output/
  training_system/
    modules.json
    sessions.json
    reflections.json
    progress.json
    seven_day.json
    actions.json
```

## modules.json
培訓模組主檔。

欄位：
- `id`
- `title`
- `category`
- `goal`
- `summary`
- `keywords`
- `attachments`
- `created_at`
- `updated_at`

## sessions.json
培訓課程主檔。

欄位：
- `id`
- `module_id`
- `title`
- `speaker`
- `date`
- `time`
- `location`
- `audience`
- `description`
- `materials`
- `status`
- `participants`
- `created_at`
- `updated_at`

## reflections.json
課後反思資料。

欄位：
- `id`
- `session_id`
- `module_id`
- `person_name`
- `person_type`
- `insight`
- `learned`
- `action`
- `goal`
- `coach_feedback`
- `created_at`
- `updated_at`

## progress.json
個人培訓進度聚合檔。

欄位：
- `person_name`
- `person_type`
- `completed_modules`
- `completed_sessions`
- `last_session_id`
- `last_reflection_id`
- `next_recommended_modules`
- `action_status`
- `updated_at`

## seven_day.json
新人七天法則追蹤。

欄位：
- `id`
- `person_name`
- `start_date`
- `coach_note`
- `days[]`
- `status`
- `created_at`
- `updated_at`

每個 `days[]`：
- `day`
- `tasks`
- `done`
- `done_text`
- `note`
- `updated_at`

## actions.json
課後行動追蹤。

欄位：
- `id`
- `person_name`
- `session_id`
- `session_title`
- `content`
- `due_date`
- `status`
- `note`
- `created_at`
- `updated_at`

## 狀態列舉

### 模組類型
- 領導人特質
- 新人守則
- 帶線系統
- 市場實戰
- 畫畫培訓
- 產品培訓
- 事業培訓

### 課後行動狀態
- 待執行
- 進行中
- 已完成
- 延後
- 需協助

### 七天法則狀態
- active
- completed
