from pathlib import Path


ROOT = Path(r"C:\Users\user\claude AI_Agent")


def replace_range(path: Path, start_line: int, end_line: int, new_lines: list[str]):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines[start_line - 1 : end_line] = new_lines
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rewrite_webhook_router():
    path = ROOT / "agents" / "webhook_command_router.py"
    replace_range(
        path,
        227,
        245,
        [
            "    training_system_prefixes = (",
            '        "新增培訓模組",',
            '        "查詢培訓模組",',
            '        "新增培訓課程",',
            '        "查詢培訓課程",',
            '        "新增培訓反思",',
            '        "查詢培訓進度",',
            '        "查詢培訓總表",',
            '        "啟動七天法則",',
            '        "七天法則回報",',
            '        "查詢七天法則",',
            '        "新增課後行動",',
            '        "回報課後行動",',
            '        "查詢課後行動",',
            "    )",
            "    if any(msg.startswith(prefix) for prefix in training_system_prefixes):",
            "        try:",
            "            training_system = load_training_system()",
            "            result = training_system.TrainingSystemAgent().handle_command(msg)",
            "            if result:",
            "                reply_message(reply_token, result)",
            "                return True",
            "        except Exception as exc:",
            '            reply_message(reply_token, f"✗ 培訓系統指令失敗：{exc}")',
            "            return True",
        ],
    )
    replace_range(
        path,
        414,
        427,
        [
            "    training_system_prefixes = (",
            '        "新增培訓模組",',
            '        "查詢培訓模組",',
            '        "新增培訓課程",',
            '        "查詢培訓課程",',
            '        "新增培訓反思",',
            '        "查詢培訓進度",',
            '        "查詢培訓總表",',
            '        "啟動七天法則",',
            '        "七天法則回報",',
            '        "查詢七天法則",',
            '        "新增課後行動",',
            '        "回報課後行動",',
            '        "查詢課後行動",',
            "    )",
            "    if any(cmd.startswith(prefix) for prefix in training_system_prefixes):",
            "        training_system = load_training_system()",
            "        result = training_system.TrainingSystemAgent().handle_command(cmd)",
            "        if result:",
            "            return result",
        ],
    )


