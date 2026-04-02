def process_line_events(
    *,
    request,
    abort,
    verify_signature,
    log,
    load_classifier,
    handle_image_message,
    handle_audio_message,
    handle_video_message,
    handle_file_message,
    handle_training_command,
    reply_message,
    execute_menu_text,
    execute_menu_items,
    exec_menu_active,
    awaiting_person_for_mode,
    awaiting_exec_input,
    awaiting_prospect_selection,
    awaiting_prospect_file,
    awaiting_invite_selection,
    awaiting_partner_invite_category,
    awaiting_partner_invite_person,
    awaiting_partner_invite_meeting,
    awaiting_invite_manage_select,
    awaiting_invite_manage_action,
    awaiting_invite_manage_edit,
    awaiting_promo_optimize_apply,
    awaiting_partner_voice_add,
    looks_like_explicit_command,
    normalize_partner_category_choice,
    partners_by_category,
    format_partner_choice_menu,
    format_meeting_choice_menu,
    format_invite_manage_list,
    format_invite_manage_actions,
    format_invite_view,
    format_invite_edit_confirm,
    load_course_invite,
    load_classifier_module,
    load_market_dev,
    format_prospect_detail,
):
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()
    if not verify_signature(body, signature):
        log("❌ 簽章驗證失敗")
        abort(400)

    data = request.json
    events = data.get("events", [])
    try:
        clf_mod = load_classifier()
        clf_agent = clf_mod.ClassifierAgent()
        mode_info = clf_agent.get_mode()
    except Exception as e:
        log(f"  ⚠️ ClassifierAgent 載入失敗：{e}")
        clf_agent = None
        mode_info = {"mode": "auto", "set_at": ""}

    for event in events:
        if event.get("type") != "message":
            continue

        msg_type = event.get("message", {}).get("type", "")
        reply_token = event.get("replyToken", "")
        user_id = event.get("source", {}).get("userId", "")
        group_id = event.get("source", {}).get("groupId", "")
        push_target = group_id or user_id

        if msg_type == "image":
            log(f"🖼️ 收到圖片（模式：{mode_info['mode']}）")
            handle_image_message(event, mode_info, clf_agent)
            continue
        if msg_type == "audio":
            log(f"🎤 收到音檔（模式：{mode_info['mode']}）")
            if clf_agent:
                handle_audio_message(event, mode_info, clf_agent)
            else:
                reply_message(reply_token, "⚠️ 音檔功能暫時無法使用")
            continue
        if msg_type == "video":
            log(f"🎬 收到影片（模式：{mode_info['mode']}）")
            if clf_agent:
                handle_video_message(event, mode_info, clf_agent)
            else:
                reply_message(reply_token, "⚠️ 影片功能暫時無法使用")
            continue
        if msg_type == "file":
            fname = event.get("message", {}).get("fileName", "")
            log(f"📄 收到檔案：{fname}（模式：{mode_info['mode']}）")
            if clf_agent:
                handle_file_message(event, mode_info, clf_agent)
            else:
                reply_message(reply_token, "⚠️ 檔案功能暫時無法使用")
            continue
        if msg_type != "text":
            continue

        user_msg = event["message"]["text"]
        log(f"📨 收到訊息 from {user_id[:8]}：{user_msg[:50]}")
        scope = group_id or user_id

        if clf_agent:
            pending = clf_agent.get_pending(scope)
            folder_result = clf_agent.submit_pending_folder_name(scope, user_msg.strip())
            if folder_result:
                reply_message(reply_token, folder_result)
                continue
            if pending and user_msg.strip().isdigit():
                choice = int(user_msg.strip())
                log(f"  待歸檔選擇：{choice}")
                reply_message(reply_token, clf_agent.execute_pending_option(scope, choice))
                continue
            if pending and user_msg.strip() in {"待歸檔", "查詢待歸檔"}:
                reply_message(reply_token, clf_agent.format_pending_menu(scope))
                continue
            if pending and user_msg.strip().upper() == "NA":
                count = len(pending.get("items", []))
                clf_agent.clear_pending(scope, remove_file=True)
                reply_message(reply_token, f"🗑️ 已取消歸檔，刪除 {count} 個待歸檔項目。")
                continue

        if user_msg.strip() == "999":
            if clf_agent:
                reply_message(reply_token, clf_agent.clear_mode())
            else:
                reply_message(reply_token, "⚠️ 歸類模式功能暫時無法使用")
            continue

        if user_msg.strip() == "5168":
            exec_menu_active[scope] = True
            awaiting_person_for_mode.pop(scope, None)
            awaiting_exec_input.pop(scope, None)
            awaiting_prospect_selection.pop(scope, None)
            awaiting_prospect_file.pop(scope, None)
            awaiting_invite_selection.pop(scope, None)
            awaiting_partner_invite_category.pop(scope, None)
            awaiting_partner_invite_person.pop(scope, None)
            awaiting_partner_invite_meeting.pop(scope, None)
            awaiting_invite_manage_select.pop(scope, None)
            awaiting_invite_manage_action.pop(scope, None)
            awaiting_invite_manage_edit.pop(scope, None)
            awaiting_promo_optimize_apply.pop(scope, None)
            awaiting_partner_voice_add.pop(scope, None)
            reply_message(reply_token, execute_menu_text)
            continue

        if exec_menu_active.get(scope) and user_msg.strip().isdigit():
            choice = int(user_msg.strip())
            item = execute_menu_items.get(choice)
            if not item:
                reply_message(reply_token, "⚠️ 無效編號，請重新輸入 5168 查看選單。")
                continue
            exec_menu_active.pop(scope, None)
            prompt = item.get("prompt")
            cmd = item.get("cmd")
            if prompt:
                reply_message(reply_token, prompt)
                continue
            if cmd:
                if cmd == "語音新增跟進夥伴":
                    awaiting_partner_voice_add[scope] = True
                    reply_message(
                        reply_token,
                        "請直接上傳語音。\n\n建議說法：\n姓名王小美，目標月入三萬，下次跟進2026年4月5日，備註持續跟進，分類A\n\n輸入 NA 可取消。",
                    )
                    continue
                handled = handle_training_command(cmd, reply_token, user_id, group_id)
                if not handled:
                    reply_message(reply_token, "⚠️ 無法辨識指令，請輸入「說明」查看可用功能。")
                continue
            reply_message(reply_token, "⚠️ 此功能尚未設定。")
            continue

        if user_msg.strip().upper() == "NA" and (
            awaiting_person_for_mode.get(scope) or awaiting_exec_input.get(scope)
            or awaiting_prospect_selection.get(scope) or awaiting_prospect_file.get(scope)
            or awaiting_invite_selection.get(scope) or awaiting_partner_invite_category.get(scope)
            or awaiting_partner_invite_person.get(scope) or awaiting_partner_invite_meeting.get(scope)
            or awaiting_invite_manage_select.get(scope) or awaiting_invite_manage_action.get(scope)
            or awaiting_invite_manage_edit.get(scope) or awaiting_promo_optimize_apply.get(scope)
            or awaiting_partner_voice_add.get(scope)
        ):
            awaiting_person_for_mode.pop(scope, None)
            awaiting_exec_input.pop(scope, None)
            awaiting_prospect_selection.pop(scope, None)
            awaiting_prospect_file.pop(scope, None)
            awaiting_invite_selection.pop(scope, None)
            awaiting_partner_invite_category.pop(scope, None)
            awaiting_partner_invite_person.pop(scope, None)
            awaiting_partner_invite_meeting.pop(scope, None)
            awaiting_invite_manage_select.pop(scope, None)
            awaiting_invite_manage_action.pop(scope, None)
            awaiting_invite_manage_edit.pop(scope, None)
            awaiting_promo_optimize_apply.pop(scope, None)
            awaiting_partner_voice_add.pop(scope, None)
            reply_message(reply_token, "↩️ 已取消，返回待機。")
            continue

        if looks_like_explicit_command(user_msg) and (
            awaiting_partner_invite_category.get(scope)
            or awaiting_partner_invite_person.get(scope)
            or awaiting_partner_invite_meeting.get(scope)
        ):
            awaiting_partner_invite_category.pop(scope, None)
            awaiting_partner_invite_person.pop(scope, None)
            awaiting_partner_invite_meeting.pop(scope, None)
            awaiting_invite_manage_select.pop(scope, None)
            awaiting_invite_manage_action.pop(scope, None)
            awaiting_invite_manage_edit.pop(scope, None)
            awaiting_promo_optimize_apply.pop(scope, None)
            awaiting_partner_voice_add.pop(scope, None)

        if awaiting_partner_voice_add.get(scope) and looks_like_explicit_command(user_msg):
            awaiting_partner_voice_add.pop(scope, None)

        if user_msg.strip() == "語音新增跟進夥伴":
            awaiting_partner_voice_add[scope] = True
            reply_message(
                reply_token,
                "請直接上傳語音。\n\n建議說法：\n姓名王小美，目標月入三萬，下次跟進2026年4月5日，備註持續跟進，分類A\n\n輸入 NA 可取消。",
            )
            continue

        if user_msg.strip().startswith("邀約文宣 跟進夥伴"):
            awaiting_partner_invite_category[scope] = True
            awaiting_partner_invite_person.pop(scope, None)
            awaiting_partner_invite_meeting.pop(scope, None)
            reply_message(reply_token, "📋 請先選擇夥伴分類屬性\n1. A 類：持續有使用產品、有積分額、且有聽過鐘老師演講\n2. B 類：偶爾使用產品，或有聽過鐘老師演講\n3. C 類：即將開始了解，或即將聽鐘老師演講\n\n請輸入 1、2、3 或 A、B、C，NA 取消")
            continue

        if awaiting_promo_optimize_apply.get(scope) and user_msg.strip().isdigit():
            state = awaiting_promo_optimize_apply.pop(scope)
            choice = int(user_msg.strip())
            if choice == 1:
                try:
                    course = load_course_invite()
                    reply_message(reply_token, course.apply_optimized_promo(state["promo_id"]))
                except Exception as e:
                    reply_message(reply_token, f"✗ 套用優化文宣失敗：{e}")
                continue
            if choice == 2:
                reply_message(reply_token, "已保留優化結果，不覆蓋原課程文宣")
                continue
            awaiting_promo_optimize_apply[scope] = state
            reply_message(reply_token, "⚠️ 請輸入 1 或 2，NA 取消")
            continue

        if awaiting_invite_manage_edit.get(scope):
            state = awaiting_invite_manage_edit[scope]
            if state.get("step") == "confirm" and user_msg.strip().isdigit():
                choice = int(user_msg.strip())
                if choice == 1:
                    awaiting_invite_manage_edit[scope] = {"step": "edit", "record": state["record"]}
                    reply_message(reply_token, "📝 請直接輸入新的邀約文宣內容，NA 取消")
                    continue
                awaiting_invite_manage_edit.pop(scope, None)
                reply_message(reply_token, "已取消修改邀約文宣")
                continue
            if state.get("step") == "confirm":
                reply_message(reply_token, "⚠️ 請輸入 1 或 2，NA 取消")
                continue
            rec = state["record"]
            awaiting_invite_manage_edit.pop(scope, None)
            new_content = user_msg.strip()
            if not new_content:
                reply_message(reply_token, "⚠️ 新內容不可空白，NA 取消")
                continue
            course = load_course_invite()
            ok = course.update_invite(rec["meeting"]["id"], rec.get("name", ""), new_content)
            reply_message(reply_token, "✅ 已更新邀約文宣" if ok else "⚠️ 找不到該筆邀約文宣")
            continue

        if awaiting_invite_manage_action.get(scope) and awaiting_invite_manage_action[scope].get("step") == "view" and user_msg.strip().isdigit():
            state = awaiting_invite_manage_action.pop(scope)
            rec = state["record"]
            choice = int(user_msg.strip())
            if choice == 1:
                awaiting_invite_manage_edit[scope] = {"step": "confirm", "record": rec}
                reply_message(reply_token, format_invite_edit_confirm(rec))
                continue
            if choice == 2:
                reply_message(reply_token, "已返回邀約文宣管理")
                continue
            reply_message(reply_token, "⚠️ 請輸入 1 或 2，NA 取消")
            continue

        if awaiting_invite_manage_action.get(scope) and user_msg.strip().isdigit():
            rec = awaiting_invite_manage_action.pop(scope)
            choice = int(user_msg.strip())
            if choice == 1:
                awaiting_invite_manage_action[scope] = {"step": "view", "record": rec}
                reply_message(reply_token, format_invite_view(rec))
                continue
            if choice == 2:
                try:
                    course = load_course_invite()
                    if rec.get("role") == "prospect":
                        result = course.generate_prospect_invite_for_meeting(rec["name"], rec["meeting"])
                    else:
                        result = course.generate_partner_invite_for_meeting(rec["name"], rec["meeting"])
                    reply_message(reply_token, result if result else "⚠️ AI 無回應，請稍後再試")
                except Exception as e:
                    reply_message(reply_token, f"✗ 強制重新產生失敗：{e}")
                continue
            reply_message(reply_token, "⚠️ 請輸入 1 或 2，NA 取消")
            continue

        if awaiting_invite_manage_select.get(scope) and user_msg.strip().isdigit():
            rows = awaiting_invite_manage_select.pop(scope)
            idx = int(user_msg.strip())
            if not (1 <= idx <= len(rows)):
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(rows)} 的編號，NA 取消")
                continue
            rec = rows[idx - 1]
            awaiting_invite_manage_action[scope] = rec
            reply_message(reply_token, format_invite_manage_actions(rec))
            continue

        if awaiting_partner_invite_category.get(scope):
            if looks_like_explicit_command(user_msg):
                awaiting_partner_invite_category.pop(scope, None)
            else:
                category = normalize_partner_category_choice(user_msg)
                if not category:
                    reply_message(reply_token, "⚠️ 請輸入 1、2、3 或 A、B、C，NA 取消")
                    continue
                people = partners_by_category(category)
                awaiting_partner_invite_category.pop(scope, None)
                if not people:
                    reply_message(reply_token, f"⚠️ 目前沒有分類 {category} 的夥伴。")
                    continue
                awaiting_partner_invite_person[scope] = {"category": category, "people": people}
                reply_message(reply_token, format_partner_choice_menu(category, people))
                continue

        if awaiting_partner_invite_person.get(scope) and user_msg.strip().isdigit():
            state = awaiting_partner_invite_person[scope]
            people = state["people"]
            idx = int(user_msg.strip())
            if not (1 <= idx <= len(people)):
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(people)} 的編號，NA 取消")
                continue
            person = people[idx - 1]
            course = load_course_invite()
            meetings = course.list_meetings()
            awaiting_partner_invite_person.pop(scope, None)
            if not meetings:
                reply_message(reply_token, "⚠️ 目前沒有排定的課程會議，請先新增課程會議。")
                continue
            awaiting_partner_invite_meeting[scope] = {"name": person.get("name", ""), "meetings": meetings}
            reply_message(reply_token, format_meeting_choice_menu(person.get("name", ""), meetings))
            continue

        if awaiting_partner_invite_meeting.get(scope) and user_msg.strip().isdigit():
            state = awaiting_partner_invite_meeting.pop(scope)
            meetings = state["meetings"]
            idx = int(user_msg.strip())
            if not (1 <= idx <= len(meetings)):
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(meetings)} 的編號，NA 取消")
                continue
            meeting = meetings[idx - 1]
            person_name = state["name"]
            try:
                course = load_course_invite()
                result = course.generate_partner_invite_for_meeting(person_name, meeting)
                reply_message(reply_token, result if result else "⚠️ AI 無回應，請稍後再試")
            except Exception as e:
                reply_message(reply_token, f"✗ 邀約文宣產生失敗：{e}")
            continue

        if awaiting_prospect_file.get(scope) and user_msg.strip().isdigit():
            rows = awaiting_prospect_file.pop(scope)
            idx = int(user_msg.strip())
            if 1 <= idx <= len(rows):
                person_name = rows[idx - 1].get("姓名", "")
                try:
                    clf_mod = load_classifier_module()
                    result = clf_mod.ClassifierAgent().set_mode("市場開發", person_name)
                    reply_message(reply_token, result + "\n\n📸 現在直接上傳照片或檔案，會自動歸入該潛在家人資料夾。")
                except Exception as e:
                    reply_message(reply_token, f"⚠️ 設定失敗：{e}")
            else:
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(rows)} 的編號，NA 取消")
            continue

        if awaiting_prospect_selection.get(scope) and user_msg.strip().isdigit():
            rows = awaiting_prospect_selection[scope]
            idx = int(user_msg.strip())
            if 1 <= idx <= len(rows):
                reply_message(reply_token, format_prospect_detail(rows[idx - 1]))
            else:
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(rows)} 的編號，NA 取消")
            continue

        if user_msg.strip() == "查詢已產生的今日之後會議邀約文宣":
            try:
                course = load_course_invite()
                rows = course.list_upcoming_invites(today_only_after=True)
            except Exception as e:
                reply_message(reply_token, f"⚠️ 查詢已產生邀約文宣失敗：{e}")
                continue
            if rows:
                awaiting_invite_manage_select[scope] = rows
            else:
                awaiting_invite_manage_select.pop(scope, None)
            reply_message(reply_token, format_invite_manage_list(rows))
            continue

        handled = handle_training_command(user_msg, reply_token, user_id, group_id)
        if (not handled) and user_msg.strip().startswith("優化課程文宣"):
            try:
                course = load_course_invite()
                result = course.CourseInviteAgent().handle_command(user_msg.strip())
                if result and result.startswith("✅ 文宣已優化（"):
                    promo_id = user_msg.strip().replace("優化課程文宣", "", 1).strip()
                    awaiting_promo_optimize_apply[scope] = {"promo_id": promo_id}
                    reply_message(
                        reply_token,
                        result + "\n\n1. 套用到該課程文宣\n2. 保留優化結果，不覆蓋\n\n請輸入 1 或 2，NA 取消",
                    )
                else:
                    reply_message(reply_token, result or "⚠️ AI 無回應，請稍後再試")
            except Exception as e:
                reply_message(reply_token, f"✗ 優化課程文宣失敗：{e}")
            continue
        if not handled:
            reply_message(reply_token, "⚠️ 無法辨識指令，請輸入「說明」查看可用功能。")

    return "OK", 200
