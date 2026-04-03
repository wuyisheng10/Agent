from typing import Callable


AI_PROMPT_PREFIXES = ("查詢AI提示詞", "更新AI提示詞")
AI_SKILL_PREFIXES = ("查詢AI技能", "更新AI技能")
FOLLOWUP_SUGGESTION_PREFIXES = ("跟進建議 潛在家人", "跟進建議 夥伴")
DAILY_REPORT_PREFIXES = ("寄送每日報告",)
CALENDAR_DIRECT_COMMANDS = ("查詢今日行事曆", "查詢過往行事曆", "查詢全部行事曆")
CALENDAR_UPLOAD_COMMANDS = ("上傳行事曆圖片",)
ARCHIVE_MODE_COMMANDS = (
    "營養保健歸檔",
    "美容保養歸檔",
    "居家清潔歸檔",
    "個人護理歸檔",
    "廚具與生活用品",
    "廚具生活歸檔",
    "空氣與水處理設備",
    "空水設備歸檔",
    "體重管理與運動營養",
    "體重管理歸檔",
    "香氛與個人風格",
    "香氛風格歸檔",
    "事業工具與教育系統",
    "事業工具歸檔",
    "人物故事歸檔",
    "產品故事歸檔",
    "421故事歸檔",
    "課程文宣歸檔",
)
COURSE_PREFIXES = (
    "查詢課程會議",
    "新增課程會議",
    "修改課程會議",
    "從行事曆加入課程",
    "刪除課程會議",
    "查詢課程文宣",
    "新增課程文宣",
    "優化課程文宣",
    "邀約文宣",
    "查詢已產生的今日之後會議邀約文宣",
    "修改已產生的今日之後會議邀約文宣",
)
NUTRITION_DRI_PREFIXES = (
    "查詢營養素標準",
    "營養素運作原理",
    "列出所有營養素",
    "列出營養素",
    "更新官方營養素標準",
    "下載營養素標準",
)
NUTRITION_ASSESSMENT_PREFIXES = (
    "開始飲食評估",
    "執行飲食評估",
    "設定下一張餐別",
    "飲食評估狀態",
    "清除飲食評估",
    "設定歸檔對象",
)
TRAINING_SYSTEM_PREFIXES = (
    "新增培訓模組",
    "查詢培訓模組",
    "新增培訓課程",
    "查詢培訓課程",
    "新增培訓反思",
    "查詢培訓進度",
    "查詢培訓總表",
    "啟動七天法則",
    "七天法則回報",
    "查詢七天法則",
    "新增課後行動",
    "回報課後行動",
    "查詢課後行動",
)


def _starts_with_any(text: str, prefixes: tuple[str, ...]) -> bool:
    return any(text.startswith(prefix) for prefix in prefixes)




def _list_prospects_text(load_market_dev, keyword=None):
    rows = load_market_dev().MarketDevAgent().list_prospects(keyword)
    if not rows:
        return "找不到符合條件的潛在家人。"
    lines = [f"潛在家人名單，共 {len(rows)} 筆", ""]
    for idx, row in enumerate(rows, 1):
        name = row.get("name") or row.get("姓名") or ""
        cat = row.get("category") or row.get("分類") or row.get("status") or ""
        lines.append(f"{idx}. {name}" + (f"｜{cat}" if cat else ""))
    return "\n".join(lines)


def _partner_query_text(load_partner, cmd: str):
    result = load_partner().handle_partner_command(cmd)
    if result:
        return result
    if cmd in {"查詢所有夥伴", "查詢夥伴"}:
        return "請輸入：查詢指定夥伴 姓名"
    if cmd == "查詢待跟進夥伴":
        return "請輸入：新增跟進夥伴 姓名 | 下次跟進日期 | 備註"
    return None

def _handle_training_system(cmd: str, load_training_system):
    if _starts_with_any(cmd, TRAINING_SYSTEM_PREFIXES):
        return load_training_system().TrainingSystemAgent().handle_command(cmd)
    return None