def rewrite_web_views():
    path = ROOT / "agents" / "webhook_web_views.py"
    replace_range(
        path,
        219,
        254,
        [
            '  {label:"🎓 培訓系統",items:[',
            '    {label:"新增培訓模組",tag:"表單",form:{title:"新增培訓模組",',
            '      fields:[{id:"t",lbl:"模組名稱",type:"text",req:1,ph:"例：四個勇於"},',
            '              {id:"c",lbl:"模組類型",type:"select",req:1,opts:["領導人特質","新人守則","帶線系統","市場實戰","畫畫培訓","產品培訓","事業培訓"]},',
            '              {id:"g",lbl:"學習目標",type:"textarea",ph:"例：建立領導人思維與承擔能力"},',
            '              {id:"s",lbl:"核心摘要",type:"textarea",ph:"例：勇於學習、勇於認錯、勇於改變、勇於承擔"}],',
            '      build:function(v){return "新增培訓模組 "+v.t+" | "+v.c+" | "+v.g+" | "+v.s;}}},',
            '    {label:"查詢培訓模組",tag:"表單",form:{title:"查詢培訓模組",',
            '      fields:[{id:"t",lbl:"模組名稱（選填）",type:"text",ph:"空白則查全部"}],',
            '      build:function(v){return v.t?"查詢培訓模組 "+v.t:"查詢培訓模組";}}},',
            '    {label:"新增培訓課程",tag:"表單",form:{title:"新增培訓課程",',
            '      fields:[{id:"t",lbl:"課程名稱",type:"text",req:1,ph:"例：領導人特質｜四個勇於"},',
            '              {id:"m",lbl:"模組名稱",type:"text",req:1,ph:"請選擇模組"},',
            '              {id:"d",lbl:"日期",type:"date",req:1},',
            '              {id:"tm",lbl:"時間",type:"time",req:1},',
            '              {id:"loc",lbl:"地點",type:"text",req:1,ph:"例：台南教室"},',
            '              {id:"sp",lbl:"講師",type:"text",ph:"例：鐘老師"},',
            '              {id:"aud",lbl:"對象",type:"select",req:1,opts:["潛在家人","夥伴","新手夥伴","核心夥伴"]}],',
            '      build:function(v){return "新增培訓課程 "+v.t+" | "+v.m+" | "+v.d+" | "+v.tm+" | "+v.loc+" | "+v.sp+" | "+v.aud;}}},',
            '    {label:"查詢培訓課程",tag:"表單",form:{title:"查詢培訓課程",',
            '      fields:[{id:"d",lbl:"日期（選填）",type:"date"},',
            '              {id:"m",lbl:"模組名稱（選填）",type:"text",ph:"空白則查全部"}],',
            '      build:function(v){var q=v.d||v.m||"";return q?"查詢培訓課程 "+q:"查詢培訓課程";}}},',
            '    {label:"新增培訓反思",tag:"表單",form:{title:"新增培訓反思",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},',
            '              {id:"st",lbl:"課程名稱",type:"text",req:1,ph:"請選擇課程"},',
            '              {id:"i",lbl:"悟到",type:"textarea",ph:"今天最大的提醒是什麼"},',
            '              {id:"l",lbl:"學到",type:"textarea",ph:"學到哪個觀念或方法"},',
            '              {id:"a",lbl:"做到",type:"textarea",ph:"接下來準備採取的行動"},',
            '              {id:"g",lbl:"目標",type:"textarea",ph:"希望達成的具體目標"}],',
            '      build:function(v){return "新增培訓反思 "+v.n+" | "+v.st+" | "+v.i+" | "+v.l+" | "+v.a+" | "+v.g;}}},',
            '    {label:"查詢培訓進度",tag:"表單",form:{title:"查詢培訓進度",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],',
            '      build:function(v){return "查詢培訓進度 "+v.n;}}},',
            '    {label:"查詢培訓總表",tag:"執行",cmd:"查詢培訓總表"},',
            '    {label:"啟動七天法則",tag:"表單",form:{title:"啟動七天法則",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},',
            '              {id:"d",lbl:"開始日期",type:"date",req:1},',
            '              {id:"note",lbl:"教練備註（選填）",type:"textarea",ph:"例：先陪他完成七天暖身"}],',
            '      build:function(v){return "啟動七天法則 "+v.n+" | "+v.d+" | "+v.note;}}},',
            '    {label:"七天法則回報",tag:"表單",form:{title:"七天法則回報",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},',
            '              {id:"day",lbl:"第幾天",type:"select",req:1,opts:["第1天","第2天","第3天","第4天","第5天","第6天","第7天"]},',
            '              {id:"task",lbl:"任務內容",type:"textarea",req:1,ph:"例：聽 OPP、進教室、回報感想"},',
            '              {id:"done",lbl:"完成狀態",type:"select",req:1,opts:["已完成","未完成"]},',
            '              {id:"note",lbl:"備註（選填）",type:"textarea",ph:"例：今天對環境比較有感"}],',
            '      build:function(v){return "七天法則回報 "+v.n+" | "+v.day+" | "+v.task+" | "+v.done+" | "+v.note;}}},',
            '    {label:"查詢七天法則",tag:"表單",form:{title:"查詢七天法則",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],',
            '      build:function(v){return "查詢七天法則 "+v.n;}}},',
            '    {label:"新增課後行動",tag:"表單",form:{title:"新增課後行動",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},',
            '              {id:"st",lbl:"課程名稱",type:"text",req:1,ph:"請選擇課程"},',
            '              {id:"content",lbl:"行動內容",type:"textarea",req:1,ph:"例：本週邀約 2 位新朋友"},',
            '              {id:"due",lbl:"截止日期",type:"date",req:1}],',
            '      build:function(v){return "新增課後行動 "+v.n+" | "+v.st+" | "+v.content+" | "+v.due;}}},',
            '    {label:"回報課後行動",tag:"表單",form:{title:"回報課後行動",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"},',
            '              {id:"aid",lbl:"行動 ID",type:"text",req:1,ph:"先查詢課後行動取得 ID"},',
            '              {id:"status",lbl:"狀態",type:"select",req:1,opts:["待執行","進行中","已完成","延後","需協助"]},',
            '              {id:"note",lbl:"備註（選填）",type:"textarea",ph:"例：已完成第一步"}],',
            '      build:function(v){return "回報課後行動 "+v.n+" | "+v.aid+" | "+v.status+" | "+v.note;}}},',
            '    {label:"查詢課後行動",tag:"表單",form:{title:"查詢課後行動",',
            '      fields:[{id:"n",lbl:"夥伴姓名",type:"text",req:1,ph:"請選擇夥伴"}],',
            '      build:function(v){return "查詢課後行動 "+v.n;}}},',
            "  ]},",
        ],
    )
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace('return !!f && (f.title||"")==="?亥岷?寡??脣漲";', 'return !!f && (f.title||"")==="查詢培訓進度";')
    text = text.replace('return !!f && (f.title||"")==="?啣??寡???;', 'return !!f && (f.title||"")==="新增培訓反思";')
    text = text.replace('return !!f && (f.title||"")==="?啣??寡?隤脩?";', 'return !!f && (f.title||"")==="新增培訓課程";')
    text = text.replace('return !!f && (f.title||"")==="?亥岷?寡?隤脩?";', 'return !!f && (f.title||"")==="查詢培訓課程";')
    text = text.replace('return !!f && (f.title||"")==="?亥岷?寡?璅∠?";', 'return !!f && (f.title||"")==="查詢培訓模組";')
    if 'function _isSevenDayForm(f){' not in text:
        text = text.replace(
            'function _isMilestoneForm(f){',
            'function _isSevenDayForm(f){\n'
            '  return !!f && ((f.title||"")==="啟動七天法則"||(f.title||"")==="七天法則回報"||(f.title||"")==="查詢七天法則");\n'
            '}\n'
            'function _isTrainingActionForm(f){\n'
            '  return !!f && ((f.title||"")==="新增課後行動"||(f.title||"")==="回報課後行動"||(f.title||"")==="查詢課後行動");\n'
            '}\n'
            'function _isMilestoneForm(f){'
        )
    text = text.replace(
        'if(!_isUpdatePartnerForm(formDef)&&!_isFollowupAddForm(formDef)&&!_isFollowupForm(formDef)&&!_isMotivateForm(formDef)&&!_isTrainingProgressForm(formDef)&&!_isTrainingReflectionForm(formDef)&&!_isMilestoneForm(formDef)&&!_isPartnerLookupForm(formDef))return;',
        'if(!_isUpdatePartnerForm(formDef)&&!_isFollowupAddForm(formDef)&&!_isFollowupForm(formDef)&&!_isMotivateForm(formDef)&&!_isTrainingProgressForm(formDef)&&!_isTrainingReflectionForm(formDef)&&!_isSevenDayForm(formDef)&&!_isTrainingActionForm(formDef)&&!_isMilestoneForm(formDef)&&!_isPartnerLookupForm(formDef))return;'
    )
    path.write_text(text, encoding="utf-8")


