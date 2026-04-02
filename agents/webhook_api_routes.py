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
):
    @app.route("/api/command", methods=["POST"])
    def api_command():
        try:
            data = request.get_json(force=True) or {}
            cmd = data.get("command", "").strip()
            if not cmd:
                return {"result": "⚠️ 請提供指令"}, 400
            result = process_web_command(cmd)
            return {"result": result}
        except Exception as e:
            return {"result": f"⚠️ 伺服器錯誤：{e}"}, 500

    @app.route("/api/upload", methods=["POST"])
    def api_upload():
        try:
            if "file" not in request.files:
                return {"result": "⚠️ 未找到上傳的檔案"}, 400
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
            menu = clf.format_pending_menu("web_user")
            return {"result": menu}
        except Exception as e:
            return {"result": f"⚠️ 上傳失敗：{e}"}, 500

    @app.route("/api/pending", methods=["GET"])
    def api_pending():
        try:
            clf_mod = load_classifier()
            clf = clf_mod.ClassifierAgent()
            menu = clf.format_pending_menu("web_user")
            return {"result": menu if menu else None}
        except Exception:
            return {"result": None}

    @app.route("/api/pending/execute", methods=["POST"])
    def api_pending_execute():
        try:
            data = request.get_json(force=True) or {}
            choice = int(data.get("choice", 0))
            clf_mod = load_classifier()
            clf = clf_mod.ClassifierAgent()
            if choice == 0:
                pending = clf.get_pending("web_user")
                if not pending:
                    return {"result": "目前沒有待歸檔項目"}
                count = len(pending.get("items", []))
                clf.clear_pending("web_user", remove_file=True)
                return {"result": f"已清除待歸檔 {count} 項"}
            result = clf.execute_pending_option("web_user", choice)
            return {"result": result}
        except Exception as e:
            return {"result": f"⚠️ 執行失敗：{e}"}, 500

    @app.route("/api/prospect/<name>", methods=["GET"])
    def api_prospect_get(name):
        try:
            market = load_market_dev()
            row = market.MarketDevAgent().get_prospect_by_name(name)
            if row:
                return {"result": row}
            return {"result": None}, 404
        except Exception as e:
            return {"result": None, "error": str(e)}, 500

    @app.route("/api/partners", methods=["GET"])
    def api_partners():
        try:
            partner = load_partner()
            items = partner.load_partners()
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

    @app.route("/api/course-invite", methods=["GET"])
    def api_course_invite_get():
        try:
            meeting_id = request.args.get("id", "").strip()
            name = request.args.get("name", "").strip()
            if not meeting_id or not name:
                return {"result": None, "error": "缺少 id 或 name"}, 400
            course = load_course_invite()
            rec = course.get_invite(meeting_id, name)
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
                return {"result": "⚠️ 缺少必要欄位"}, 400
            course = load_course_invite()
            ok = course.update_invite(meeting_id, name, content)
            if ok:
                return {"result": "✅ 邀約文宣已更新"}
            return {"result": "⚠️ 找不到該筆邀約，請先產生"}, 404
        except Exception as e:
            return {"result": f"⚠️ 更新失敗：{e}"}, 500

    @app.route("/api/prospect/update", methods=["POST"])
    def api_prospect_update():
        try:
            data = request.get_json(force=True) or {}
            name = data.pop("name", "").strip()
            if not name:
                return {"result": "⚠️ 請提供姓名"}, 400
            market = load_market_dev()
            result = market.MarketDevAgent().update_prospect_fields(name, data)
            return {"result": result}
        except Exception as e:
            return {"result": f"⚠️ 更新失敗：{e}"}, 500

    @app.route("/api/prospect/experience", methods=["POST"])
    def api_prospect_experience():
        try:
            data = request.get_json(force=True) or {}
            name = data.get("name", "").strip()
            product = data.get("product", "").strip()
            if not name or not product:
                return {"result": "⚠️ 姓名和產品為必填"}, 400
            market = load_market_dev()
            result = market.MarketDevAgent().add_experience(
                name,
                product,
                note=data.get("note", ""),
                filter_last=data.get("filter_last", ""),
                filter_next=data.get("filter_next", ""),
            )
            return {"result": result}
        except Exception as e:
            return {"result": f"⚠️ 新增失敗：{e}"}, 500

    @app.route("/api/send-daily-report", methods=["POST"])
    def api_send_daily_report():
        try:
            dr = load_daily_report()
            result = dr.DailyReportAgent().run()
            return {"result": result}
        except Exception as e:
            return {"result": f"⚠️ 每日報告失敗：{e}"}, 500

    @app.route("/api/ai-prompts", methods=["GET"])
    def api_ai_prompts():
        try:
            pm = load_ai_prompt_manager()
            return {"result": pm.list_prompt_labels()}
        except Exception as e:
            return {"result": [], "error": str(e)}, 500