def _format_direct_calendar(load_calendar, cmd: str) -> str:
    cal = load_calendar()
    if cmd == "查詢今日行事曆":
        return cal.format_events(cal.upcoming_events(), title="今日之後行事曆")
    if cmd == "查詢過往行事曆":
        return cal.format_events(cal.past_events(), title="過往行事曆")
    return cal.format_events(cal.events_between(), title="全部行事曆")


def _format_archive_mode_result(load_classifier, mode: str) -> str:
    alias_map = {
        "廚具與生活用品": "廚具生活歸檔",
        "空氣與水處理設備": "空水設備歸檔",
        "體重管理與運動營養": "體重管理歸檔",
        "香氛與個人風格": "香氛風格歸檔",
        "事業工具與教育系統": "事業工具歸檔",
    }
    mode = alias_map.get(mode, mode)
    result = load_classifier().ClassifierAgent().set_mode(mode)
    if mode == "行事曆":
        return f"{result}\n\n請直接上傳行事曆圖片。"
    return result


def handle_line_command(
    msg: str,
    reply_token: str,
    push_target: str,
    sessions: dict,
    reply_message: Callable[[str, str], None],
    push_message: Callable[[str, str], None],
    load_calendar,
    load_partner,
    load_classifier,
    load_market_dev,
    load_course_invite,
    load_daily_report,
    load_nutrition_dri,
    load_nutrition_assessment,
    load_ai_prompt_manager,
    load_ai_skill_manager,
    load_followup_suggestion,
    load_training_agent,
    load_training_system,
    load_followup,
    load_motivation,
):
    msg = (msg or "").strip()

    try:
        if msg == "查詢目前歸類模式":
            reply_message(reply_token, load_classifier().ClassifierAgent().handle_mode_command("歸類模式"))
            return True

        if msg == "顯示所有指令":
            reply_message(reply_token, "請輸入：5168")
            return True

        if msg == "跟進報告":
            reply_message(reply_token, load_followup().FollowupAgent().generate_report_text())
            return True

        if msg in {"查詢今日行事曆", "查詢過往行事曆", "查詢全部行事曆"}:
            if msg == "查詢今日行事曆":
                reply_message(reply_token, _format_direct_calendar(load_calendar, "查詢今日行事曆"))
            elif msg == "查詢過往行事曆":
                reply_message(reply_token, _format_direct_calendar(load_calendar, "查詢過往行事曆"))
            else:
                reply_message(reply_token, _format_direct_calendar(load_calendar, "查詢全部行事曆"))
            return True

        if msg == "上傳行事曆圖片":
            reply_message(reply_token, _format_archive_mode_result(load_classifier, "行事曆"))
            return True

        if msg in {"查詢所有夥伴", "查詢夥伴", "查詢待跟進夥伴"}:
            reply_message(reply_token, _partner_query_text(load_partner, msg))
            return True

        if msg in {"查詢所有歸檔", "查詢歸檔"}:
            reply_message(reply_token, load_classifier().ClassifierAgent().query_archive(None))
            return True

        if msg.startswith("查詢指定人員歸檔 ") or msg.startswith("查詢歸檔 "):
            person = msg.split(" ", 1)[1].strip() or None
            reply_message(reply_token, load_classifier().ClassifierAgent().query_archive(person))
            return True

        if msg in {
            "營養保健歸檔",
            "美容保養歸檔",
            "居家清潔歸檔",
            "個人護理歸檔",
            "廚具與生活用品",
            "廚具生活歸檔",
            "空氣與水處理設備",
            "空水設備歸檔",
            "體重管理與運動營養",
            "體重管理歸檔",
            "香氛與個人風格",
            "香氛風格歸檔",
            "事業工具與教育系統",
            "事業工具歸檔",
            "人物故事歸檔",
            "產品故事歸檔",
            "421故事歸檔",
            "課程文宣歸檔",
        }:
            reply_message(reply_token, _format_archive_mode_result(load_classifier, msg))
            return True

        if msg == "查詢潛在家人":
            reply_message(reply_token, _list_prospects_text(load_market_dev))
            return True
        if _starts_with_any(msg, AI_PROMPT_PREFIXES):
            result = load_ai_prompt_manager().handle_command(msg)
            if result:
                reply_message(reply_token, result)
                return True

        if _starts_with_any(msg, AI_SKILL_PREFIXES):
            result = load_ai_skill_manager().handle_command(msg)
            if result:
                reply_message(reply_token, result)
                return True

        if _starts_with_any(msg, FOLLOWUP_SUGGESTION_PREFIXES):
            result = load_followup_suggestion().FollowupSuggestionAgent().handle_command(msg)
            if result:
                reply_message(reply_token, result)
                return True

        if _starts_with_any(msg, DAILY_REPORT_PREFIXES):
            reply_message(reply_token, "正在寄送每日報告，完成後會再推送結果。")
            push_message(push_target, load_daily_report().DailyReportAgent().run())
            return True

        if msg in CALENDAR_DIRECT_COMMANDS:
            reply_message(reply_token, _format_direct_calendar(load_calendar, msg))
            return True

        if msg in CALENDAR_UPLOAD_COMMANDS:
            reply_message(reply_token, _format_archive_mode_result(load_classifier, "行事曆"))
            return True

        if msg in ARCHIVE_MODE_COMMANDS:
            reply_message(reply_token, _format_archive_mode_result(load_classifier, msg))
            return True

        cal_result = load_calendar().handle_calendar_command(msg)
        if cal_result:
            reply_message(reply_token, cal_result)
            return True

        partner_result = _partner_query_text(load_partner, msg)
        if partner_result:
            reply_message(reply_token, partner_result)
            return True

        if msg.startswith("查詢所有歸檔") or msg == "查詢歸檔":
            reply_message(reply_token, load_classifier().ClassifierAgent().query_archive(None))
            return True

        if msg.startswith("查詢歸檔 "):
            person = msg.replace("查詢歸檔", "", 1).strip() or None
            reply_message(reply_token, load_classifier().ClassifierAgent().query_archive(person))
            return True

        if msg.startswith("查詢指定人員歸檔"):
            person = msg.replace("查詢指定人員歸檔", "", 1).strip() or None
            reply_message(reply_token, load_classifier().ClassifierAgent().query_archive(person))
            return True

        if msg.startswith("新增潛在家人"):
            reply_message(reply_token, "正在新增潛在家人，完成後會再推送結果。")
            push_message(push_target, load_market_dev().MarketDevAgent().handle_add_prospect(msg))
            return True

        if msg.startswith("查詢潛在家人近況") or msg.startswith("查詢潛在家人") or msg == "潛在家人總表":
            keyword = msg
            keyword = keyword.replace("查詢潛在家人近況", "", 1)
            keyword = keyword.replace("查詢潛在家人", "", 1).strip() or None
            rows = load_market_dev().MarketDevAgent().list_prospects(keyword)
            if not rows:
                reply_message(reply_token, "找不到符合條件的潛在家人。")
            else:
                lines = [f"潛在家人名單，共 {len(rows)} 筆", ""]
                for idx, row in enumerate(rows, 1):
                    name = row.get("name") or row.get("姓名") or ""
                    cat = row.get("category") or row.get("分類") or row.get("status") or ""
                    lines.append(f"{idx}. {name}" + (f"｜{cat}" if cat else ""))
                reply_message(reply_token, "\n".join(lines))
            return True

        if msg.startswith("修改潛在家人資訊") or msg.startswith("更新潛在家人"):
            content = msg
            content = content.replace("修改潛在家人資訊", "", 1)
            content = content.replace("更新潛在家人", "", 1).strip()
            parts = [p.strip() for p in content.split("|")]
            name = parts[0] if parts else ""
            fields = {}
            for part in parts[1:]:
                if ":" in part:
                    key, value = part.split(":", 1)
                    fields[key.strip()] = value.strip()
            reply_message(reply_token, load_market_dev().MarketDevAgent().update_prospect_fields(name, fields))
            return True

        if _starts_with_any(msg, COURSE_PREFIXES):
            course = load_course_invite()
            if msg.startswith("邀約文宣"):
                reply_message(reply_token, "正在產生邀約文宣，完成後會再推送結果。")
                push_message(push_target, course.CourseInviteAgent().handle_command(msg) or "邀約文宣已完成。")
            else:
                reply_message(reply_token, course.CourseInviteAgent().handle_command(msg) or "課程邀約指令已處理。")
            return True

        if _starts_with_any(msg, NUTRITION_DRI_PREFIXES):
            reply_message(reply_token, load_nutrition_dri().NutritionDRIAgent().handle_command(msg))
            return True

        if _starts_with_any(msg, NUTRITION_ASSESSMENT_PREFIXES):
            assessment = load_nutrition_assessment()
            if msg.startswith("執行飲食評估"):
                reply_message(reply_token, "正在分析飲食內容並產生報告，完成後會再推送結果。")
                result = assessment.handle_command(msg, sessions, push_target)
                if result:
                    push_message(push_target, result)
            else:
                result = assessment.handle_command(msg, sessions, push_target)
                if result:
                    reply_message(reply_token, result)
            return True

        training_system_result = _handle_training_system(msg, load_training_system)
        if training_system_result:
            reply_message(reply_token, training_system_result)
            return True

        if msg.startswith("查詢培訓進度 "):
            reply_message(reply_token, load_training_agent().TrainingAgent().handle_query(msg))
            return True

        if msg == "跟進報告":
            reply_message(reply_token, load_followup().FollowupAgent().generate_report_text())
            return True

        if msg.startswith("激勵夥伴") or msg.startswith("里程碑記錄") or msg.startswith("里程碑 "):
            reply_message(reply_token, load_motivation().MotivationAgent().handle_realtime(msg))
            return True

        return False
    except Exception as exc:
        reply_message(reply_token, f"⚠️ 指令處理失敗：{exc}")
        return True