def append_webhook_text():
    path = ROOT / "agents" / "webhook_text.py"
    with open(path, "a", encoding="utf-8") as f:
        f.write(
            '\n# Training system clean overrides\n'
            'EXEC_MENU_ITEMS[81] = {"label": "新增培訓模組", "cmd": None, "prompt": "請輸入：新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要"}\n'
            'EXEC_MENU_ITEMS[82] = {"label": "查詢培訓模組", "cmd": "查詢培訓模組", "prompt": None}\n'
            'EXEC_MENU_ITEMS[83] = {"label": "新增培訓課程", "cmd": None, "prompt": "請輸入：新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象"}\n'
            'EXEC_MENU_ITEMS[84] = {"label": "查詢培訓課程", "cmd": "查詢培訓課程", "prompt": None}\n'
            'EXEC_MENU_ITEMS[85] = {"label": "新增培訓反思", "cmd": None, "prompt": "請輸入：新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標"}\n'
            'EXEC_MENU_ITEMS[86] = {"label": "查詢培訓進度", "cmd": None, "prompt": "請輸入：查詢培訓進度 姓名"}\n'
            'EXEC_MENU_ITEMS[87] = {"label": "查詢培訓總表", "cmd": "查詢培訓總表", "prompt": None}\n'
            'EXEC_MENU_ITEMS[88] = {"label": "啟動七天法則", "cmd": None, "prompt": "請輸入：啟動七天法則 姓名 | 開始日期 | 教練備註"}\n'
            'EXEC_MENU_ITEMS[89] = {"label": "七天法則回報", "cmd": None, "prompt": "請輸入：七天法則回報 姓名 | 第幾天 | 任務內容 | 已完成/未完成 | 備註"}\n'
            'EXEC_MENU_ITEMS[90] = {"label": "查詢七天法則", "cmd": None, "prompt": "請輸入：查詢七天法則 姓名"}\n'
            'EXEC_MENU_ITEMS[91] = {"label": "新增課後行動", "cmd": None, "prompt": "請輸入：新增課後行動 姓名 | 課程名稱 | 行動內容 | 截止日期"}\n'
            'EXEC_MENU_ITEMS[92] = {"label": "回報課後行動", "cmd": None, "prompt": "請輸入：回報課後行動 姓名 | ACTION-ID | 狀態 | 備註"}\n'
            'EXEC_MENU_ITEMS[93] = {"label": "查詢課後行動", "cmd": None, "prompt": "請輸入：查詢課後行動 姓名"}\n'
            'EXEC_MENU_TEXT += "\\n\\n🎓 培訓系統 2.0（新版）\\n 81. 新增培訓模組\\n 82. 查詢培訓模組 ▶\\n 83. 新增培訓課程\\n 84. 查詢培訓課程 ▶\\n 85. 新增培訓反思\\n 86. 查詢培訓進度 ▶\\n 87. 查詢培訓總表 ▶\\n 88. 啟動七天法則\\n 89. 七天法則回報\\n 90. 查詢七天法則 ▶\\n 91. 新增課後行動\\n 92. 回報課後行動\\n 93. 查詢課後行動 ▶"\n'
            'HELP_TEXT += "\\n\\n🎓 培訓系統 2.0（新版）\\n  新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要\\n  查詢培訓模組 [模組名稱]\\n  新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象\\n  查詢培訓課程 [日期或模組名稱]\\n  新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標\\n  查詢培訓進度 姓名\\n  查詢培訓總表\\n  啟動七天法則 姓名 | 開始日期 | 教練備註\\n  七天法則回報 姓名 | 第幾天 | 任務內容 | 已完成/未完成 | 備註\\n  查詢七天法則 姓名\\n  新增課後行動 姓名 | 課程名稱 | 行動內容 | 截止日期\\n  回報課後行動 姓名 | ACTION-ID | 狀態 | 備註\\n  查詢課後行動 姓名\\n"\n'
        )


