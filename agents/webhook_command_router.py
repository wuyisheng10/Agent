from typing import Callable


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
    load_training_agent,
    load_followup,
    load_motivation,
):
    msg = (msg or "").strip()

    if msg == "寄送每日報告":
        try:
            reply_message(reply_token, "⏳ 正在產生每日報告並寄送，請稍候...")
            dr = load_daily_report()
            result = dr.DailyReportAgent().run()
            push_message(push_target, result)
        except Exception as exc:
            reply_message(reply_token, f"✗ 每日報告失敗：{exc}")
        return True

    try:
        cal = load_calendar()
        result = cal.handle_calendar_command(msg)
        if result:
            reply_message(reply_token, result)
            return True
    except Exception as exc:
        reply_message(reply_token, f"✗ 行事曆指令失敗：{exc}")
        return True

    try:
        partner = load_partner()
        result = partner.handle_partner_command(msg)
        if result:
            reply_message(reply_token, result)
            return True
    except Exception as exc:
        reply_message(reply_token, f"✗ 夥伴指令失敗：{exc}")
        return True

    if msg.startswith("查詢歸檔"):
        try:
            clf_mod = load_classifier()
            person = msg.replace("查詢歸檔", "", 1).strip() or None
            result = clf_mod.ClassifierAgent().query_archive(person)
            reply_message(reply_token, result)
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 查詢歸檔失敗：{exc}")
            return True

    if msg.startswith("新增潛在家人"):
        try:
            reply_message(reply_token, "⏳ 正在新增潛在家人並進行 AI 評分，請稍候...")
            market = load_market_dev()
            result = market.MarketDevAgent().handle_add_prospect(msg)
            push_message(push_target, result)
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 新增潛在家人失敗：{exc}")
            return True

    if msg.startswith("查詢潛在家人"):
        try:
            keyword = msg.replace("查詢潛在家人", "", 1).strip() or None
            market = load_market_dev()
            rows = market.MarketDevAgent().list_prospects(keyword)
            if not rows:
                reply_message(reply_token, "⚠️ 目前沒有潛在家人資料。")
                return True
            lines = [f"📋 潛在家人清單（共 {len(rows)} 位）", ""]
            for i, row in enumerate(rows, 1):
                lines.append(f"{i}. {row.get('姓名','')}｜{row.get('類型','')}")
            reply_message(reply_token, "\n".join(lines))
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 查詢潛在家人失敗：{exc}")
            return True

    course_prefixes = (
        "新增課程會議", "查詢課程會議", "刪除課程會議", "修改課程會議", "從行事曆加入課程",
        "新增課程文宣", "查詢課程文宣", "優化課程文宣",
        "查詢已產生的今日之後會議邀約文宣", "修改已產生的今日之後會議邀約文宣",
        "邀約文宣 潛在家人", "邀約文宣 跟進夥伴",
        "課程會議", "課程文宣", "課程",
    )
    if any(msg.startswith(prefix) for prefix in course_prefixes):
        try:
            course = load_course_invite()
            if msg.startswith("優化課程文宣") or msg.startswith("邀約文宣"):
                reply_message(reply_token, "⏳ 正在透過 AI 產生課程文宣，請稍候...")
                result = course.CourseInviteAgent().handle_command(msg)
                push_message(push_target, result if result else "⚠️ 課程指令無結果")
            else:
                result = course.CourseInviteAgent().handle_command(msg)
                reply_message(reply_token, result if result else "⚠️ 課程指令無結果")
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 課程邀約失敗：{exc}")
            return True

    dri_prefixes = ("查詢營養素標準", "營養素運作原理", "列出營養素", "所有營養素", "下載營養素標準", "更新營養素標準")
    if any(msg.startswith(prefix) for prefix in dri_prefixes) or msg in dri_prefixes:
        try:
            dri_mod = load_nutrition_dri()
            result = dri_mod.NutritionDRIAgent().handle_command(msg)
            if result:
                reply_message(reply_token, result)
                return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 營養素查詢失敗：{exc}")
            return True

    assess_prefixes = ("開始飲食評估", "設定餐別", "設定評估對象", "評估飲食", "清除飲食評估", "取消飲食評估", "飲食評估狀態")
    if any(msg.startswith(prefix) for prefix in assess_prefixes):
        try:
            na_mod = load_nutrition_assessment()
            if msg.startswith("評估飲食"):
                reply_message(reply_token, "⏳ 正在分析餐點照片並生成報告，請稍候（約30-60秒）...")
                try:
                    result = na_mod.handle_command(msg, sessions, push_target)
                    if result:
                        push_message(push_target, result)
                except Exception as exc:
                    push_message(push_target, f"✗ 飲食評估失敗：{exc}")
            else:
                result = na_mod.handle_command(msg, sessions, push_target)
                if result:
                    reply_message(reply_token, result)
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 飲食評估指令失敗：{exc}")
            return True

    if msg.startswith("培訓"):
        try:
            training = load_training_agent()
            result = training.TrainingAgent().handle_query(msg)
            reply_message(reply_token, result)
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 培訓查詢失敗：{exc}")
            return True

    if msg == "跟進報告":
        try:
            reply_message(reply_token, "⏳ 正在生成跟進報告，請稍候...")
            followup = load_followup()
            result = followup.FollowupAgent().generate_report_text()
            push_message(push_target, result)
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 跟進報告失敗：{exc}")
            return True

    if msg.startswith("激勵") or msg.startswith("里程碑"):
        try:
            reply_message(reply_token, "⏳ 正在生成激勵訊息，請稍候...")
            motivation = load_motivation()
            result = motivation.MotivationAgent().handle_realtime(msg)
            push_message(push_target, result)
            return True
        except Exception as exc:
            reply_message(reply_token, f"✗ 激勵訊息失敗：{exc}")
            return True

    return False


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
    load_training_agent,
    load_followup,
    load_motivation,
):
    cmd = (cmd or "").strip()

    if cmd == "寄送每日報告":
        dr = load_daily_report()
        return dr.DailyReportAgent().run()

    cal = load_calendar()
    result = cal.handle_calendar_command(cmd)
    if result:
        return result

    partner = load_partner()
    result = partner.handle_partner_command(cmd)
    if result:
        return result

    if cmd.startswith("查詢歸檔"):
        clf_mod = load_classifier()
        person = cmd.replace("查詢歸檔", "", 1).strip() or None
        return clf_mod.ClassifierAgent().query_archive(person)

    if cmd.startswith("新增潛在家人") or cmd.startswith("查詢潛在家人"):
        market = load_market_dev()
        if cmd.startswith("新增潛在家人"):
            return market.MarketDevAgent().handle_add_prospect(cmd)
        keyword = cmd.replace("查詢潛在家人", "", 1).strip() or None
        rows = market.MarketDevAgent().list_prospects(keyword)
        if not rows:
            return "⚠️ 目前沒有潛在家人資料。"
        lines = [f"📋 潛在家人清單（共 {len(rows)} 位）", ""]
        for i, row in enumerate(rows, 1):
            lines.append(f"{i}. {row.get('姓名','')}｜{row.get('類型','')}")
        return "\n".join(lines)

    course_prefixes = (
        "新增課程會議", "查詢課程會議", "刪除課程會議", "修改課程會議", "從行事曆加入課程",
        "新增課程文宣", "查詢課程文宣", "優化課程文宣",
        "查詢已產生的今日之後會議邀約文宣", "修改已產生的今日之後會議邀約文宣",
        "邀約文宣 潛在家人", "邀約文宣 跟進夥伴",
        "課程會議", "課程文宣", "課程",
    )
    if any(cmd.startswith(prefix) for prefix in course_prefixes):
        course = load_course_invite()
        result = course.CourseInviteAgent().handle_command(cmd)
        return result if result else "⚠️ 課程指令無結果"

    dri_prefixes = ("查詢營養素標準", "營養素運作原理", "列出營養素", "所有營養素", "下載營養素標準", "更新營養素標準")
    if any(cmd.startswith(prefix) for prefix in dri_prefixes) or cmd in dri_prefixes:
        dri_mod = load_nutrition_dri()
        result = dri_mod.NutritionDRIAgent().handle_command(cmd)
        return result if result else "⚠️ 無結果"

    assess_prefixes = ("開始飲食評估", "設定餐別", "設定評估對象", "評估飲食", "清除飲食評估", "取消飲食評估", "飲食評估狀態")
    if any(cmd.startswith(prefix) for prefix in assess_prefixes):
        na_mod = load_nutrition_assessment()
        result = na_mod.handle_command(cmd, sessions, "web")
        return result if result else "⚠️ 無結果"

    if cmd.startswith("培訓"):
        training = load_training_agent()
        return training.TrainingAgent().handle_query(cmd)

    if cmd.startswith("跟進報告"):
        followup = load_followup()
        return followup.FollowupAgent().generate_report_text()

    if cmd.startswith("激勵") or cmd.startswith("里程碑"):
        motivation = load_motivation()
        return motivation.MotivationAgent().handle_realtime(cmd)

    return None