def handle_web_command(
    cmd: str,
    sessions: dict,
    load_calendar,
    load_partner,
    load_classifier,
    load_market_dev,
    load_course_invite,
    load_daily_report,
    load_nutrition_dri,
    load_nutrition_assessment,
    load_ai_prompt_manager,
    load_ai_skill_manager,
    load_followup_suggestion,
    load_training_agent,
    load_training_system,
    load_followup,
    load_motivation,
):
    cmd = (cmd or "").strip()

    if cmd == "查詢目前歸類模式":
        return load_classifier().ClassifierAgent().handle_mode_command("歸類模式")

    if cmd == "顯示所有指令":
        return "請輸入：5168"

    if cmd == "????":
        return load_followup().FollowupAgent().generate_report_text()

    if cmd in {"???????", "???????", "???????"}:
        if cmd == "???????":
            return _format_direct_calendar(load_calendar, "???????????")
        if cmd == "???????":
            return _format_direct_calendar(load_calendar, "???????????")
        return _format_direct_calendar(load_calendar, "???????????")

    if cmd == "???????":
        return _format_archive_mode_result(load_classifier, "?????")

    if cmd in {"??????", "????", "???????"}:
        return _partner_query_text(load_partner, cmd)

    if cmd in {"??????", "????"}:
        return load_classifier().ClassifierAgent().query_archive(None)

    if cmd.startswith("???????? ") or cmd.startswith("???? "):
        person = cmd.split(" ", 1)[1].strip() or None
        return load_classifier().ClassifierAgent().query_archive(person)

    if cmd in {"??????", "??????", "??????", "??????", "???????", "????????", "?????????", "???????", "?????????", "??????", "??????", "421????", "??????"}:
        return _format_archive_mode_result(load_classifier, cmd)

    if cmd == "??????":
        return _list_prospects_text(load_market_dev)

    if _starts_with_any(cmd, AI_PROMPT_PREFIXES):
        return load_ai_prompt_manager().handle_command(cmd)

    if _starts_with_any(cmd, AI_SKILL_PREFIXES):
        return load_ai_skill_manager().handle_command(cmd)

    if _starts_with_any(cmd, FOLLOWUP_SUGGESTION_PREFIXES):
        return load_followup_suggestion().FollowupSuggestionAgent().handle_command(cmd)

    if _starts_with_any(cmd, DAILY_REPORT_PREFIXES):
        return load_daily_report().DailyReportAgent().run()

    if cmd in CALENDAR_DIRECT_COMMANDS:
        return _format_direct_calendar(load_calendar, cmd)

    if cmd in CALENDAR_UPLOAD_COMMANDS:
        return _format_archive_mode_result(load_classifier, "行事曆")

    if cmd in ARCHIVE_MODE_COMMANDS:
        return _format_archive_mode_result(load_classifier, cmd)

    cal_result = load_calendar().handle_calendar_command(cmd)
    if cal_result:
        return cal_result

    partner_result = _partner_query_text(load_partner, cmd)
    if partner_result:
        return partner_result

    if cmd.startswith("查詢所有歸檔") or cmd == "查詢歸檔":
        return load_classifier().ClassifierAgent().query_archive(None)

    if cmd.startswith("查詢歸檔 "):
        person = cmd.replace("查詢歸檔", "", 1).strip() or None
        return load_classifier().ClassifierAgent().query_archive(person)

    if cmd.startswith("查詢指定人員歸檔"):
        person = cmd.replace("查詢指定人員歸檔", "", 1).strip() or None
        return load_classifier().ClassifierAgent().query_archive(person)

    if cmd.startswith("新增潛在家人"):
        return load_market_dev().MarketDevAgent().handle_add_prospect(cmd)

    if cmd.startswith("查詢潛在家人近況") or cmd.startswith("查詢潛在家人") or cmd == "潛在家人總表":
        keyword = cmd
        keyword = keyword.replace("查詢潛在家人近況", "", 1)
        keyword = keyword.replace("查詢潛在家人", "", 1).strip() or None
        rows = load_market_dev().MarketDevAgent().list_prospects(keyword)
        if not rows:
            return "找不到符合條件的潛在家人。"
        lines = [f"潛在家人名單，共 {len(rows)} 筆", ""]
        for idx, row in enumerate(rows, 1):
            name = row.get("name") or row.get("姓名") or ""
            cat = row.get("category") or row.get("分類") or row.get("status") or ""
            lines.append(f"{idx}. {name}" + (f"｜{cat}" if cat else ""))
        return "\n".join(lines)

    if cmd.startswith("修改潛在家人資訊") or cmd.startswith("更新潛在家人"):
        content = cmd
        content = content.replace("修改潛在家人資訊", "", 1)
        content = content.replace("更新潛在家人", "", 1).strip()
        parts = [p.strip() for p in content.split("|")]
        name = parts[0] if parts else ""
        fields = {}
        for part in parts[1:]:
            if ":" in part:
                key, value = part.split(":", 1)
                fields[key.strip()] = value.strip()
        return load_market_dev().MarketDevAgent().update_prospect_fields(name, fields)

    if _starts_with_any(cmd, COURSE_PREFIXES):
        return load_course_invite().CourseInviteAgent().handle_command(cmd)

    if _starts_with_any(cmd, NUTRITION_DRI_PREFIXES):
        return load_nutrition_dri().NutritionDRIAgent().handle_command(cmd)

    if _starts_with_any(cmd, NUTRITION_ASSESSMENT_PREFIXES):
        return load_nutrition_assessment().handle_command(cmd, sessions, "web", push_fn=None, reply_fn=None)

    training_system_result = _handle_training_system(cmd, load_training_system)
    if training_system_result:
        return training_system_result

    if cmd.startswith("查詢培訓進度 "):
        return load_training_agent().TrainingAgent().handle_query(cmd)

    if cmd == "跟進報告":
        return load_followup().FollowupAgent().generate_report_text()

    if cmd.startswith("激勵夥伴") or cmd.startswith("里程碑記錄") or cmd.startswith("里程碑 "):
        return load_motivation().MotivationAgent().handle_realtime(cmd)

    return None