def rewrite_smoke_test():
    path = ROOT / "tests" / "test_all_features_smoke.py"
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for idx, line in enumerate(text):
        if 'patch.object(training_system, "PROGRESS_FILE"' in line:
            text[idx + 1 : idx + 1] = [
                '            patch.object(training_system, "SEVEN_DAY_FILE", self.training_system_dir / "seven_day.json"),',
                '            patch.object(training_system, "ACTIONS_FILE", self.training_system_dir / "actions.json"),',
            ]
            break
    start = next(i for i, line in enumerate(text) if line.strip().startswith("def test_training_system_phase1_flow"))
    end = next(i for i, line in enumerate(text[start:], start=start) if line.strip() == 'if __name__ == "__main__":')
    text[start:end] = [
        "    def test_training_system_phase1_flow(self):",
        "        agent = training_system.TrainingSystemAgent()",
        '        self.assertIn("已新增培訓模組", agent.handle_command("新增培訓模組 四個勇於 | 領導人特質 | 建立領導人思維 | 勇於學習、勇於認錯、勇於改變、勇於承擔"))',
        '        self.assertIn("已新增培訓課程", agent.handle_command("新增培訓課程 領導人特質｜四個勇於 | 四個勇於 | 2026-04-10 | 19:30 | 台南教室 | 鐘老師 | 夥伴"))',
        '        self.assertIn("已新增培訓反思", agent.handle_command("新增培訓反思 建德 | 領導人特質｜四個勇於 | 願意認錯 | 學到四個勇於 | 每天回報市場 | 建立帶線節奏"))',
        '        self.assertIn("建德 的培訓進度", agent.handle_command("查詢培訓進度 建德"))',
        '        self.assertIn("培訓總表", agent.handle_command("查詢培訓總表"))',
        '        self.assertIn("已啟動七天法則", agent.handle_command("啟動七天法則 建德 | 2026-04-12 | 先陪跑"))',
        '        self.assertIn("已更新七天法則", agent.handle_command("七天法則回報 建德 | 第1天 | 聽 OPP | 已完成 | 有回報感想"))',
        '        self.assertIn("已新增課後行動", agent.handle_command("新增課後行動 建德 | 領導人特質｜四個勇於 | 本週邀約 2 位朋友 | 2026-04-18"))',
        '        self.assertIn("建德 的課後行動", agent.handle_command("查詢課後行動 建德"))',
        "",
    ]
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


def rewrite_line_web_validation():
    path = ROOT / "tests" / "test_line_web_full_validation.py"
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace('????', '四個勇於')
    text = text.replace('銝予瘜?', '七天法則')
    text = text.replace('??鈭箇鞈迎?????', '領導人特質｜四個勇於')
    text = text.replace('?唬犖銝予瘜?', '新人七天法則')
    text = text.replace(
        '"查詢培訓進度": "查詢培訓進度 建德",',
        '"查詢培訓進度": "查詢培訓進度 建德",\n    "啟動七天法則": "啟動七天法則 建德 | 2026-04-12 | 先陪跑",\n    "七天法則回報": "七天法則回報 建德 | 第1天 | 聽 OPP、進教室 | 已完成 | 有回報感想",\n    "查詢七天法則": "查詢七天法則 建德",\n    "新增課後行動": "新增課後行動 建德 | 領導人特質｜四個勇於 | 本週邀約 2 位朋友 | 2026-04-18",\n    "回報課後行動": "回報課後行動 建德 | TA-建德-001 | 進行中 | 已完成第一步",\n    "查詢課後行動": "查詢課後行動 建德",'
    )
    text = text.replace(
        '        self.assertIn("新增培訓反思", html)\n',
        '        self.assertIn("新增培訓反思", html)\n        self.assertIn("啟動七天法則", html)\n        self.assertIn("新增課後行動", html)\n'
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    rewrite_webhook_router()
    rewrite_web_views()
    append_webhook_text()
    rewrite_smoke_test()
    rewrite_line_web_validation()
