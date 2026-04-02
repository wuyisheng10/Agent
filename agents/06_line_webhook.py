"""
LINE Bot Webhook Server
File: C:/Users/user/claude AI_Agent/agents/06_line_webhook.py
Function: Receive user replies, AI intent detection, update follow-up status
Run: python 06_line_webhook.py (keep running)
External access: use ngrok (free) to expose Webhook URL
"""

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, abort, send_from_directory
from dotenv import load_dotenv
import importlib.util as _ilu
import sys as _sys
try:
    from webhook_common import (
        BASE_DIR as COMMON_BASE_DIR,
        CLASSIFIED_DIR as COMMON_CLASSIFIED_DIR,
        LINE_PUSH as COMMON_LINE_PUSH,
        LINE_REPLY as COMMON_LINE_REPLY,
        LINE_SECRET as COMMON_LINE_SECRET,
        LINE_TOKEN as COMMON_LINE_TOKEN,
        LOG_FILE as COMMON_LOG_FILE,
        NGROK_URL as COMMON_NGROK_URL,
        SENT_LOG as COMMON_SENT_LOG,
        _load_calendar as common_load_calendar,
        _load_classifier as common_load_classifier,
        _load_course_invite as common_load_course_invite,
        _load_daily_report as common_load_daily_report,
        _load_followup as common_load_followup,
        _load_market_dev as common_load_market_dev,
        _load_motivation as common_load_motivation,
        _load_nutrition_assessment as common_load_nutrition_assessment,
        _load_nutrition_dri as common_load_nutrition_dri,
        _load_partner as common_load_partner,
        _load_training as common_load_training,
        _load_training_agent as common_load_training_agent,
    )
    from webhook_text import (
        EXEC_MENU_ITEMS as TEXT_EXEC_MENU_ITEMS,
        EXEC_MENU_TEXT as TEXT_EXEC_MENU_TEXT,
        HELP_TEXT as TEXT_HELP_TEXT,
        TRIGGER_WORDS as TEXT_TRIGGER_WORDS,
    )
except ModuleNotFoundError:
    from agents.webhook_common import (
        BASE_DIR as COMMON_BASE_DIR,
        CLASSIFIED_DIR as COMMON_CLASSIFIED_DIR,
        LINE_PUSH as COMMON_LINE_PUSH,
        LINE_REPLY as COMMON_LINE_REPLY,
        LINE_SECRET as COMMON_LINE_SECRET,
        LINE_TOKEN as COMMON_LINE_TOKEN,
        LOG_FILE as COMMON_LOG_FILE,
        NGROK_URL as COMMON_NGROK_URL,
        SENT_LOG as COMMON_SENT_LOG,
        _load_calendar as common_load_calendar,
        _load_classifier as common_load_classifier,
        _load_course_invite as common_load_course_invite,
        _load_daily_report as common_load_daily_report,
        _load_followup as common_load_followup,
        _load_market_dev as common_load_market_dev,
        _load_motivation as common_load_motivation,
        _load_nutrition_assessment as common_load_nutrition_assessment,
        _load_nutrition_dri as common_load_nutrition_dri,
        _load_partner as common_load_partner,
        _load_training as common_load_training,
        _load_training_agent as common_load_training_agent,
    )
    from agents.webhook_text import (
        EXEC_MENU_ITEMS as TEXT_EXEC_MENU_ITEMS,
        EXEC_MENU_TEXT as TEXT_EXEC_MENU_TEXT,
        HELP_TEXT as TEXT_HELP_TEXT,
        TRIGGER_WORDS as TEXT_TRIGGER_WORDS,
    )

try:
    import webhook_state as _webhook_state
    import webhook_router_helpers as _webhook_router_helpers
    import webhook_command_router as _webhook_command_router
    import webhook_web_views as _webhook_web_views
    import webhook_api_routes as _webhook_api_routes
    import webhook_line_media as _webhook_line_media
    import webhook_line_events as _webhook_line_events
    import webhook_runtime as _webhook_runtime
    import webhook_intent as _webhook_intent
except ModuleNotFoundError:
    from agents import webhook_state as _webhook_state
    from agents import webhook_router_helpers as _webhook_router_helpers
    from agents import webhook_command_router as _webhook_command_router
    from agents import webhook_web_views as _webhook_web_views
    from agents import webhook_api_routes as _webhook_api_routes
    from agents import webhook_line_media as _webhook_line_media
    from agents import webhook_line_events as _webhook_line_events
    from agents import webhook_runtime as _webhook_runtime
    from agents import webhook_intent as _webhook_intent

