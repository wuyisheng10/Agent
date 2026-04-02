def register_api_routes(
    app,
    *,
    process_web_command,
    request,
    nutrition_sessions,
    load_classifier,
    load_market_dev,
    load_partner,
    load_course_invite,
    load_daily_report,
    load_nutrition_assessment,
    load_ai_prompt_manager,
    load_ai_skill_manager,
):
    @app.route("/api/command", methods=["POST"])
    def api_command():
        try:
            data = request.get_json(force=True) or {}
            cmd = data.get("command", "").strip()
            if not cmd:
                return {"result": "缺少指令"}, 400
            return {"result": process_web_command(cmd)}
        except Exception as e:
            return {"result": f"指令執行失敗：{e}"}, 500

    @app.route("/api/upload", methods=["POST"])
    def api_upload():
        try:
            if "file" not in request.files:
                return {"result": "沒有收到檔案"}, 400

            f = request.files["file"]
            filename = f.filename or "upload"
            data = f.read()
            content_type = f.content_type or "application/octet-stream"

            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext in ("jpg", "jpeg", "png", "gif", "webp"):
                file_type = "image"
            elif ext in ("m4a", "mp3", "wav", "ogg", "aac"):
                file_type = "audio"
            elif ext in ("mp4", "mov", "avi", "mkv"):
                file_type = "video"
            else:
                file_type = "file"

            if file_type == "image" and "web" in nutrition_sessions and nutrition_sessions["web"].get("awaiting_photo"):
                na_mod = load_nutrition_assessment()
                session = nutrition_sessions["web"]
                meal_label = session.pop("next_meal_label", None)
                result = na_mod.NutritionAssessmentAgent().add_photo(session, data, meal_label)
                return {"result": result}

            clf_mod = load_classifier()
            clf = clf_mod.ClassifierAgent()
            clf.stage_file(data, filename, file_type, "web_user", content_type=content_type, source_name=filename)
            return {"result": clf.format_pending_menu("web_user")}
        except Exception as e:
            return {"result": f"上傳失敗：{e}"}, 500

    @app.route("/api/pending", methods=["GET"])
    def api_pending():
        try:
            clf = load_classifier().ClassifierAgent()
            menu = clf.format_pending_menu("web_user")
            return {"result": menu if menu else None}
        except Exception:
            return {"result": None}

    @app.route("/api/pending/execute", methods=["POST"])
    def api_pending_execute():
        try:
            data = request.get_json(force=True) or {}
            choice = int(data.get("choice", 0))
            clf = load_classifier().ClassifierAgent()
            if choice == 0:
                pending = clf.get_pending("web_user")
                if not pending:
                    return {"result": "目前沒有待歸檔項目"}
                count = len(pending.get("items", []))
                clf.clear_pending("web_user", remove_file=True)
                return {"result": f"已清除待歸檔，共 {count} 項"}
            return {"result": clf.execute_pending_option("web_user", choice)}
        except Exception as e:
            return {"result": f"待歸檔執行失敗：{e}"}, 500

    @app.route("/api/prospect/<name>", methods=["GET"])
    def api_prospect_get(name):
        try:
            row = load_market_dev().MarketDevAgent().get_prospect_by_name(name)
            if row:
                return {"result": row}
            return {"result": None}, 404
        except Exception as e:
            return {"result": None, "error": str(e)}, 500

    @app.route("/api/prospects", methods=["GET"])
    def api_prospects():
        try:
            market = load_market_dev()
            rows = market.MarketDevAgent().list_prospects()
            try:
                from webhook_router_helpers import prospect_category_from_row
            except ModuleNotFoundError:
                from agents.webhook_router_helpers import prospect_category_from_row

            items = []
            for row in rows:
                name = str(row.get("姓名", "") or row.get("憪?", "")).strip()
                if not name:
                    continue
                items.append(
                    {
                        "name": name,
                        "job": str(row.get("職業", "") or row.get("?瑟平", "")).strip(),
                        "area": str(row.get("地區", "") or row.get("?啣?", "")).strip(),
                        "status": str(row.get("接觸狀態", "")).strip(),
                        "tag": str(row.get("需求標籤", "")).strip(),
                        "category": prospect_category_from_row(row),
                    }
                )
            items.sort(key=lambda x: x.get("name", ""))
            return {"result": items}
        except Exception as e:
            return {"result": [], "error": str(e)}, 500

    @app.route("/api/partners", methods=["GET"])
    def api_partners():
        try:
            items = load_partner().load_partners()
            rows = [
                {
                    "name": item.get("name", ""),
                    "amway_no": item.get("amway_no", ""),
                    "stage": item.get("stage", ""),
                    "level": item.get("level", ""),
                    "category": item.get("category", ""),
                }
                for item in items
                if item.get("name")
            ]
            rows.sort(key=lambda x: (x.get("name", ""), x.get("amway_no", "")))
            return {"result": rows}
        except Exception as e:
            return {"result": [], "error": str(e)}, 500

    @app.route("/api/partner-statuses", methods=["GET"])
    def api_partner_statuses():
        try:
            return {"result": load_partner().PARTNER_STAGE_DEFINITIONS}
        except Exception as e:
            return {"result": [], "error": str(e)}, 500

    @app.route("/api/partner/<name>", methods=["GET"])
    def api_partner_get(name):
        try:
            partner = load_partner()
            items = partner.load_partners()
            item = partner._find_partner(name, items)
            if not item:
                return {"result": None}, 404
            return {"result": item}
        except Exception as e:
            return {"result": None, "error": str(e)}, 500

    @app.route("/api/course-promos", methods=["GET"])
    def api_course_promos():
        try:
            rows = load_course_invite().list_promos()
            items = []
            for row in rows:
                promo_id = str(row.get("id", "")).strip()
                if not promo_id:
                    continue
                items.append(
                    {
                        "id": promo_id,
                        "title": str(row.get("title", "")).strip(),
                        "content": str(row.get("content", "")).strip(),
                        "optimized": str(row.get("optimized", "")).strip(),
                    }
                )
            items.sort(key=lambda x: x.get("id", ""))
            return {"result": items}
        except Exception as e:
            return {"result": [], "error": str(e)}, 500

    @app.route("/api/course-invite", methods=["GET"])
    def api_course_invite_get():
        try:
            meeting_id = request.args.get("id", "").strip()
            name = request.args.get("name", "").strip()
            if not meeting_id or not name:
                return {"result": None, "error": "缺少 id 或 name"}, 400
            rec = load_course_invite().get_invite(meeting_id, name)
            if rec:
                return {"result": rec}
            return {"result": None}, 404
        except Exception as e:
            return {"result": None, "error": str(e)}, 500

    @app.route("/api/course-invite/update", methods=["POST"])
    def api_course_invite_update():
        try:
            data = request.get_json(force=True) or {}
            meeting_id = data.get("meeting_id", "").strip()
            name = data.get("name", "").strip()
            content = data.get("content", "").strip()
            if not meeting_id or not name or not content:
                return {"result": "缺少必要欄位"}, 400
            ok = load_course_invite().update_invite(meeting_id, name, content)
            if ok:
                return {"result": "已更新邀約文宣"}
            return {"result": "找不到要更新的邀約文宣"}, 404
        except Exception as e:
            return {"result": f"更新邀約文宣失敗：{e}"}, 500

    @app.route("/api/prospect/update", methods=["POST"])
    def api_prospect_update():
        try:
            data = request.get_json(force=True) or {}
            name = data.pop("name", "").strip()
            if not name:
                return {"result": "缺少姓名"}, 400
            result = load_market_dev().MarketDevAgent().update_prospect_fields(name, data)
            return {"result": result}
        except Exception as e:
            return {"result": f"更新潛在家人失敗：{e}"}, 500

    @app.route("/api/prospect/experience", methods=["POST"])
    def api_prospect_experience():
        try:
            data = request.get_json(force=True) or {}
            name = data.get("name", "").strip()
            product = data.get("product", "").strip()
            if not name or not product:
                return {"result": "缺少姓名或產品"}, 400
            result = load_market_dev().MarketDevAgent().add_experience(
                name,
                product,
                note=data.get("note", ""),
                filter_last=data.get("filter_last", ""),
                filter_next=data.get("filter_next", ""),
            )
            return {"result": result}
        except Exception as e:
            return {"result": f"新增體驗失敗：{e}"}, 500

    @app.route("/api/send-daily-report", methods=["POST"])
    def api_send_daily_report():
        try:
            return {"result": load_daily_report().DailyReportAgent().run()}
        except Exception as e:
            return {"result": f"寄送每日報告失敗：{e}"}, 500

    @app.route("/api/ai-prompts", methods=["GET"])
    def api_ai_prompts():
        try:
            return {"result": load_ai_prompt_manager().list_prompt_labels()}
        except Exception as e:
            return {"result": [], "error": str(e)}, 500

    @app.route("/api/ai-prompt/<key>", methods=["GET"])
    def api_ai_prompt_detail(key):
        try:
            item = load_ai_prompt_manager().get_prompt(key)
            if not item:
                return {"result": None}, 404
            return {"result": {"key": key, **item}}
        except Exception as e:
            return {"result": None, "error": str(e)}, 500

    @app.route("/api/ai-skills", methods=["GET"])
    def api_ai_skills():
        try:
            return {"result": load_ai_skill_manager().list_skill_labels()}
        except Exception as e:
            return {"result": [], "error": str(e)}, 500

    @app.route("/api/ai-skill/<key>", methods=["GET"])
    def api_ai_skill_detail(key):
        try:
            item = load_ai_skill_manager().get_skill(key)
            if not item:
                return {"result": None}, 404
            return {"result": {"key": key, **item}}
        except Exception as e:
            return {"result": None, "error": str(e)}, 500
