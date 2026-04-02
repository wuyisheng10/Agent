# 06_line_webhook.py 重構計畫

## 目標

- 將 `agents/06_line_webhook.py` 從單一巨型檔案拆成可維護模組
- 保持現有 LINE、Web、API 功能不回歸
- 優先抽出低耦合區塊，再拆高風險流程

## 第一批已完成

- `agents/webhook_common.py`
  - 共用路徑與環境變數
  - agent loader
- `agents/webhook_text.py`
  - `TRIGGER_WORDS`
  - `HELP_TEXT`
  - `EXEC_MENU_ITEMS`
  - `EXEC_MENU_TEXT`
- `agents/06_line_webhook.py`
  - 已改成引用上述模組
  - 目前仍保留舊常數/loader，作為過渡期 fallback

## 第二批建議拆分

### 1. webhook_state.py

負責：

- `_exec_menu_active`
- `_nutrition_sessions`
- `_awaiting_person_for_mode`
- `_awaiting_exec_input`
- `_awaiting_prospect_selection`
- `_awaiting_prospect_file`
- `_awaiting_invite_selection`
- `_awaiting_partner_invite_category`
- `_awaiting_partner_invite_person`
- `_awaiting_partner_invite_meeting`
- `_awaiting_invite_manage_select`
- `_awaiting_invite_manage_action`
- `_awaiting_invite_manage_edit`
- `_web_invite_combos`
- `_web_partner_invite_state`
- `_web_invite_manage_state`

原因：

- 目前 state 散在主檔，難以追蹤
- 後續可再包成 class 或 dataclass

### 2. webhook_line_handlers.py

負責：

- `extract_trigger`
- `log`
- `verify_signature`
- `analyze_intent`
- `reply_message`
- `push_message`
- `schedule_pending_menu`
- `_download_line_content`
- `handle_image_message`
- `handle_audio_message`
- `handle_video_message`
- `handle_file_message`

原因：

- 這一段主要是 LINE I/O 與素材接收
- 可和 Flask route 分離

### 3. webhook_command_router.py

負責：

- `handle_training_command`
- `process_web_command`
- 夥伴、課程、營養、每日報告等指令分流

原因：

- 目前指令分流過長
- 可進一步拆成多個 `dispatch_*` 函式

### 4. webhook_web_views.py

負責：

- `_render_archive_html`
- `_render_dashboard_html`
- `_render_dashboard_html_v2`

原因：

- HTML/JS 內嵌字串很大
- 適合拆到獨立模組，之後再考慮改模板檔

### 5. webhook_api_routes.py

負責：

- `/health`
- `/summary/*`
- `/archive/*`
- `/api/command`
- `/api/upload`
- `/api/pending*`
- `/api/prospect*`
- `/api/course-invite*`
- `/api/send-daily-report`

原因：

- Flask route 可改成 `register_routes(app, deps)` 形式
- 主檔只保留 app 建立與啟動

## 目標最終形態

`agents/06_line_webhook.py` 只保留：

- app 建立
- 模組注入
- route registration
- `if __name__ == "__main__": ...`

預期主檔縮到約 `200-400` 行。

## 推薦拆分順序

1. `webhook_state.py`
2. `webhook_line_handlers.py`
3. `webhook_command_router.py`
4. `webhook_web_views.py`
5. `webhook_api_routes.py`
6. 最後刪除 `06_line_webhook.py` 過渡期舊碼