def _load_training():
    spec = _ilu.spec_from_file_location(
        "training_log",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "07_training_log.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_calendar():
    spec = _ilu.spec_from_file_location(
        "calendar_manager",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "08_calendar_manager.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_partner():
    spec = _ilu.spec_from_file_location(
        "partner_engagement",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "09_partner_engagement.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_market_dev():
    spec = _ilu.spec_from_file_location(
        "market_dev_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "11_market_dev_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_training_agent():
    spec = _ilu.spec_from_file_location(
        "training_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "12_training_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_followup():
    spec = _ilu.spec_from_file_location(
        "followup_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "13_followup_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_motivation():
    spec = _ilu.spec_from_file_location(
        "motivation_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "14_motivation_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_classifier():
    spec = _ilu.spec_from_file_location(
        "classifier_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "15_classifier_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_course_invite():
    spec = _ilu.spec_from_file_location(
        "course_invite_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "16_course_invite_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_daily_report():
    spec = _ilu.spec_from_file_location(
        "daily_report_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "17_daily_report_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_nutrition_dri():
    spec = _ilu.spec_from_file_location(
        "nutrition_dri_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "18_nutrition_dri_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_nutrition_assessment():
    spec = _ilu.spec_from_file_location(
        "nutrition_assessment_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "19_nutrition_assessment_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_ai_prompt_manager():
    spec = _ilu.spec_from_file_location(
        "ai_prompt_manager",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "20_ai_prompt_manager.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_ai_skill_manager():
    spec = _ilu.spec_from_file_location(
        "ai_skill_manager",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "22_ai_skill_manager.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_followup_suggestion():
    spec = _ilu.spec_from_file_location(
        "followup_suggestion_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "21_followup_suggestion_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

BASE_DIR        = Path(r"C:\Users\user\claude AI_Agent")
SENT_LOG        = BASE_DIR / "output" / "sent_log.json"
LOG_FILE        = BASE_DIR / "logs" / "webhook_log.txt"
CLASSIFIED_DIR  = BASE_DIR / "output" / "classified"

LINE_TOKEN    = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_SECRET   = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_REPLY    = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH     = "https://api.line.me/v2/bot/message/push"
NGROK_URL     = os.getenv("NGROK_URL", "").rstrip("/")

# 觸發詞設定（訊息必須以此開頭才會被處理）
TRIGGER_WORDS = ["小幫手", "@Yisheng助理", "@Yisheng", "/yisheng"]

HELP_TEXT = """\
📋 Yisheng 助理 — 可用指令
觸發詞：小幫手 / @Yisheng / /yisheng
══════════════════════
📚 培訓記錄
  整理
    → 整理今天已歸檔的逐字稿
  整理 YYYYMMDD
    → 整理指定日期的逐字稿
  整理 [逐字稿內容]
    → 直接附上逐字稿一起整理
  再次整理
    → 強制覆蓋重新整理今天記錄
  再次整理 [逐字稿]
    → 強制覆蓋並重新整理

🔍 查詢記錄
  MTG-YYYYMMDD
    → 查詢指定日期的培訓總結
    範例：MTG-20260329

📷 傳送圖片
  → 自動歸檔至今日培訓資料夾

❓ 說明
  指令集 / 所有指令 / 查詢 / 指令 / help / ?
    → 顯示所有可用指令
══════════════════════
完整記錄網頁版：
""" + (NGROK_URL + "/summary/YYYYMMDD" if NGROK_URL else "（尚未設定 NGROK_URL）")

HELP_TEXT += """

🗓️ 行事曆
  查詢行事曆
  查詢過往行事曆
  查詢行事曆 YYYY-MM-DD
  查詢行事曆 YYYY-MM-DD 到 YYYY-MM-DD
  查詢全部行事曆
  新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註
  修改行事曆 EVT-xxxx YYYY-MM-DD [HH:MM] 標題 | 備註
  刪除行事曆 EVT-xxxx

📷 行事曆圖片
  上傳圖片/檔案後會先進待歸檔目錄，再回傳數字選單
  回覆「13」可執行行事曆圖檔整理
"""

HELP_TEXT += """

📂 歸類模式（Content Router）
  上傳圖片 / 音檔 / 影片 / 檔案
    → 先進待歸檔目錄，系統回傳數字選單
    → 直接回數字即可執行，例如回 7 = 第 7 個歸檔項目
  待歸檔 / 查詢待歸檔
    → 重新查看目前待歸檔選單
  歸類模式
    → 查詢目前模式與可用模式清單
  歸類模式 [模式名稱] [日期]
    → 設定歸類模式，可加日期指定歸檔目錄
    日期可輸入：今日 / 昨日 / 今天 / 昨天 / YYYY-MM-DD / YYYYMMDD
    可用：會議記錄 / 行事曆 / 夥伴跟進 / 市場開發 / 培訓資料 / 一般歸檔
         整理會議心得 / 歸檔會議紀錄 / 歸檔行動紀錄 / 歸檔文件
         421故事歸檔 / 課程文宣歸檔
    例：歸類模式 培訓資料 昨日
        歸類模式 會議記錄 2026-03-28
  歸類模式 [人員名稱] [模式名稱] [日期]
    → 設定人員專屬歸類（如：歸類模式 建德 會議記錄 昨日）
  關閉歸類模式
    → 回到自動模式
  查詢歸檔
    → 列出所有人員的歸檔記錄（含網頁瀏覽連結）
  查詢歸檔 [人員名稱]
    → 查詢指定人員的所有歸檔（含網頁連結可查看圖片/檔案）

  在歸類模式下，不需觸發詞，直接傳：
    🖼️ 圖片 / 🎤 音檔 / 🎬 影片 / 📄 檔案 → 先暫存並回傳歸檔選單
    💬 文字 → 記入今日備註（行事曆/夥伴跟進模式會嘗試解析）
"""

HELP_TEXT += """

🎯 市場開發（新系統）
  新增潛在家人 姓名|職業|接觸管道|備註
    → 新增至本地清單並立即 AI 評分 + 生成三種接觸話術
  查詢潛在家人 [姓名]
    → 列出所有潛在家人（可加姓名篩選）
  潛在家人資料 姓名
    → 設定歸檔模式，後續上傳的照片/檔案自動歸入該人員資料夾

📚 培訓系統（新系統）
  培訓 夥伴名
    → 查詢該夥伴培訓進度（Day 1/3/5/7/14/30）

📋 夥伴跟進（新系統）
  跟進報告
    → 即時生成🔴🟡🟢風險報告 + 關懷草稿

💪 夥伴激勵（新系統）
  激勵 夥伴名 [情境說明]
    → 生成個人化鼓勵文 + 今日小目標
  里程碑 夥伴名 [成就描述]
    → 生成慶賀訊息 + 更新里程碑紀錄
"""

HELP_TEXT += """

🥗 營養評估系統（衛福部第八版 DRI）
  查詢營養素標準 性別 年齡 [餐別]
    → 查詢指定性別年齡的每日/每餐攝取參考量
    範例：查詢營養素標準 女 30 午餐
  營養素運作原理 營養素名稱
    → 查看該營養素的功能機制與長期缺乏警訊
    範例：營養素運作原理 維生素D
  列出營養素
    → 列出所有可查詢的營養素
  下載營養素標準
    → 從衛福部網站下載最新 PDF 資料
  開始飲食評估 性別 年齡
    → 開始今日飲食評估，進入接收照片模式
    範例：開始飲食評估 男 35
  設定餐別 早餐/午餐/晚餐
    → 指定下一張上傳照片的餐別
  （上傳餐點照片 1-3 張）
    → 在評估模式下上傳，系統自動收集
  評估飲食 喝水量XXXml
    → 觸發 AI 分析所有餐點照片，生成報告並寄至 Email
    範例：評估飲食 喝水量1500ml
  飲食評估狀態
    → 查看目前評估進度
  清除飲食評估
    → 取消並清除本次評估記錄
"""

HELP_TEXT += """

🎓 課程會議邀約
  新增課程會議 YYYY-MM-DD [HH:MM] 標題|地點|說明
    → 手動新增課程會議
  查詢課程會議
    → 查詢接下來的所有課程
  刪除課程會議 COURSE-XXXX
    → 刪除指定課程會議
  從行事曆加入課程 [關鍵字]
    → 從行事曆匯入課程活動（可加關鍵字篩選）
  新增課程文宣 標題|內文
    → 新增課程宣傳文案
  查詢課程文宣
    → 列出所有課程文宣
  優化課程文宣 PROMO-XXXX
    → 透過 AI 優化指定文宣
  邀約文宣 潛在家人 [姓名]
    → 透過 AI 產生潛在家人課程邀約（不填姓名＝通用邀約）
  邀約文宣 跟進夥伴 [姓名]
    → 先選 A/B/C 分類，再選夥伴，再選會議，最後產生邀約文宣
  查詢已產生的今日之後會議邀約文宣
    → 查詢所有未過期的已產生邀約文宣
  修改已產生的今日之後會議邀約文宣 COURSE-XXXX | 姓名 | 新內容
    → 修改指定邀約文宣
"""

HELP_TEXT += """

🤝 夥伴經營
  新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類
  更新夥伴 姓名 | 層級 | 近況 | 下次跟進日期 | 聯絡資訊 | 備註 | 類型 | 編號 | 合夥人 | 推薦人 | 到期日 | 年月 | 一年內新上獎銜 | 首次獎金% | 現金抵用券 | 購物積點 | 優惠券 | 本月購貨 | 上月購貨 | 前2月購貨 | 前3月購貨 | 分類
  邀約夥伴 姓名 | 活動名稱 | 下次跟進日期 | 備註
  跟進夥伴 姓名 | 狀態 | 下次跟進日期 | 備註
  激勵夥伴 姓名
  查詢夥伴
  查詢待跟進夥伴
  查詢夥伴 姓名
  刪除夥伴 姓名
  匯入夥伴名單
  分類建議：A / B / C
"""

# ============================================================
# 📋 執行選單
# ============================================================

EXEC_MENU_ITEMS = {
    1:  {"label": "新增潛在家人",       "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 新增潛在家人 姓名|職業|管道|備註\n\n查詢名單：小幫手 查詢潛在家人\n上傳照片：小幫手 潛在家人資料 姓名"},
    32: {"label": "查詢潛在家人",       "cmd": "查詢潛在家人",  "prompt": None},
    33: {"label": "加入潛在家人資訊",   "prospect_file": True,  "prompt": None},
    2:  {"label": "查詢培訓進度",       "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 培訓 夥伴名"},
    3:  {"label": "跟進報告",           "cmd": "跟進報告",       "prompt": None},
    4:  {"label": "激勵夥伴",           "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 激勵 夥伴名 [情境說明]"},
    5:  {"label": "里程碑記錄",         "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 里程碑 夥伴名 [成就描述]"},
    6:  {"label": "查詢所有夥伴",       "cmd": "查詢夥伴",       "prompt": None},
    7:  {"label": "查詢待跟進夥伴",     "cmd": "查詢待跟進夥伴", "prompt": None},
    8:  {"label": "查詢今日行事曆",     "cmd": "查詢行事曆",     "prompt": None},
    9:  {"label": "查詢過往行事曆",     "cmd": "查詢過往行事曆", "prompt": None},
    10: {"label": "新增行事曆事件",     "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註"},
    11: {"label": "查詢目前歸類模式",   "cmd": "歸類模式",       "prompt": None},
    12: {"label": "設定歸類模式",       "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 歸類模式 [模式名稱]\n"
                   "可用模式：會議記錄 / 行事曆 / 夥伴跟進 / 市場開發\n"
                   "培訓資料 / 一般歸檔 / 整理會議心得\n"
                   "歸檔會議紀錄 / 歸檔行動紀錄 / 歸檔文件\n"
                   "421故事歸檔 / 課程文宣歸檔"},
    13: {"label": "設定人員＋歸類模式", "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 歸類模式 [人員名稱] [模式名稱]"},
    14: {"label": "關閉歸類模式",       "cmd": "關閉歸類模式",   "prompt": None},
    15: {"label": "查詢所有歸檔",       "cmd": "查詢歸檔",       "prompt": None},
    16: {"label": "查詢指定人員歸檔",   "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 查詢歸檔 [人員名稱]"},
    17: {"label": "整理今日培訓記錄",   "cmd": "整理",           "prompt": None},
    18: {"label": "新增夥伴",           "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類"},
    19: {"label": "跟進夥伴",           "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 跟進夥伴 姓名 | 狀態 | 下次跟進日期 | 備註"},
    20: {"label": "顯示所有指令",       "cmd": "指令集",         "prompt": None},
    # 安麗產品歸檔（不綁定人員）
    21: {"label": "💊 營養保健歸檔 (Nutrilite)", "cmd": "營養保健歸檔", "prompt": None, "reset_person": True},
    22: {"label": "💄 美容保養歸檔 (Artistry)",  "cmd": "美容保養歸檔", "prompt": None, "reset_person": True},
    23: {"label": "🧹 居家清潔歸檔 (Home)","cmd": "居家清潔歸檔", "prompt": None, "reset_person": True},
    24: {"label": "🪥 個人護理歸檔 (Glister)",   "cmd": "個人護理歸檔", "prompt": None, "reset_person": True},
    25: {"label": "🍳 廚具與生活用品歸檔",        "cmd": "廚具生活歸檔", "prompt": None, "reset_person": True},
    26: {"label": "💧 空氣與水處理設備歸檔",      "cmd": "空水設備歸檔", "prompt": None, "reset_person": True},
    27: {"label": "⚖️ 體重管理與運動營養歸檔",    "cmd": "體重管理歸檔", "prompt": None, "reset_person": True},
    28: {"label": "🌸 香氛與個人風格歸檔",        "cmd": "香氛風格歸檔", "prompt": None, "reset_person": True},
    29: {"label": "🛠️ 事業工具與教育系統歸檔",    "cmd": "事業工具歸檔", "prompt": None, "reset_person": True},
    # 故事分類
    30: {"label": "👤 人物故事歸檔",              "cmd": None, "prompt": None, "ask_person": "人物故事歸檔"},
    31: {"label": "📖 產品故事歸檔",              "cmd": "產品故事歸檔", "prompt": None, "reset_person": True},
    # 課程會議邀約
    34: {"label": "查詢課程會議",     "cmd": "查詢課程會議",  "prompt": None},
    35: {"label": "新增課程會議",     "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 新增課程會議 YYYY-MM-DD HH:MM 標題|地點|說明\n\n範例：\n小幫手 新增課程會議 2026-04-10 19:00 四月OPP說明會|台中大里店|歡迎帶朋友"},
    36: {"label": "從行事曆加入課程", "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 從行事曆加入課程 [關鍵字]\n\n範例：\n小幫手 從行事曆加入課程 OPP"},
    37: {"label": "刪除課程會議",     "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 刪除課程會議 COURSE-XXXX\n先查詢：小幫手 查詢課程會議"},
    38: {"label": "查詢課程文宣",     "cmd": "查詢課程文宣",  "prompt": None},
    39: {"label": "新增課程文宣",     "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 新增課程文宣 標題|內文"},
    40: {"label": "優化課程文宣",     "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 優化課程文宣 PROMO-XXXX\n先查詢：小幫手 查詢課程文宣"},
    41: {"label": "邀約文宣－潛在家人", "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 邀約文宣 潛在家人 [姓名]\n\n不填姓名＝通用邀約\n範例：\n小幫手 邀約文宣 潛在家人 Amy"},
    42: {"label": "邀約文宣－跟進夥伴", "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 邀約文宣 跟進夥伴 [姓名]\n\n不填姓名＝通用邀約\n範例：\n小幫手 邀約文宣 跟進夥伴 建德"},
    43: {"label": "查詢已產生的邀約文宣", "cmd": "查詢已產生的今日之後會議邀約文宣", "prompt": None},
    44: {"label": "修改已產生的邀約文宣", "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 修改已產生的今日之後會議邀約文宣 COURSE-XXXX | 姓名 | 新內容"},
    45: {"label": "📧 寄送每日報告",    "cmd": "寄送每日報告",  "prompt": None},
    # 營養評估
    46: {"label": "📊 查詢營養素標準",  "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 查詢營養素標準 男 30\n（可加餐別：早餐/午餐/晚餐）"},
    47: {"label": "🔬 營養素運作原理",  "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 營養素運作原理 鈣\n可查：鈣/鐵/維生素D/維生素C/蛋白質 等"},
    48: {"label": "📋 列出所有營養素",  "cmd": "列出營養素",   "prompt": None},
    49: {"label": "📥 更新官方營養素標準", "cmd": "下載營養素標準", "prompt": None},
    50: {"label": "🍽️ 開始飲食評估",   "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 開始飲食評估 男 30\n（填寫性別：男/女，年齡）\n然後上傳餐點照片"},
    51: {"label": "🥗 執行飲食評估",    "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 評估飲食 喝水量1500ml\n（先上傳餐點照片後再執行）"},
    52: {"label": "📷 設定下一張餐別",  "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 設定餐別 早餐\n（可選：早餐/午餐/晚餐/宵夜）"},
    53: {"label": "📈 飲食評估狀態",    "cmd": "飲食評估狀態", "prompt": None},
    54: {"label": "🗑️ 清除飲食評估",   "cmd": "清除飲食評估", "prompt": None},
    55: {"label": "🏷️ 設定歸檔對象",   "cmd": None,
         "prompt": "請複製後修改再送出：\n小幫手 設定評估對象 王小明\n（照片與報告將歸入 classified/王小明/飲食評估/）"},
}

EXEC_MENU_TEXT = """\
📋 小幫手執行選單
══════════════════
🎯 市場開發
  1. 新增潛在家人
 32. 查詢潛在家人 ▶
 33. 加入潛在家人資訊 ▶

📚 培訓系統
  2. 查詢培訓進度

🤝 夥伴陪伴
  3. 跟進報告 ▶
  4. 激勵夥伴
  5. 里程碑記錄
  6. 查詢所有夥伴 ▶
  7. 查詢待跟進夥伴 ▶
 18. 新增夥伴
 19. 跟進夥伴

🗓️ 行事曆
  8. 查詢今日行事曆 ▶
  9. 查詢過往行事曆 ▶
 10. 新增行事曆事件

📂 歸類模式
 11. 查詢目前歸類模式 ▶
 12. 設定歸類模式
 13. 設定人員＋歸類模式
 14. 關閉歸類模式 ▶
 15. 查詢所有歸檔 ▶
 16. 查詢指定人員歸檔

📖 培訓記錄
 17. 整理今日培訓記錄 ▶

❓ 說明
 20. 顯示所有指令 ▶

🛍️ 安麗產品歸檔（設定模式）
 21. 💊 營養保健 (Nutrilite) ▶
 22. 💄 美容保養 (Artistry) ▶
 23. 🧹 居家清潔 (Home) ▶
 24. 🪥 個人護理 (Glister) ▶
 25. 🍳 廚具與生活用品 ▶
 26. 💧 空氣與水處理設備 ▶
 27. ⚖️ 體重管理與運動營養 ▶
 28. 🌸 香氛與個人風格 ▶
 29. 🛠️ 事業工具與教育系統 ▶

📝 故事分類
 30. 👤 人物故事歸檔 ▶
 31. 📖 產品故事歸檔 ▶

🎓 課程會議邀約
 34. 查詢課程會議 ▶
 35. 新增課程會議
 36. 從行事曆加入課程
 37. 刪除課程會議
 38. 查詢課程文宣 ▶
 39. 新增課程文宣
 40. 優化課程文宣（AI）
 41. 邀約文宣－潛在家人（AI）
 42. 邀約文宣－跟進夥伴（AI）
 43. 查詢已產生的邀約文宣 ▶
 44. 修改已產生的邀約文宣

📧 每日報告
 45. 寄送每日報告 ▶

🥗 營養評估（衛福部第八版 DRI）
 46. 查詢營養素標準
 47. 營養素運作原理
 48. 列出所有營養素 ▶
 49. 更新官方營養素標準 ▶
 50. 開始飲食評估
 51. 執行飲食評估（AI分析＋寄報告）
 52. 設定下一張餐別
 53. 飲食評估狀態 ▶
 54. 清除飲食評估 ▶
 55. 設定歸檔對象

══════════════════
▶ 直接執行　其餘顯示輸入範本
回覆數字即可　NA = 取消返回"""

# Use extracted modules as the source of truth during the refactor.
BASE_DIR = COMMON_BASE_DIR
SENT_LOG = COMMON_SENT_LOG
LOG_FILE = COMMON_LOG_FILE
CLASSIFIED_DIR = COMMON_CLASSIFIED_DIR
LINE_TOKEN = COMMON_LINE_TOKEN
LINE_SECRET = COMMON_LINE_SECRET
LINE_REPLY = COMMON_LINE_REPLY
LINE_PUSH = COMMON_LINE_PUSH
NGROK_URL = COMMON_NGROK_URL

TRIGGER_WORDS = TEXT_TRIGGER_WORDS
HELP_TEXT = TEXT_HELP_TEXT
EXEC_MENU_ITEMS = TEXT_EXEC_MENU_ITEMS
EXEC_MENU_TEXT = TEXT_EXEC_MENU_TEXT

EXEC_MENU_ITEMS[79] = {"label": "查詢AI技能", "cmd": "查詢AI技能", "prompt": None}
EXEC_MENU_ITEMS[80] = {"label": "修改AI技能", "cmd": None, "prompt": "請輸入：更新AI技能 key | 新內容"}
EXEC_MENU_TEXT += "\n\n🤖 AI 技能管理\n 79. 查詢AI技能 ▶\n 80. 修改AI技能"
HELP_TEXT += "\n\n🤖 AI 技能管理\n  查詢AI技能\n  查詢AI技能 key\n  更新AI技能 key | 新內容\n"

_load_training = common_load_training
_load_calendar = common_load_calendar
_load_partner = common_load_partner
_load_market_dev = common_load_market_dev
_load_training_agent = common_load_training_agent
_load_followup = common_load_followup
_load_motivation = common_load_motivation
_load_classifier = common_load_classifier
_load_course_invite = common_load_course_invite
_load_daily_report = common_load_daily_report
_load_nutrition_dri = common_load_nutrition_dri
_load_nutrition_assessment = common_load_nutrition_assessment

# 追蹤哪些 scope 正在等待執行選單輸入（in-memory，重啟後清除）
_exec_menu_active: dict = {}
# 追蹤飲食評估 Session（scope_id → {gender, age, photos, water_ml, awaiting_photo}）
_nutrition_sessions: dict = {}
# 追蹤哪些 scope 正在等待輸入人物名稱以設定模式（scope_id → mode_name）
_awaiting_person_for_mode: dict = {}
# 追蹤哪些 scope 已送出 prompt 等待使用者填入後回傳（scope_id → True）
_awaiting_exec_input: dict = {}
# 追蹤哪些 scope 正在等待潛在家人編號選擇（scope_id → list[dict]）
_awaiting_prospect_selection: dict = {}
# 追蹤哪些 scope 正在等待選擇要歸檔的潛在家人（scope_id → list[dict]）
_awaiting_prospect_file: dict = {}
# 追蹤哪些 scope 正在等待邀約組合編號選擇（scope_id → list[{name, role, meeting}]）
_awaiting_invite_selection: dict = {}
# 跟進夥伴邀約三段式：先選分類（scope_id → True）
_awaiting_partner_invite_category: dict = {}
# 跟進夥伴邀約三段式：再選人（scope_id → list[dict]）
_awaiting_partner_invite_person: dict = {}
# 跟進夥伴邀約三段式：最後選會議（scope_id → {name, meetings})
_awaiting_partner_invite_meeting: dict = {}
# 已產生邀約文宣管理：先選文宣（scope_id → list[dict]）
_awaiting_invite_manage_select: dict = {}
# 已產生邀約文宣管理：再選操作（scope_id → dict）
_awaiting_invite_manage_action: dict = {}
# 已產生邀約文宣管理：等待輸入新內容（scope_id → dict）
_awaiting_invite_manage_edit: dict = {}
# 網頁邀約組合清單暫存（"web" → list[{name, role, meeting}]）
_web_invite_combos: dict = {}
_web_partner_invite_state: dict = {}
_web_invite_manage_state: dict = {}

# Shared state backing store for refactor modules.
_exec_menu_active = _webhook_state._exec_menu_active
_nutrition_sessions = _webhook_state._nutrition_sessions
_awaiting_person_for_mode = _webhook_state._awaiting_person_for_mode
_awaiting_exec_input = _webhook_state._awaiting_exec_input
_awaiting_prospect_selection = _webhook_state._awaiting_prospect_selection
_awaiting_prospect_file = _webhook_state._awaiting_prospect_file
_awaiting_invite_selection = _webhook_state._awaiting_invite_selection
_awaiting_partner_invite_category = _webhook_state._awaiting_partner_invite_category
_awaiting_partner_invite_person = _webhook_state._awaiting_partner_invite_person
_awaiting_partner_invite_meeting = _webhook_state._awaiting_partner_invite_meeting
_awaiting_invite_manage_select = _webhook_state._awaiting_invite_manage_select
_awaiting_invite_manage_action = _webhook_state._awaiting_invite_manage_action
_awaiting_invite_manage_edit = _webhook_state._awaiting_invite_manage_edit
_awaiting_promo_optimize_apply = _webhook_state._awaiting_promo_optimize_apply
_awaiting_partner_voice_add = _webhook_state._awaiting_partner_voice_add
_web_invite_combos = _webhook_state._web_invite_combos
_web_partner_invite_state = _webhook_state._web_partner_invite_state
_web_invite_manage_state = _webhook_state._web_invite_manage_state
_web_promo_optimize_state = _webhook_state._web_promo_optimize_state


def _format_prospect_detail(r: dict) -> str:
    import json as _json
    star = "⭐" * int(r["AI評分"]) if r.get("AI評分", "").isdigit() else ""
    lines = [
        f"👤 {r.get('姓名','')}　{r.get('職業','')}",
        f"AI評分：{r.get('AI評分','')} {star}　需求：{r.get('需求標籤','')}",
        f"管道：{r.get('接觸管道','')}",
        f"狀態：{r.get('接觸狀態','')}　下次跟進：{r.get('下次跟進日','')}",
    ]
    if r.get("電話"):
        lines.append(f"📱 電話：{r.get('電話','')}")
    if r.get("地區") or r.get("地址"):
        lines.append(f"📍 地區：{r.get('地區','')}　地址：{r.get('地址','')}")
    if r.get("備註"):
        lines.append(f"備註：{r.get('備註','')}")
    if r.get("使用產品"):
        lines.append(f"🛍️ 使用產品：{r.get('使用產品','')}")
    if r.get("淨水器型號"):
        lines.append(f"💧 淨水器：{r.get('淨水器型號','')}")
    if r.get("濾心上次換"):
        lines.append(f"   上次換濾心：{r.get('濾心上次換','')}")
    if r.get("濾心下次換"):
        lines.append(f"   下次換濾心：{r.get('濾心下次換','')}")
    exp_raw = r.get("體驗記錄", "")
    if exp_raw:
        try:
            records = _json.loads(exp_raw)
            if records:
                lines.append(f"\n📋 體驗記錄（共 {len(records)} 筆）：")
                for rec in records[-5:]:
                    lines.append(f"  • {rec.get('日期','')} {rec.get('產品','')} {rec.get('備註','')}")
        except Exception:
            pass
    for key, label in [("話術_健康型", "🌿 健康型"), ("話術_收入型", "💰 收入型"), ("話術_好奇型", "🤔 好奇型")]:
        val = r.get(key, "")
        if val:
            lines.append(f"{label}：{val}")
    return "\n".join(lines)


def _load_partner_rows() -> list[dict]:
    partners_json = BASE_DIR / "output" / "partners" / "partners.json"
    if not partners_json.exists():
        return []
    try:
        with open(partners_json, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _partners_by_category(category: str) -> list[dict]:
    category = (category or "").strip().upper()
    rows = [p for p in _load_partner_rows() if (p.get("category", "") or "").upper() == category and p.get("name")]
    rows.sort(key=lambda p: (p.get("level", ""), p.get("name", "")))
    return rows


def _partner_category_menu() -> str:
    return (
        "📋 請先選擇夥伴分類屬性\n"
        "1. A 類：持續有使用產品、有積分額、且有聽過鐘老師演講\n"
        "2. B 類：偶爾使用產品，或有聽過鐘老師演講\n"
        "3. C 類：即將開始了解，或即將聽鐘老師演講\n\n"
        "請輸入 1、2、3 或 A、B、C，NA 取消"
    )


def _normalize_partner_category_choice(raw: str) -> str:
    raw = (raw or "").strip().upper()
    return {"1": "A", "2": "B", "3": "C", "A": "A", "B": "B", "C": "C"}.get(raw, "")


def _format_partner_choice_menu(category: str, people: list[dict]) -> str:
    lines = [f"📋 {category} 類夥伴清單（共 {len(people)} 位）", "輸入編號選人，NA 取消", ""]
    for i, p in enumerate(people[:30], 1):
        line = f"{i}. {p.get('name','')}"
        if p.get("level"):
            line += f"｜層級{p.get('level','')}"
        if p.get("stage"):
            line += f"｜{p.get('stage','')}"
        lines.append(line)
    return "\n".join(lines)


def _format_meeting_choice_menu(name: str, meetings: list[dict]) -> str:
    lines = [f"📋 {name} 的可邀約會議（共 {len(meetings)} 場）", "輸入編號產生邀約文宣，NA 取消", ""]
    for i, m in enumerate(meetings, 1):
        when = m["date"] + (f" {m['time']}" if m.get("time") else "")
        lines.append(f"{i}. {m['title']}（{when}）")
    return "\n".join(lines)


def _format_invite_manage_list(rows: list[dict]) -> str:
    if not rows:
        return "目前沒有今日之後已產生的會議邀約文宣。"
    lines = ["📨 今日之後已產生的會議邀約文宣：", "輸入編號管理該筆文宣，NA 取消", ""]
    for i, rec in enumerate(rows, 1):
        meeting = rec["meeting"]
        when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
        lines.append(f"{i}. {meeting['id']}｜{rec.get('name','')}｜{meeting['title']}｜{when}")
    return "\n".join(lines)


def _format_invite_manage_actions(rec: dict) -> str:
    meeting = rec["meeting"]
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    return (
        "🛠️ 邀約文宣管理\n"
        f"{meeting['id']}｜{rec.get('name','')}｜{meeting['title']}｜{when}\n\n"
        "1. 修改已產生文宣\n"
        "2. 強制重新產生\n\n"
        "請輸入 1 或 2，NA 取消"
    )


def _format_invite_edit_confirm(rec: dict) -> str:
    meeting = rec["meeting"]
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    content = (rec.get("content", "") or "").strip()
    if not content:
        content = "（目前沒有已產生內容）"
    return (
        "📝 是否修改這份邀約文宣？\n"
        f"{meeting['id']}｜{rec.get('name','')}｜{meeting['title']}｜{when}\n\n"
        f"目前內容：\n{content}\n\n"
        "1. 確定修改\n"
        "2. 取消\n\n"
        "請輸入 1 或 2，NA 取消"
    )


def _looks_like_explicit_command(msg: str) -> bool:
    text = (msg or "").strip()
    if not text:
        return False
    prefixes = (
        "查詢", "新增", "更新", "修改", "刪除", "整理", "再次整理",
        "邀約文宣", "邀約夥伴", "跟進夥伴", "激勵夥伴", "里程碑", "培訓",
        "歸類模式", "關閉歸類模式", "潛在家人資料", "新增體驗", "換濾心",
        "執行選單", "指令集", "課程", "MTG-",
    )
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False


# Router helpers extracted for the webhook refactor.
_load_partner_rows = lambda: _webhook_router_helpers.load_partner_rows(BASE_DIR)
_partners_by_category = lambda category: _webhook_router_helpers.partners_by_category(BASE_DIR, category)
_partner_category_menu = _webhook_router_helpers.partner_category_menu
_normalize_partner_category_choice = _webhook_router_helpers.normalize_partner_category_choice
_format_partner_choice_menu = _webhook_router_helpers.format_partner_choice_menu
_format_meeting_choice_menu = _webhook_router_helpers.format_meeting_choice_menu
_format_invite_manage_list = _webhook_router_helpers.format_invite_manage_list
_format_invite_manage_actions = _webhook_router_helpers.format_invite_manage_actions
_format_invite_view = _webhook_router_helpers.format_invite_view
_format_invite_edit_confirm = _webhook_router_helpers.format_invite_edit_confirm
_looks_like_explicit_command = _webhook_router_helpers.looks_like_explicit_command

app = Flask(__name__)

def extract_trigger(msg: str) -> str | None:
    return _webhook_runtime.extract_trigger(msg, TRIGGER_WORDS)


def log(msg: str):
    _webhook_runtime.log_message(msg, LOG_FILE)


_webhook_intent.configure(SENT_LOG, log)


# ============================================================
# LINE helper wrappers
# ============================================================

def verify_signature(body: bytes, signature: str) -> bool:
    return _webhook_runtime.verify_signature(body, signature, LINE_SECRET)


# ============================================================
# Web API route registration
# ============================================================

def analyze_intent(user_message: str) -> dict:
    return _webhook_intent.analyze_intent(user_message)


# ============================================================
# LINE event dispatcher
# ============================================================


def reply_message(reply_token: str, message: str):
    _webhook_runtime.reply_message(reply_token, message, LINE_TOKEN, LINE_REPLY, log)


def push_message(user_id: str, message: str):
    _webhook_runtime.push_message(user_id, message, LINE_TOKEN, LINE_PUSH, log)


def schedule_pending_menu(clf, scope_id: str, push_target: str, delay_sec: int = 3):
    _webhook_runtime.schedule_pending_menu(clf, scope_id, push_target, push_message, delay_sec)


# ============================================================
# Webhook entry
# ============================================================

def _download_line_content(msg_id: str, timeout: int = 30) -> bytes | None:
    return _webhook_runtime.download_line_content(msg_id, LINE_TOKEN, timeout)


def handle_image_message(event: dict, mode_info: dict = None, clf=None):
    return _webhook_line_media.handle_image_message(
        event,
        mode_info,
        clf,
        download_line_content=_download_line_content,
        reply_message=reply_message,
        push_message=push_message,
        nutrition_sessions=_nutrition_sessions,
        load_nutrition_assessment=_load_nutrition_assessment,
        load_training=_load_training,
        schedule_pending_menu=schedule_pending_menu,
    )


def handle_audio_message(event: dict, mode_info: dict, clf):
    return _webhook_line_media.handle_audio_message(
        event,
        mode_info,
        clf,
        download_line_content=_download_line_content,
        reply_message=reply_message,
        schedule_pending_menu=schedule_pending_menu,
        awaiting_partner_voice_add=_awaiting_partner_voice_add,
        load_partner=_load_partner,
    )


def handle_video_message(event: dict, mode_info: dict, clf):
    return _webhook_line_media.handle_video_message(
        event,
        mode_info,
        clf,
        download_line_content=_download_line_content,
        reply_message=reply_message,
        schedule_pending_menu=schedule_pending_menu,
    )


def handle_file_message(event: dict, mode_info: dict, clf):
    return _webhook_line_media.handle_file_message(
        event,
        mode_info,
        clf,
        download_line_content=_download_line_content,
        reply_message=reply_message,
        schedule_pending_menu=schedule_pending_menu,
    )


def handle_training_command(user_msg: str, reply_token: str,
                            user_id: str = "", group_id: str = ""):
    """
    培訓記錄指令判斷：
      整理 / 整理YYYYMMDD → 產生當日或指定日期總結（背景執行，Push 到群組）
      再次整理            → 強制覆蓋重新整理
      MTG-YYYYMMDD        → 查詢已有總結（立即 Reply）
      [長文字 >100字]     → 視為逐字稿直接整理
    """
    tl = _load_training()
    cal = _load_calendar()
    partner = _load_partner()
    msg = user_msg.strip()
    push_target = group_id or user_id   # 優先推送回群組
    if msg == "查詢已產生的今日之後會議邀約文宣":
        try:
            course = _load_course_invite()
            rows = course.list_upcoming_invites(today_only_after=True)
            if rows:
                _awaiting_invite_manage_select[group_id or user_id] = rows
            reply_message(reply_token, _format_invite_manage_list(rows))
        except Exception as e:
            reply_message(reply_token, f"✗ 查詢邀約文宣失敗：{e}")
        return True
    if msg.startswith("優化課程文宣"):
        return False
    routed = _webhook_command_router.handle_line_command(
        msg=msg,
        reply_token=reply_token,
        push_target=push_target,
        sessions=_nutrition_sessions,
        reply_message=reply_message,
        push_message=push_message,
        load_calendar=_load_calendar,
        load_partner=_load_partner,
        load_classifier=_load_classifier,
        load_market_dev=_load_market_dev,
        load_course_invite=_load_course_invite,
        load_daily_report=_load_daily_report,
        load_nutrition_dri=_load_nutrition_dri,
        load_nutrition_assessment=_load_nutrition_assessment,
        load_ai_prompt_manager=_load_ai_prompt_manager,
        load_ai_skill_manager=_load_ai_skill_manager,
        load_followup_suggestion=_load_followup_suggestion,
        load_training_agent=_load_training_agent,
        load_followup=_load_followup,
        load_motivation=_load_motivation,
    )
    if routed:
        return True

    # ── 歸類模式指令（優先處理）──────────────────────────────
    if msg.startswith("歸類模式") or msg == "關閉歸類模式":
        try:
            clf_mod = _load_classifier()
            result = clf_mod.ClassifierAgent().handle_command(msg)
            if result:
                reply_message(reply_token, result)
                return True
        except Exception as e:
            reply_message(reply_token, f"✗ 歸類模式設定失敗：{e}")
            return True

    # === 新系統：市場開發 / 培訓 / 跟進 / 激勵 ===

    if msg.startswith("潛在家人資料"):
        # 設定歸類模式為「市場開發」並指定人員，後續上傳的圖片/檔案歸入該人員資料夾
        person_name = msg.replace("潛在家人資料", "", 1).strip()
        if not person_name:
            reply_message(reply_token, "⚠️ 格式：小幫手 潛在家人資料 姓名\n設定後直接上傳照片或檔案即可歸檔")
            return True
        try:
            clf_mod = _load_classifier()
            result = clf_mod.ClassifierAgent().set_mode("市場開發", person_name)
            reply_message(reply_token, result + "\n\n📸 現在直接上傳照片或檔案，會自動歸入該潛在家人資料夾。")
        except Exception as e:
            reply_message(reply_token, f"✗ 設定失敗：{e}")
        return True

    if msg.startswith("更新潛在家人"):
        # 格式：更新潛在家人 姓名|欄位:值|欄位:值
        # 欄位：電話 地區 地址 接觸狀態 下次跟進日 使用產品 淨水器型號 備註
        content = msg.replace("更新潛在家人", "", 1).strip()
        parts = [p.strip() for p in content.split("|")]
        name = parts[0] if parts else ""
        if not name:
            reply_message(reply_token,
                "⚠️ 格式：\n小幫手 更新潛在家人 姓名|欄位:值|欄位:值\n\n"
                "可用欄位：電話、地區、地址、接觸狀態、下次跟進日、使用產品、淨水器型號、備註\n\n"
                "範例：\n小幫手 更新潛在家人 Amy|地區:台中西屯|地址:民生路123號|電話:0912345678")
            return True
        try:
            fields = {}
            for p in parts[1:]:
                if ":" in p:
                    k, v = p.split(":", 1)
                    fields[k.strip()] = v.strip()
            if not fields:
                reply_message(reply_token, "⚠️ 請提供要更新的欄位，格式：欄位:值")
                return True
            market = _load_market_dev()
            result = market.MarketDevAgent().update_prospect_fields(name, fields)
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 更新失敗：{e}")
        return True

    if msg.startswith("新增體驗"):
        # 格式：新增體驗 姓名|產品名稱|備註（選填）
        content = msg.replace("新增體驗", "", 1).strip()
        parts = [p.strip() for p in content.split("|")]
        name    = parts[0] if len(parts) > 0 else ""
        product = parts[1] if len(parts) > 1 else ""
        note    = parts[2] if len(parts) > 2 else ""
        if not name or not product:
            reply_message(reply_token,
                "⚠️ 格式：\n小幫手 新增體驗 姓名|產品名稱|備註（選填）\n\n"
                "範例：\n小幫手 新增體驗 Amy|益生菌|每天早上服用2顆")
            return True
        try:
            market = _load_market_dev()
            result = market.MarketDevAgent().add_experience(name, product, note=note)
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 新增體驗記錄失敗：{e}")
        return True

    if msg.startswith("換濾心"):
        # 格式：換濾心 姓名|上次日期|下次日期
        content = msg.replace("換濾心", "", 1).strip()
        parts = [p.strip() for p in content.split("|")]
        name       = parts[0] if len(parts) > 0 else ""
        last_date  = parts[1] if len(parts) > 1 else ""
        next_date  = parts[2] if len(parts) > 2 else ""
        if not name or (not last_date and not next_date):
            reply_message(reply_token,
                "⚠️ 格式：\n小幫手 換濾心 姓名|上次換濾心日期|下次換濾心日期\n\n"
                "範例：\n小幫手 換濾心 Amy|2026-03-31|2026-09-30")
            return True
        try:
            market = _load_market_dev()
            result = market.MarketDevAgent().add_experience(
                name, "濾心更換",
                note=f"上次：{last_date}　下次：{next_date}",
                filter_last=last_date, filter_next=next_date,
            )
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 換濾心記錄失敗：{e}")
        return True

    # 1. Key 查詢（立即回覆）
    if msg.upper().startswith("MTG-"):
        result = tl.get_summary_by_key(msg.upper())
        if result:
            reply_message(reply_token, result)
        else:
            reply_message(reply_token, f"❌ 找不到記錄：{msg}\n請確認 Key 是否正確")
        return True

    def _parse_cmd(prefix: str) -> tuple[str | None, str | None]:
        rest = msg[len(prefix):].strip()
        if not rest:
            return datetime.now().strftime("%Y%m%d"), None
        import re as _re
        if _re.fullmatch(r"\d{8}", rest):
            return rest, None
        return datetime.now().strftime("%Y%m%d"), rest

    def _bg_process(transcript: str, date_str: str, force: bool):
        """背景執行整理，完成後 Push 到群組（不使用 reply token）"""
        try:
            key, summary_msg = tl.process_transcript(transcript, date_str, force=force)
            url_prefix = f"🌐 {NGROK_URL}/summary/{date_str}\n{'─'*20}\n" if NGROK_URL else ""
            push_message(push_target, url_prefix + summary_msg)
        except Exception as e:
            log(f"背景整理失敗：{e}")
            push_message(push_target, f"❌ 整理失敗，請重試\n{str(e)[:80]}")

    # 2. 再次整理（強制覆蓋，背景執行）
    if msg.startswith("再次整理"):
        date_str, inline = _parse_cmd("再次整理")
        if inline:
            tl.archive_transcript(inline, date_str)
            transcript = inline
        else:
            transcript_path = tl.get_date_dir(date_str) / "transcript.txt"
            if not transcript_path.exists():
                reply_message(reply_token, f"⚠️ 找不到 {date_str} 的逐字稿")
                return True
            with open(transcript_path, encoding="utf-8") as f:
                transcript = f.read()
        threading.Thread(target=_bg_process, args=(transcript, date_str, True), daemon=True).start()
        return True

    # 3. 整理指令（背景執行）
    if msg.startswith("整理"):
        date_str, inline = _parse_cmd("整理")
        if inline:
            tl.archive_transcript(inline, date_str)
            transcript = inline
        else:
            transcript_path = tl.get_date_dir(date_str) / "transcript.txt"
            if not transcript_path.exists():
                reply_message(reply_token, f"⚠️ 找不到 {date_str} 的逐字稿")
                return True
            with open(transcript_path, encoding="utf-8") as f:
                transcript = f.read()
        threading.Thread(target=_bg_process, args=(transcript, date_str, False), daemon=True).start()
        return True

    # 4. 長文字視為逐字稿（>100字，背景執行）
    if len(msg) > 100:
        date_str = datetime.now().strftime("%Y%m%d")
        tl.archive_transcript(msg, date_str)
        threading.Thread(target=_bg_process, args=(msg, date_str, False), daemon=True).start()
        return True

    return False


@app.route("/webhook", methods=["POST"])
def webhook():
    return _webhook_line_events.process_line_events(
        request=request,
        abort=abort,
        verify_signature=verify_signature,
        log=log,
        load_classifier=_load_classifier,
        handle_image_message=handle_image_message,
        handle_audio_message=handle_audio_message,
        handle_video_message=handle_video_message,
        handle_file_message=handle_file_message,
        handle_training_command=handle_training_command,
        reply_message=reply_message,
        execute_menu_text=EXEC_MENU_TEXT,
        execute_menu_items=EXEC_MENU_ITEMS,
        exec_menu_active=_exec_menu_active,
        awaiting_person_for_mode=_awaiting_person_for_mode,
        awaiting_exec_input=_awaiting_exec_input,
        awaiting_prospect_selection=_awaiting_prospect_selection,
        awaiting_prospect_file=_awaiting_prospect_file,
        awaiting_invite_selection=_awaiting_invite_selection,
        awaiting_partner_invite_category=_awaiting_partner_invite_category,
        awaiting_partner_invite_person=_awaiting_partner_invite_person,
        awaiting_partner_invite_meeting=_awaiting_partner_invite_meeting,
        awaiting_invite_manage_select=_awaiting_invite_manage_select,
        awaiting_invite_manage_action=_awaiting_invite_manage_action,
        awaiting_invite_manage_edit=_awaiting_invite_manage_edit,
        awaiting_promo_optimize_apply=_awaiting_promo_optimize_apply,
        awaiting_partner_voice_add=_awaiting_partner_voice_add,
        looks_like_explicit_command=_looks_like_explicit_command,
        normalize_partner_category_choice=_normalize_partner_category_choice,
        partners_by_category=_partners_by_category,
        format_partner_choice_menu=_format_partner_choice_menu,
        format_meeting_choice_menu=_format_meeting_choice_menu,
        format_invite_manage_list=_format_invite_manage_list,
        format_invite_manage_actions=_format_invite_manage_actions,
        format_invite_view=_format_invite_view,
        format_invite_edit_confirm=_format_invite_edit_confirm,
        load_course_invite=_load_course_invite,
        load_classifier_module=_load_classifier,
        load_market_dev=_load_market_dev,
        format_prospect_detail=_format_prospect_detail,
    )

@app.route("/health", methods=["GET"])
def health():
    return {"status": "running", "time": datetime.now().isoformat()}


@app.route("/summary/<date_str>", methods=["GET"])
def view_summary(date_str):
    tl = _load_training()
    path = tl.get_date_dir(date_str) / "summary.html"
    if not path.exists():
        return f"<h2>找不到 {date_str} 的記錄</h2>", 404
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return content, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/summary/<date_str>/images/<path:filename>", methods=["GET"])
def view_summary_image(date_str, filename):
    tl = _load_training()
    img_dir = tl.get_date_dir(date_str) / "images"
    if not img_dir.exists():
        return f"<h2>找不到 {date_str} 的圖片資料夾</h2>", 404
    return send_from_directory(str(img_dir), filename)


# ============================================================
# 📂 歸檔瀏覽器（HTML）
# ============================================================

_ARCHIVE_MODE_ICON = {
    "會議記錄": "📝", "行事曆": "🗓️", "夥伴跟進": "🤝",
    "市場開發": "🎯", "培訓資料": "📚", "一般歸檔": "📁",
}
_ARCHIVE_EXT_ICON = {
    ".pdf": "📄", ".pptx": "📊", ".xlsx": "📊", ".docx": "📝",
    ".mp4": "🎬", ".m4a": "🎤", ".mov": "🎬",
}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _render_archive_html(current_dir: Path, url_parts: list) -> str:
    """產生歸檔瀏覽器 HTML 頁面"""

    # ── 麵包屑 ──────────────────────────────────────────────
    crumbs = ['<a href="/archive">歸檔總覽</a>']
    for i, part in enumerate(url_parts):
        href = "/archive/" + "/".join(url_parts[:i + 1])
        crumbs.append(f'<a href="{href}">{part}</a>')
    breadcrumb = " &rsaquo; ".join(crumbs)

    # ── 分類子項 ────────────────────────────────────────────
    subdirs, images, other_files, notes_text = [], [], [], ""

    if current_dir.exists():
        for item in sorted(current_dir.iterdir()):
            if item.is_dir():
                subdirs.append(item)
            elif item.is_file():
                if item.name == "notes.txt":
                    try:
                        notes_text = item.read_text(encoding="utf-8")
                    except Exception:
                        notes_text = "(讀取失敗)"
                elif item.suffix.lower() in _IMAGE_EXTS:
                    images.append(item)
                else:
                    other_files.append(item)

    # ── 資料夾卡片 ──────────────────────────────────────────
    dir_cards_html = ""
    for d in subdirs:
        href = "/archive/" + "/".join(url_parts + [d.name])
        icon = _ARCHIVE_MODE_ICON.get(d.name, "📁")
        try:
            dt = datetime.strptime(d.name, "%Y%m%d")
            label = dt.strftime("%Y/%m/%d")
            icon = "📅"
        except ValueError:
            label = d.name
        file_count = sum(1 for _ in d.rglob("*") if _.is_file())
        dir_cards_html += f'''
        <a href="{href}" class="card">
          <span class="icon">{icon}</span>
          <div>
            <div class="card-name">{label}</div>
            <div class="card-meta">{file_count} 個檔案</div>
          </div>
        </a>'''

    # ── 圖片格子 ────────────────────────────────────────────
    images_html = ""
    for img in images:
        href = "/archive/" + "/".join(url_parts + [img.name])
        images_html += f'''
        <a href="{href}" target="_blank" class="img-thumb">
          <img src="{href}" alt="{img.name}" loading="lazy">
          <div class="img-name">{img.name}</div>
        </a>'''

    # ── 一般檔案列表 ────────────────────────────────────────
    files_html = ""
    for f in other_files:
        href = "/archive/" + "/".join(url_parts + [f.name])
        ext = f.suffix.lower()
        icon = _ARCHIVE_EXT_ICON.get(ext, "📎")
        size = f.stat().st_size
        size_str = f"{size // 1024}KB" if size >= 1024 else f"{size}B"
        files_html += f'''
        <div class="file-row">
          <a href="{href}" download="{f.name}">{icon} {f.name}</a>
          <span class="file-size">{size_str}</span>
        </div>'''

    # ── notes.txt 預覽 ──────────────────────────────────────
    notes_html = ""
    if notes_text:
        safe = notes_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        notes_html = f'''
        <div class="section-title">📋 備註記錄</div>
        <div class="notes-box"><pre>{safe}</pre></div>'''

    # ── 各區塊組合 ──────────────────────────────────────────
    body_parts = []
    if dir_cards_html:
        body_parts.append(
            f'<div class="section-title">資料夾</div>'
            f'<div class="cards">{dir_cards_html}</div>'
        )
    body_parts.append(notes_html)
    if images_html:
        body_parts.append(
            f'<div class="section-title">圖片（{len(images)} 張）</div>'
            f'<div class="img-grid">{images_html}</div>'
        )
    if files_html:
        body_parts.append(
            f'<div class="section-title">檔案（{len(other_files)} 個）</div>'
            f'<div class="file-list">{files_html}</div>'
        )
    if not dir_cards_html and not images_html and not files_html and not notes_text:
        body_parts.append('<div class="empty">此資料夾目前沒有內容</div>')

    body = "\n".join(body_parts)
    title = url_parts[-1] if url_parts else "歸檔總覽"

    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — 歸檔瀏覽器</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
     background:#f5f5f7;color:#1d1d1f;}}
.header{{background:#fff;padding:14px 20px;border-bottom:1px solid #e5e5ea;
         position:sticky;top:0;z-index:10;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.header h1{{font-size:18px;margin-bottom:4px}}
.breadcrumb{{font-size:13px;color:#888}}
.breadcrumb a{{color:#007aff;text-decoration:none}}
.breadcrumb a:hover{{text-decoration:underline}}
.container{{max-width:900px;margin:0 auto;padding:16px 20px}}
.section-title{{font-size:11px;font-weight:700;color:#888;text-transform:uppercase;
                letter-spacing:.5px;margin:20px 0 8px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}
.card{{background:#fff;border-radius:12px;padding:12px 14px;text-decoration:none;
       color:#1d1d1f;display:flex;align-items:center;gap:10px;
       box-shadow:0 1px 3px rgba(0,0,0,.08);transition:box-shadow .15s}}
.card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.14)}}
.icon{{font-size:26px;line-height:1;flex-shrink:0}}
.card-name{{font-size:13px;font-weight:600;word-break:break-word}}
.card-meta{{font-size:11px;color:#aaa;margin-top:2px}}
.img-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px}}
.img-thumb{{display:block;text-decoration:none;color:#555}}
.img-thumb img{{width:100%;height:110px;object-fit:cover;border-radius:8px;
                border:1px solid #e5e5ea;display:block}}
.img-name{{font-size:10px;margin-top:3px;text-align:center;
           overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.file-list{{background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.file-row{{display:flex;justify-content:space-between;align-items:center;
           padding:11px 16px;border-bottom:1px solid #f2f2f7}}
.file-row:last-child{{border-bottom:none}}
.file-row a{{text-decoration:none;color:#007aff;font-size:13px}}
.file-row a:hover{{text-decoration:underline}}
.file-size{{font-size:11px;color:#aaa;margin-left:8px;white-space:nowrap}}
.notes-box{{background:#fffde7;border:1px solid #ffe082;border-radius:12px;padding:14px 16px}}
.notes-box pre{{white-space:pre-wrap;font-size:13px;line-height:1.65;font-family:inherit}}
.empty{{text-align:center;color:#bbb;padding:48px 0;font-size:14px}}
</style>
</head>
<body>
<div class="header">
  <h1>📂 歸檔瀏覽器</h1>
  <div class="breadcrumb">{breadcrumb}</div>
</div>
<div class="container">
{body}
</div>
</body>
</html>'''


@app.route("/archive")
@app.route("/archive/")
def archive_index():
    return _render_archive_html(CLASSIFIED_DIR, []), 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/archive/<path:subpath>")
def archive_browse(subpath):
    target = CLASSIFIED_DIR / subpath
    if not target.exists():
        return "<h2 style='font-family:sans-serif;padding:20px'>找不到此路徑</h2>", 404
    if target.is_file():
        return send_from_directory(str(target.parent), target.name)
    parts = list(Path(subpath).parts)
    return _render_archive_html(target, parts), 200, {"Content-Type": "text/html; charset=utf-8"}


# ============================================================
# 🌐 Web Dashboard
# ============================================================

def process_web_command(cmd: str) -> str:
    """Handle all bot commands and return a string result (no LINE reply)."""
    web_scope = "web_user"
    try:
        clf = _load_classifier().ClassifierAgent()
        pending = clf.get_pending(web_scope)
        if pending and pending.get("status") == "awaiting_folder_name":
            if cmd.strip().upper() == "NA":
                count = len(pending.get("items", []))
                clf.clear_pending(web_scope, remove_file=True)
                return f"🗑️ 已取消歸檔，刪除 {count} 個待歸檔項目。"
            return clf.submit_pending_folder_name(web_scope, cmd.strip()) or "目錄名稱不可空白，請重新輸入"
        if pending and cmd.strip().isdigit():
            return clf.execute_pending_option(web_scope, int(cmd.strip()))
        if pending and cmd.strip() in {"待歸檔", "查詢待歸檔"}:
            return clf.format_pending_menu(web_scope)
        if pending and cmd.strip().upper() == "NA":
            count = len(pending.get("items", []))
            clf.clear_pending(web_scope, remove_file=True)
            return f"🗑️ 已取消歸檔，刪除 {count} 個待歸檔項目。"
    except Exception:
        pass
    if cmd.strip() == "查詢已產生的今日之後會議邀約文宣":
        try:
            course = _load_course_invite()
            rows = course.list_upcoming_invites(today_only_after=True)
            if rows:
                _web_invite_manage_state["web"] = {"step": "select", "rows": rows}
            else:
                _web_invite_manage_state.pop("web", None)
            return _format_invite_manage_list(rows)
        except Exception as e:
            return f"✗ 查詢邀約文宣失敗：{e}"

    if cmd.strip().startswith("邀約文宣 跟進夥伴"):
        _web_partner_invite_state["web"] = {"step": "category"}
        return _partner_category_menu()

    if _web_promo_optimize_state.get("web") and cmd.strip().isdigit():
        state = _web_promo_optimize_state.pop("web")
        choice = int(cmd.strip())
        if choice == 1:
            try:
                course = _load_course_invite()
                return course.apply_optimized_promo(state["promo_id"])
            except Exception as e:
                return f"✗ 套用優化文宣失敗：{e}"
        if choice == 2:
            return "已保留優化結果，不覆蓋原課程文宣"
        _web_promo_optimize_state["web"] = state
        return "⚠️ 請輸入 1 或 2，NA 取消"

    if cmd.startswith("優化課程文宣"):
        try:
            course = _load_course_invite()
            result = course.CourseInviteAgent().handle_command(cmd)
            if result and result.startswith("✅ 文宣已優化（"):
                promo_id = cmd.replace("優化課程文宣", "", 1).strip()
                _web_promo_optimize_state["web"] = {"promo_id": promo_id}
                return result + "\n\n1. 套用到該課程文宣\n2. 保留優化結果，不覆蓋\n\n請輸入 1 或 2，NA 取消"
            return result or "⚠️ AI 無回應，請稍後再試"
        except Exception as e:
            return f"✗ 優化課程文宣失敗：{e}"

    routed = _webhook_command_router.handle_web_command(
        cmd=cmd,
        sessions=_nutrition_sessions,
        load_calendar=_load_calendar,
        load_partner=_load_partner,
        load_classifier=_load_classifier,
        load_market_dev=_load_market_dev,
        load_course_invite=_load_course_invite,
        load_daily_report=_load_daily_report,
        load_nutrition_dri=_load_nutrition_dri,
        load_nutrition_assessment=_load_nutrition_assessment,
        load_ai_prompt_manager=_load_ai_prompt_manager,
        load_ai_skill_manager=_load_ai_skill_manager,
        load_followup_suggestion=_load_followup_suggestion,
        load_training_agent=_load_training_agent,
        load_followup=_load_followup,
        load_motivation=_load_motivation,
    )
    if routed is not None:
        return routed
    if cmd.strip().upper() == "NA":
        _web_invite_combos.pop("web", None)
        _web_partner_invite_state.pop("web", None)
        _web_invite_manage_state.pop("web", None)
        return "↩️ 已取消，返回待機。"

    if _looks_like_explicit_command(cmd) and _web_partner_invite_state.get("web"):
        _web_partner_invite_state.pop("web", None)
    if _looks_like_explicit_command(cmd) and _web_invite_manage_state.get("web"):
        _web_invite_manage_state.pop("web", None)

    if _web_partner_invite_state.get("web"):
        state = _web_partner_invite_state["web"]
        if _looks_like_explicit_command(cmd):
            _web_partner_invite_state.pop("web", None)
            state = None
        if not state:
            pass
        elif state.get("step") == "category":
            category = _normalize_partner_category_choice(cmd)
            if not category:
                return "⚠️ 請輸入 1、2、3 或 A、B、C"
            people = _partners_by_category(category)
            if not people:
                _web_partner_invite_state.pop("web", None)
                return f"⚠️ 目前沒有分類 {category} 的夥伴。"
            _web_partner_invite_state["web"] = {"step": "person", "category": category, "people": people}
            return _format_partner_choice_menu(category, people)
        elif state.get("step") == "person" and cmd.strip().isdigit():
            people = state["people"]
            idx = int(cmd.strip())
            if not (1 <= idx <= len(people)):
                return f"⚠️ 請輸入 1～{len(people)} 的編號"
            course = _load_course_invite()
            meetings = course.list_meetings()
            if not meetings:
                _web_partner_invite_state.pop("web", None)
                return "⚠️ 目前沒有排定的課程會議，請先新增課程會議。"
            person = people[idx - 1]
            _web_partner_invite_state["web"] = {"step": "meeting", "name": person.get("name", ""), "meetings": meetings}
            return _format_meeting_choice_menu(person.get("name", ""), meetings)
        elif state.get("step") == "meeting" and cmd.strip().isdigit():
            meetings = state["meetings"]
            idx = int(cmd.strip())
            if not (1 <= idx <= len(meetings)):
                return f"⚠️ 請輸入 1～{len(meetings)} 的編號"
            meeting = meetings[idx - 1]
            name = state["name"]
            _web_partner_invite_state.pop("web", None)
            try:
                course = _load_course_invite()
                return course.generate_partner_invite_for_meeting(name, meeting)
            except Exception as e:
                return f"✗ 邀約文宣產生失敗：{e}"

    # 邀約組合編號選擇（網頁版）
    if _web_invite_combos.get("web") and cmd.strip().isdigit():
        combos = _web_invite_combos.pop("web")
        idx = int(cmd.strip())
        if 1 <= idx <= len(combos):
            combo = combos[idx - 1]
            try:
                course = _load_course_invite()
                if combo["role"] == "prospect":
                    return course.generate_prospect_invite_for_meeting(combo["name"], combo["meeting"])
                else:
                    return course.generate_partner_invite_for_meeting(combo["name"], combo["meeting"])
            except Exception as e:
                return f"✗ 邀約文宣產生失敗：{e}"
        else:
            return f"⚠️ 請輸入 1～{len(combos)} 的編號"

    if _web_invite_manage_state.get("web"):
        state = _web_invite_manage_state["web"]
        if state.get("step") == "select" and cmd.strip().isdigit():
            rows = state["rows"]
            idx = int(cmd.strip())
            if not (1 <= idx <= len(rows)):
                return f"⚠️ 請輸入 1～{len(rows)} 的編號"
            rec = rows[idx - 1]
            _web_invite_manage_state["web"] = {"step": "action", "record": rec}
            return _format_invite_manage_actions(rec)
        if state.get("step") == "view" and cmd.strip().isdigit():
            rec = state["record"]
            choice = int(cmd.strip())
            if choice == 1:
                _web_invite_manage_state["web"] = {"step": "confirm_edit", "record": rec}
                return _format_invite_edit_confirm(rec)
            if choice == 2:
                _web_invite_manage_state.pop("web", None)
                return "已返回邀約文宣管理"
            return "⚠️ 請輸入 1 或 2"
        if state.get("step") == "action" and cmd.strip().isdigit():
            rec = state["record"]
            choice = int(cmd.strip())
            if choice == 1:
                _web_invite_manage_state["web"] = {"step": "view", "record": rec}
                return _format_invite_view(rec)
            if choice == 2:
                _web_invite_manage_state.pop("web", None)
                try:
                    course = _load_course_invite()
                    if rec.get("role") == "prospect":
                        return course.generate_prospect_invite_for_meeting(rec["name"], rec["meeting"])
                    return course.generate_partner_invite_for_meeting(rec["name"], rec["meeting"])
                except Exception as e:
                    return f"✗ 強制重新產生失敗：{e}"
            return "⚠️ 請輸入 1 或 2"
        if state.get("step") == "confirm_edit" and cmd.strip().isdigit():
            choice = int(cmd.strip())
            if choice == 1:
                _web_invite_manage_state["web"] = {"step": "edit", "record": state["record"]}
                return "📝 請直接輸入新的邀約文宣內容，NA 取消"
            _web_invite_manage_state.pop("web", None)
            return "已取消修改邀約文宣"
        if state.get("step") == "confirm_edit":
            return "⚠️ 請輸入 1 或 2，NA 取消"
        if state.get("step") == "edit":
            rec = state["record"]
            _web_invite_manage_state.pop("web", None)
            new_content = cmd.strip()
            if not new_content:
                return "⚠️ 新內容不可空白"
            try:
                course = _load_course_invite()
                ok = course.update_invite(rec["meeting"]["id"], rec["name"], new_content)
                return "✅ 已更新邀約文宣" if ok else "⚠️ 找不到該筆邀約文宣"
            except Exception as e:
                return f"✗ 更新邀約文宣失敗：{e}"

    try:
        # Classifier modes / archive queries
        clf_mod = _load_classifier()

        if cmd.startswith("歸類模式") or cmd.startswith("關閉歸類模式"):
            clf = clf_mod.ClassifierAgent()
            return clf.handle_command(cmd)

        if cmd.startswith("潛在家人資料"):
            name = cmd.replace("潛在家人資料", "").strip()
            if not name:
                return "⚠️ 請提供人員名稱，例如：潛在家人資料 張三"
            clf = clf_mod.ClassifierAgent()
            return clf.set_mode("市場開發", name)
    except Exception as e:
        return f"⚠️ 歸類指令錯誤：{e}"

    try:
        # Market dev
        market = _load_market_dev()

        import re as _re_web
        if _re_web.match(r'^潛在家人詳情\s+\d+$', cmd):
            idx = int(cmd.split()[-1])
            rows = market.MarketDevAgent().list_prospects()
            if 1 <= idx <= len(rows):
                return _format_prospect_detail(rows[idx - 1])
            return f"⚠️ 無效編號 {idx}"
    except Exception as e:
        return f"⚠️ 市場開發指令錯誤：{e}"

    try:
        # Training log
        tl = _load_training()

        if cmd.upper().startswith("MTG-"):
            result = tl.get_summary_by_key(cmd.upper())
            return result if result else f"找不到記錄：{cmd.upper()}"

        if cmd.startswith("再次整理") or cmd.startswith("整理"):
            # Parse date and transcript from command
            parts = cmd.split(None, 1)
            date_str = datetime.now().strftime("%Y-%m-%d")
            transcript = cmd
            if len(parts) >= 2:
                rest = parts[1].strip()
                # Try to extract YYYY-MM-DD
                import re
                date_match = re.match(r"(\d{4}-\d{2}-\d{2})", rest)
                if date_match:
                    date_str = date_match.group(1)
                    transcript = rest[len(date_str):].strip()
                else:
                    transcript = rest
            force = cmd.startswith("再次整理")
            key, msg = tl.process_transcript(transcript, date_str, force=force)
            if NGROK_URL:
                msg = f"{NGROK_URL}/summary/{key}\n\n{msg}"
            return msg
    except Exception as e:
        return f"⚠️ 培訓記錄指令錯誤：{e}"

    # Exec menu
    if cmd in ("執行選單", "選單"):
        return EXEC_MENU_TEXT

    # Help commands
    if cmd in ("help", "指令集", "說明", "指令", "?", "？"):
        return HELP_TEXT

    # Fallback: intent analysis
    try:
        intent = analyze_intent(cmd)
        return (
            f"意圖：{intent['意圖']}\n"
            f"情緒：{intent['情緒']}\n"
            f"建議回覆：{intent['建議回覆']}\n"
            f"建議行動：{intent['建議行動']}"
        )
    except Exception as e:
        return f"⚠️ 無法分析指令：{e}"


def _render_dashboard_html_v2() -> str:
    return _webhook_web_views.render_dashboard_html_v2()


_webhook_web_views.register_web_view_routes(app, _render_dashboard_html_v2)

_webhook_api_routes.register_api_routes(
    app,
    process_web_command=lambda cmd: process_web_command(cmd),
    request=request,
    nutrition_sessions=_nutrition_sessions,
    load_classifier=lambda: _load_classifier(),
    load_market_dev=lambda: _load_market_dev(),
    load_partner=lambda: _load_partner(),
    load_course_invite=lambda: _load_course_invite(),
    load_daily_report=lambda: _load_daily_report(),
    load_nutrition_assessment=lambda: _load_nutrition_assessment(),
    load_ai_prompt_manager=lambda: _load_ai_prompt_manager(),
    load_ai_skill_manager=lambda: _load_ai_skill_manager(),
)


# ============================================================
# 📝 更新跟進狀態
# ============================================================

def update_status(user_id: str, intent: dict):
    _webhook_intent.update_status(user_id, intent)


# ============================================================
# General command handling
# ============================================================


if __name__ == "__main__":
    log("🚀 LINE Webhook 伺服器啟動")
    log("📡 本地地址：http://localhost:5000/webhook")
    log("💡 對外存取：請執行 ngrok http 5000")
    log("   複製 ngrok URL 設定到 LINE Console → Webhook URL")
    app.run(host="0.0.0.0", port=5000, debug=False)
