"""
LINE Bot Webhook Server
File: C:/Users/user/claude AI_Agent/agents/06_line_webhook.py
Function: Receive user replies, AI intent detection, update follow-up status
Run: python 06_line_webhook.py (keep running)
External access: use ngrok (free) to expose Webhook URL
"""

import os
import json
import hmac
import hashlib
import base64
import threading
import time
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, abort, send_from_directory
from dotenv import load_dotenv
import importlib.util as _ilu
import sys as _sys

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
    23: {"label": "🧹 居家清潔歸檔 (Amway Home)","cmd": "居家清潔歸檔", "prompt": None, "reset_person": True},
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
 23. 🧹 居家清潔 (Amway Home) ▶
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

══════════════════
▶ 直接執行　其餘顯示輸入範本
回覆數字即可　NA = 取消返回"""

# 追蹤哪些 scope 正在等待執行選單輸入（in-memory，重啟後清除）
_exec_menu_active: dict = {}
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

app = Flask(__name__)

def extract_trigger(msg: str) -> str | None:
    """若訊息以觸發詞開頭，回傳去掉觸發詞後的內容；否則回傳 None"""
    for tw in TRIGGER_WORDS:
        if msg.startswith(tw):
            return msg[len(tw):].strip()
    return None

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [WEBHOOK] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 🔐 LINE 簽章驗證
# ============================================================

def verify_signature(body: bytes, signature: str) -> bool:
    if not LINE_SECRET:
        return True  # 開發模式跳過驗證
    hash_val = hmac.new(
        LINE_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_val).decode() == signature


# ============================================================
# 🤖 規則式意圖分析（零 API 消耗）
# ============================================================

INTENT_RULES = [
    {
        "意圖": "有興趣",
        "關鍵字": ["有興趣","想了解","想知道","告訴我","可以","好啊","好的","想試","報名","加入","怎麼做","如何"],
        "情緒": "正面",
        "建議回覆": "太好了！我這邊為你安排更多資訊，方便的話我們可以找個時間聊聊 😊",
        "建議行動": "安排會面"
    },
    {
        "意圖": "需要更多資訊",
        "關鍵字": ["什麼","詳細","介紹","說明","資料","多少錢","費用","怎樣","如何","哪裡"],
        "情緒": "中立",
        "建議回覆": "當然！我來為你說明，這個機會非常適合想要增加收入的朋友 💪",
        "建議行動": "發送資料"
    },
    {
        "意圖": "忙碌稍後",
        "關鍵字": ["忙","等等","待會","晚點","之後","改天","最近","稍後","下次"],
        "情緒": "中立",
        "建議回覆": "沒問題！等你方便的時候再聊，我隨時都在 😄",
        "建議行動": "繼續跟進"
    },
    {
        "意圖": "婉拒",
        "關鍵字": ["不用","不要","沒興趣","不需要","拒絕","算了","不了","謝謝但","不考慮"],
        "情緒": "負面",
        "建議回覆": "完全理解！如果未來有任何需要，歡迎隨時找我 😊",
        "建議行動": "暫停跟進"
    },
]

def analyze_intent(user_message: str) -> dict:
    """規則式意圖分析，零 API 消耗"""
    msg = user_message.lower()
    for rule in INTENT_RULES:
        if any(kw in msg for kw in rule["關鍵字"]):
            return {
                "意圖":    rule["意圖"],
                "情緒":    rule["情緒"],
                "建議回覆": rule["建議回覆"],
                "建議行動": rule["建議行動"],
            }
    return {
        "意圖": "其他",
        "情緒": "中立",
        "建議回覆": "謝謝你的訊息！我稍後再跟你聯繫 😊",
        "建議行動": "繼續跟進"
    }


# ============================================================
# 💬 回覆 LINE 訊息
# ============================================================

def reply_message(reply_token: str, message: str):
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    r = requests.post(LINE_REPLY, headers=headers, json=payload, timeout=5)
    if r.status_code != 200:
        log(f"  ⚠️ Reply 失敗：{r.status_code} {r.text[:80]}")

def push_message(user_id: str, message: str):
    """Push API：不受 reply token 限制，自動分割超過 4900 字的訊息"""
    MAX = 4900
    chunks = [message[i:i+MAX] for i in range(0, len(message), MAX)]
    messages = [{"type": "text", "text": c} for c in chunks[:5]]  # LINE 最多 5 則
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {"to": user_id, "messages": messages}
    r = requests.post(LINE_PUSH, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        log(f"  ⚠️ Push 失敗：{r.status_code} {r.text[:120]}")


def schedule_pending_menu(clf, scope_id: str, push_target: str, delay_sec: int = 3):
    token = clf.mark_pending_menu(scope_id)
    if not token:
        return

    def _worker():
        time.sleep(delay_sec)
        if clf.should_push_pending_menu(scope_id, token):
            push_message(push_target, clf.format_pending_menu(scope_id))
            clf.mark_menu_sent(scope_id)

    threading.Thread(target=_worker, daemon=True).start()


# ============================================================
# 📡 Webhook 路由
# ============================================================

def _download_line_content(msg_id: str, timeout: int = 30) -> bytes | None:
    """從 LINE Content API 下載媒體（圖片/音檔/影片/檔案）"""
    url = f"https://api-data.line.me/v2/bot/message/{msg_id}/content"
    r = requests.get(url, headers={"Authorization": f"Bearer {LINE_TOKEN}"}, timeout=timeout)
    return r.content if r.status_code == 200 else None


def handle_image_message(event: dict, mode_info: dict = None, clf=None):
    """接收圖片 → 模式已設定時直接歸檔；auto 模式先暫存顯示選單"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id
    push_target = group_id or user_id

    img_bytes = _download_line_content(msg_id)
    if img_bytes is None:
        reply_message(reply_token, "⚠️ 圖片下載失敗，請重試")
        return

    mode   = (mode_info or {}).get("mode", "auto")
    person = (mode_info or {}).get("person", "")

    if clf is not None and mode != "auto":
        # 模式已設定 → 直接歸檔
        clf.route_image(img_bytes, msg_id, mode, person,
                        reply_message, push_message, reply_token, push_target)
        return

    if clf is not None:
        clf.stage_file(
            img_bytes,
            f"image_{msg_id}.jpg",
            "image",
            scope_id,
            content_type="image/jpeg",
            source_name=event.get("message", {}).get("type", "image"),
        )
        schedule_pending_menu(clf, scope_id, scope_id)
        return

    date_str = datetime.now().strftime("%Y%m%d")
    tl  = _load_training()
    filename = f"image_{msg_id}.jpg"
    tl.archive_image(img_bytes, filename, date_str)
    reply_message(reply_token, f"📸 圖片已歸檔（{date_str}）")


def handle_audio_message(event: dict, mode_info: dict, clf):
    """接收音檔 → 模式已設定時直接歸檔；auto 模式先暫存顯示選單"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id

    data = _download_line_content(msg_id, timeout=60)
    if data is None:
        reply_message(reply_token, "⚠️ 音檔下載失敗，請重試")
        return

    mode      = (mode_info or {}).get("mode", "auto")
    person    = (mode_info or {}).get("person", "")
    date_str  = (mode_info or {}).get("archive_date", "")
    filename  = f"audio_{msg_id}.m4a"

    if mode != "auto":
        saved = clf.archive_file(data, filename, mode, "audio", person, date_str)
        person_tag = f"「{person}」的" if person else ""
        reply_message(reply_token,
                      f"🎤 音檔已歸入{person_tag}「{mode}」\n路徑：.../{'/'.join(saved.parts[-4:])}")
        return

    clf.stage_file(data, filename, "audio", scope_id,
                   content_type="audio/m4a",
                   source_name=event.get("message", {}).get("type", "audio"))
    schedule_pending_menu(clf, scope_id, scope_id)


def handle_video_message(event: dict, mode_info: dict, clf):
    """接收影片 → 模式已設定時直接歸檔；auto 模式先暫存顯示選單"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id

    data = _download_line_content(msg_id, timeout=120)
    if data is None:
        reply_message(reply_token, "⚠️ 影片下載失敗，請重試")
        return

    mode      = (mode_info or {}).get("mode", "auto")
    person    = (mode_info or {}).get("person", "")
    date_str  = (mode_info or {}).get("archive_date", "")
    filename  = f"video_{msg_id}.mp4"

    if mode != "auto":
        saved = clf.archive_file(data, filename, mode, "videos", person, date_str)
        person_tag = f"「{person}」的" if person else ""
        reply_message(reply_token,
                      f"🎬 影片已歸入{person_tag}「{mode}」\n路徑：.../{'/'.join(saved.parts[-4:])}")
        return

    clf.stage_file(data, filename, "video", scope_id,
                   content_type="video/mp4",
                   source_name=event.get("message", {}).get("type", "video"))
    schedule_pending_menu(clf, scope_id, scope_id)


def handle_file_message(event: dict, mode_info: dict, clf):
    """接收檔案（PDF/PPTX/XLSX/其他）→ 模式已設定時直接歸檔；auto 模式先暫存顯示選單"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id

    orig_name = event["message"].get("fileName", "")
    safe = "".join(c for c in orig_name if c.isalnum() or c in "._- ()[]") or f"file_{msg_id}"

    data = _download_line_content(msg_id, timeout=60)
    if data is None:
        reply_message(reply_token, "⚠️ 檔案下載失敗，請重試")
        return

    mode      = (mode_info or {}).get("mode", "auto")
    person    = (mode_info or {}).get("person", "")
    date_str  = (mode_info or {}).get("archive_date", "")

    if mode != "auto":
        saved = clf.archive_file(data, safe, mode, "files", person, date_str)
        person_tag = f"「{person}」的" if person else ""
        reply_message(reply_token,
                      f"📄 檔案已歸入{person_tag}「{mode}」\n路徑：.../{'/'.join(saved.parts[-4:])}")
        return

    clf.stage_file(data, safe, "file", scope_id,
                   content_type=event.get("message", {}).get("fileName", ""),
                   source_name=orig_name)
    schedule_pending_menu(clf, scope_id, scope_id)


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

    if msg.startswith("查詢歸檔"):
        try:
            clf_mod = _load_classifier()
            person = msg.replace("查詢歸檔", "").strip()
            result = clf_mod.ClassifierAgent().query_archive(person)
            # 附上網頁瀏覽連結
            if NGROK_URL:
                if person:
                    # 嘗試找實際資料夾名稱（支援模糊）
                    from pathlib import Path as _P
                    _classified = BASE_DIR / "output" / "classified"
                    matched_name = person
                    if _classified.exists():
                        for _d in _classified.iterdir():
                            if _d.is_dir() and (person in _d.name or _d.name in person):
                                matched_name = _d.name
                                break
                    import urllib.parse
                    url_path = urllib.parse.quote(matched_name, safe="")
                    result += f"\n\n🌐 網頁查看：{NGROK_URL}/archive/{url_path}"
                else:
                    result += f"\n\n🌐 網頁查看：{NGROK_URL}/archive"
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 查詢歸檔失敗：{e}")
        return True

    cal_result = cal.handle_calendar_command(msg)
    if cal_result:
        reply_message(reply_token, cal_result)
        return True

    partner_result = partner.handle_partner_command(msg)
    if partner_result:
        reply_message(reply_token, partner_result)
        return True

    # === 新系統：市場開發 / 培訓 / 跟進 / 激勵 ===

    if msg.startswith("新增潛在家人"):
        def _run_market():
            try:
                market = _load_market_dev()
                result = market.MarketDevAgent().handle_add_prospect(msg)
                push_message(push_target, result)
            except Exception as e:
                push_message(push_target, f"✗ 新增潛在家人失敗：{e}")
        reply_message(reply_token, "⏳ 正在新增並 AI 評分，請稍候...")
        threading.Thread(target=_run_market, daemon=True).start()
        return True

    if msg.startswith("查詢潛在家人"):
        try:
            keyword = msg.replace("查詢潛在家人", "", 1).strip()
            market = _load_market_dev()
            rows = market.MarketDevAgent().list_prospects(keyword)
            if not rows:
                reply_message(reply_token, "📋 目前名單是空的。\n新增：小幫手 新增潛在家人 姓名|職業|管道|備註")
                return True
            _awaiting_prospect_selection[group_id or user_id] = rows
            lines = [f"📋 潛在家人名單（共 {len(rows)} 位）\n輸入編號查看詳細資料，NA 取消\n"]
            for i, r in enumerate(rows, 1):
                star = "⭐" * int(r["AI評分"]) if r.get("AI評分", "").isdigit() else "─"
                lines.append(f"{i}. {r.get('姓名','')}　{r.get('職業','')}　{star}")
            reply_message(reply_token, "\n".join(lines))
        except Exception as e:
            reply_message(reply_token, f"✗ 查詢失敗：{e}")
        return True

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

    # === 課程會議邀約 ===

    # 邀約文宣 潛在家人（無姓名）→ 列出組合清單
    if msg.strip() == "邀約文宣 潛在家人":
        try:
            course = _load_course_invite()
            market = _load_market_dev()
            meetings = course.list_meetings()
            if not meetings:
                reply_message(reply_token, "⚠️ 目前沒有排定的課程會議，請先新增課程會議。")
                return True
            prospects = market.MarketDevAgent().list_prospects()
            if not prospects:
                reply_message(reply_token, "⚠️ 目前沒有潛在家人資料，請先新增。")
                return True
            combos = []
            for p in prospects:
                for m in meetings:
                    combos.append({"name": p.get("姓名", ""), "role": "prospect", "meeting": m})
                    if len(combos) >= 20:
                        break
                if len(combos) >= 20:
                    break
            _awaiting_invite_selection[group_id or user_id] = combos
            lines = [f"📋 邀約組合清單（共 {len(combos)} 組）\n輸入編號產生邀約文宣，NA 取消\n"]
            for i, c in enumerate(combos, 1):
                when = c["meeting"]["date"] + (f" {c['meeting']['time']}" if c["meeting"].get("time") else "")
                lines.append(f"{i}. {c['name']} × {c['meeting']['title']}（{when}）")
            reply_message(reply_token, "\n".join(lines))
        except Exception as e:
            reply_message(reply_token, f"✗ 邀約清單失敗：{e}")
        return True

    # 邀約文宣 跟進夥伴（無姓名）→ 列出組合清單
    if msg.strip() == "邀約文宣 跟進夥伴":
        _awaiting_partner_invite_category[group_id or user_id] = True
        reply_message(reply_token, _partner_category_menu())
        return True

    if msg.strip() == "查詢已產生的今日之後會議邀約文宣":
        try:
            course = _load_course_invite()
            rows = course.list_upcoming_invites(today_only_after=True)
            if not rows:
                reply_message(reply_token, "目前沒有今日之後已產生的會議邀約文宣。")
                return True
            _awaiting_invite_manage_select[group_id or user_id] = rows
            reply_message(reply_token, _format_invite_manage_list(rows))
        except Exception as e:
            reply_message(reply_token, f"✗ 查詢已產生邀約文宣失敗：{e}")
        return True

    _course_cmds = (
        "新增課程會議", "查詢課程會議", "刪除課程會議", "修改課程會議", "從行事曆加入課程",
        "新增課程文宣", "查詢課程文宣", "優化課程文宣",
        "查詢已產生的今日之後會議邀約文宣", "修改已產生的今日之後會議邀約文宣",
        "邀約文宣 潛在家人", "邀約文宣 跟進夥伴",
        "課程會議", "課程文宣", "課程",
    )
    if any(msg.startswith(c) for c in _course_cmds):
        _is_async_course = msg.startswith("優化課程文宣") or msg.startswith("邀約文宣")
        if _is_async_course:
            def _run_course():
                try:
                    course = _load_course_invite()
                    result = course.CourseInviteAgent().handle_command(msg)
                    push_message(push_target, result if result else "⚠️ 課程指令無結果")
                except Exception as e:
                    push_message(push_target, f"✗ 課程邀約失敗：{e}")
            reply_message(reply_token, "⏳ 正在透過 AI 產生課程文宣，請稍候...")
            threading.Thread(target=_run_course, daemon=True).start()
        else:
            try:
                course = _load_course_invite()
                result = course.CourseInviteAgent().handle_command(msg)
                reply_message(reply_token, result if result else "⚠️ 課程指令無結果")
            except Exception as e:
                reply_message(reply_token, f"✗ 課程指令失敗：{e}")
        return True

    if msg.startswith("培訓"):
        try:
            training = _load_training_agent()
            result = training.TrainingAgent().handle_query(msg)
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 培訓查詢失敗：{e}")
        return True

    if msg.strip() == "跟進報告":
        def _run_followup():
            try:
                followup = _load_followup()
                result = followup.FollowupAgent().generate_report_text()
                push_message(push_target, result)
            except Exception as e:
                push_message(push_target, f"✗ 跟進報告失敗：{e}")
        reply_message(reply_token, "⏳ 正在生成跟進報告，請稍候...")
        threading.Thread(target=_run_followup, daemon=True).start()
        return True

    if msg.startswith("激勵") or msg.startswith("里程碑"):
        def _run_motivation():
            try:
                motivation = _load_motivation()
                result = motivation.MotivationAgent().handle_realtime(msg)
                push_message(push_target, result)
            except Exception as e:
                push_message(push_target, f"✗ 激勵訊息失敗：{e}")
        reply_message(reply_token, "⏳ 正在生成激勵訊息，請稍候...")
        threading.Thread(target=_run_motivation, daemon=True).start()
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
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()

    if not verify_signature(body, signature):
        log("❌ 簽章驗證失敗")
        abort(400)

    data   = request.json
    events = data.get("events", [])

    # 載入歸類模式（一次，供所有 event 共用）
    try:
        _clf_mod   = _load_classifier()
        _clf_agent = _clf_mod.ClassifierAgent()
        _mode_info = _clf_agent.get_mode()
    except Exception as _e:
        log(f"  ⚠️ ClassifierAgent 載入失敗：{_e}")
        _clf_agent = None
        _mode_info = {"mode": "auto", "set_at": ""}

    for event in events:
        if event.get("type") != "message":
            continue

        msg_type    = event.get("message", {}).get("type", "")
        reply_token = event.get("replyToken", "")
        user_id     = event.get("source", {}).get("userId", "")
        group_id    = event.get("source", {}).get("groupId", "")
        push_target = group_id or user_id

        # ── 圖片 ───────────────────────────────────────────────
        if msg_type == "image":
            log(f"🖼️ 收到圖片（模式：{_mode_info['mode']}）")
            handle_image_message(event, _mode_info, _clf_agent)
            continue

        # ── 音檔 ───────────────────────────────────────────────
        if msg_type == "audio":
            log(f"🎤 收到音檔（模式：{_mode_info['mode']}）")
            if _clf_agent:
                handle_audio_message(event, _mode_info, _clf_agent)
            else:
                reply_message(reply_token, "⚠️ 音檔功能暫時無法使用")
            continue

        # ── 影片 ───────────────────────────────────────────────
        if msg_type == "video":
            log(f"🎬 收到影片（模式：{_mode_info['mode']}）")
            if _clf_agent:
                handle_video_message(event, _mode_info, _clf_agent)
            else:
                reply_message(reply_token, "⚠️ 影片功能暫時無法使用")
            continue

        # ── 檔案（PDF/PPTX/XLSX 等）────────────────────────────
        if msg_type == "file":
            fname = event.get("message", {}).get("fileName", "")
            log(f"📄 收到檔案：{fname}（模式：{_mode_info['mode']}）")
            if _clf_agent:
                handle_file_message(event, _mode_info, _clf_agent)
            else:
                reply_message(reply_token, "⚠️ 檔案功能暫時無法使用")
            continue

        if msg_type != "text":
            continue

        user_msg = event["message"]["text"]
        log(f"📨 收到訊息 from {user_id[:8]}：{user_msg[:50]}")

        if _clf_agent:
            pending_scope = group_id or user_id
            pending = _clf_agent.get_pending(pending_scope)
            folder_result = _clf_agent.submit_pending_folder_name(pending_scope, user_msg.strip())
            if folder_result:
                reply_message(reply_token, folder_result)
                continue
            if pending and user_msg.strip().isdigit():
                choice = int(user_msg.strip())
                log(f"  待歸檔選擇：{choice}")
                reply_message(reply_token, _clf_agent.execute_pending_option(pending_scope, choice))
                continue
            if pending and user_msg.strip() in {"待歸檔", "查詢待歸檔"}:
                reply_message(reply_token, _clf_agent.format_pending_menu(pending_scope))
                continue
            if pending and user_msg.strip().upper() == "NA":
                count = len(pending.get("items", []))
                _clf_agent.clear_pending(pending_scope, remove_file=True)
                reply_message(reply_token, f"🗑️ 已取消歸檔，刪除 {count} 個待歸檔項目。")
                continue

        # ── 999 / 5168 快捷鍵優先（不被任何 awaiting 狀態攔截）──────
        _scope = group_id or user_id
        if user_msg.strip() == "999":
            if _clf_agent:
                result = _clf_agent.clear_mode()
                reply_message(reply_token, result)
            else:
                reply_message(reply_token, "⚠️ 歸類模式功能暫時無法使用")
            continue
        if user_msg.strip() == "5168":
            _exec_menu_active[_scope] = True
            # 清除所有等待狀態，避免殘留
            _awaiting_person_for_mode.pop(_scope, None)
            _awaiting_exec_input.pop(_scope, None)
            _awaiting_prospect_selection.pop(_scope, None)
            _awaiting_prospect_file.pop(_scope, None)
            _awaiting_invite_selection.pop(_scope, None)
            _awaiting_partner_invite_category.pop(_scope, None)
            _awaiting_partner_invite_person.pop(_scope, None)
            _awaiting_partner_invite_meeting.pop(_scope, None)
            _awaiting_invite_manage_select.pop(_scope, None)
            _awaiting_invite_manage_action.pop(_scope, None)
            _awaiting_invite_manage_edit.pop(_scope, None)
            reply_message(reply_token, EXEC_MENU_TEXT)
            continue

        # ── 等待執行選單後續輸入時，NA 可取消 ────────────────────────
        if user_msg.strip().upper() == "NA" and (
            _awaiting_person_for_mode.get(_scope) or _awaiting_exec_input.get(_scope)
            or _awaiting_prospect_selection.get(_scope) or _awaiting_prospect_file.get(_scope)
            or _awaiting_invite_selection.get(_scope)
            or _awaiting_partner_invite_category.get(_scope)
            or _awaiting_partner_invite_person.get(_scope)
            or _awaiting_partner_invite_meeting.get(_scope)
            or _awaiting_invite_manage_select.get(_scope)
            or _awaiting_invite_manage_action.get(_scope)
            or _awaiting_invite_manage_edit.get(_scope)
        ):
            _awaiting_person_for_mode.pop(_scope, None)
            _awaiting_exec_input.pop(_scope, None)
            _awaiting_prospect_selection.pop(_scope, None)
            _awaiting_prospect_file.pop(_scope, None)
            _awaiting_invite_selection.pop(_scope, None)
            _awaiting_partner_invite_category.pop(_scope, None)
            _awaiting_partner_invite_person.pop(_scope, None)
            _awaiting_partner_invite_meeting.pop(_scope, None)
            _awaiting_invite_manage_select.pop(_scope, None)
            _awaiting_invite_manage_action.pop(_scope, None)
            _awaiting_invite_manage_edit.pop(_scope, None)
            reply_message(reply_token, "↩️ 已取消，返回待機。")
            continue

        if _looks_like_explicit_command(user_msg) and (
            _awaiting_partner_invite_category.get(_scope)
            or _awaiting_partner_invite_person.get(_scope)
            or _awaiting_partner_invite_meeting.get(_scope)
        ):
            _awaiting_partner_invite_category.pop(_scope, None)
            _awaiting_partner_invite_person.pop(_scope, None)
            _awaiting_partner_invite_meeting.pop(_scope, None)
            _awaiting_invite_manage_select.pop(_scope, None)
            _awaiting_invite_manage_action.pop(_scope, None)
            _awaiting_invite_manage_edit.pop(_scope, None)

        if _awaiting_invite_manage_edit.get(_scope):
            state = _awaiting_invite_manage_edit[_scope]
            if state.get("step") == "confirm" and user_msg.strip().isdigit():
                choice = int(user_msg.strip())
                if choice == 1:
                    _awaiting_invite_manage_edit[_scope] = {"step": "edit", "record": state["record"]}
                    reply_message(reply_token, "📝 請直接輸入新的邀約文宣內容，NA 取消")
                    continue
                _awaiting_invite_manage_edit.pop(_scope, None)
                reply_message(reply_token, "已取消修改邀約文宣")
                continue
            if state.get("step") == "confirm":
                reply_message(reply_token, "⚠️ 請輸入 1 或 2，NA 取消")
                continue

            rec = state["record"]
            _awaiting_invite_manage_edit.pop(_scope, None)
            new_content = user_msg.strip()
            if not new_content:
                reply_message(reply_token, "⚠️ 新內容不可空白，NA 取消")
                continue
            course = _load_course_invite()
            ok = course.update_invite(rec["meeting"]["id"], rec.get("name", ""), new_content)
            reply_message(reply_token, "✅ 已更新邀約文宣" if ok else "⚠️ 找不到該筆邀約文宣")
            continue

        if _awaiting_invite_manage_action.get(_scope) and user_msg.strip().isdigit():
            rec = _awaiting_invite_manage_action.pop(_scope)
            choice = int(user_msg.strip())
            if choice == 1:
                _awaiting_invite_manage_edit[_scope] = {"step": "confirm", "record": rec}
                reply_message(reply_token, _format_invite_edit_confirm(rec))
                continue
            if choice == 2:
                def _run_regen(rec=rec, push_target=push_target):
                    try:
                        course = _load_course_invite()
                        if rec.get("role") == "prospect":
                            result = course.generate_prospect_invite_for_meeting(rec["name"], rec["meeting"])
                        else:
                            result = course.generate_partner_invite_for_meeting(rec["name"], rec["meeting"])
                        push_message(push_target, result if result else "⚠️ AI 無回應，請稍後再試")
                    except Exception as e:
                        push_message(push_target, f"✗ 強制重新產生失敗：{e}")
                reply_message(reply_token, f"⏳ 正在強制重新產生「{rec['name']} × {rec['meeting']['title']}」邀約文宣...")
                threading.Thread(target=_run_regen, daemon=True).start()
                continue
            reply_message(reply_token, "⚠️ 請輸入 1 或 2，NA 取消")
            continue

        if _awaiting_invite_manage_select.get(_scope) and user_msg.strip().isdigit():
            rows = _awaiting_invite_manage_select.pop(_scope)
            idx = int(user_msg.strip())
            if not (1 <= idx <= len(rows)):
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(rows)} 的編號，NA 取消")
                continue
            rec = rows[idx - 1]
            _awaiting_invite_manage_action[_scope] = rec
            reply_message(reply_token, _format_invite_manage_actions(rec))
            continue

        if _awaiting_partner_invite_category.get(_scope):
            if _looks_like_explicit_command(user_msg):
                _awaiting_partner_invite_category.pop(_scope, None)
            else:
                category = _normalize_partner_category_choice(user_msg)
                if not category:
                    reply_message(reply_token, "⚠️ 請輸入 1、2、3 或 A、B、C，NA 取消")
                    continue
                people = _partners_by_category(category)
                _awaiting_partner_invite_category.pop(_scope, None)
                if not people:
                    reply_message(reply_token, f"⚠️ 目前沒有分類 {category} 的夥伴。")
                    continue
                _awaiting_partner_invite_person[_scope] = {"category": category, "people": people}
                reply_message(reply_token, _format_partner_choice_menu(category, people))
                continue

        if _awaiting_partner_invite_person.get(_scope) and user_msg.strip().isdigit():
            state = _awaiting_partner_invite_person[_scope]
            people = state["people"]
            idx = int(user_msg.strip())
            if not (1 <= idx <= len(people)):
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(people)} 的編號，NA 取消")
                continue
            person = people[idx - 1]
            course = _load_course_invite()
            meetings = course.list_meetings()
            _awaiting_partner_invite_person.pop(_scope, None)
            if not meetings:
                reply_message(reply_token, "⚠️ 目前沒有排定的課程會議，請先新增課程會議。")
                continue
            _awaiting_partner_invite_meeting[_scope] = {"name": person.get("name", ""), "meetings": meetings}
            reply_message(reply_token, _format_meeting_choice_menu(person.get("name", ""), meetings))
            continue

        if _awaiting_partner_invite_meeting.get(_scope) and user_msg.strip().isdigit():
            state = _awaiting_partner_invite_meeting.pop(_scope)
            meetings = state["meetings"]
            idx = int(user_msg.strip())
            if not (1 <= idx <= len(meetings)):
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(meetings)} 的編號，NA 取消")
                continue
            meeting = meetings[idx - 1]
            person_name = state["name"]
            def _run_partner_invite(name=person_name, meeting=meeting, push_target=push_target):
                try:
                    course = _load_course_invite()
                    result = course.generate_partner_invite_for_meeting(name, meeting)
                    push_message(push_target, result if result else "⚠️ AI 無回應，請稍後再試")
                except Exception as e:
                    push_message(push_target, f"✗ 邀約文宣產生失敗：{e}")
            reply_message(reply_token, f"⏳ 正在為「{person_name} × {meeting['title']}」產生邀約文宣...")
            threading.Thread(target=_run_partner_invite, daemon=True).start()
            continue

        # ── 加入潛在家人資訊：選擇人員後設定歸檔模式 ────────────────
        if _awaiting_prospect_file.get(_scope) and user_msg.strip().isdigit():
            rows = _awaiting_prospect_file.pop(_scope)
            idx = int(user_msg.strip())
            if 1 <= idx <= len(rows):
                person_name = rows[idx - 1].get("姓名", "")
                try:
                    clf_mod = _load_classifier()
                    result = clf_mod.ClassifierAgent().set_mode("市場開發", person_name)
                    reply_message(reply_token, result + "\n\n📸 現在直接上傳照片或檔案，會自動歸入該潛在家人資料夾。")
                except Exception as e:
                    reply_message(reply_token, f"⚠️ 設定失敗：{e}")
            else:
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(rows)} 的編號，NA 取消")
            continue

        # ── 潛在家人編號選擇（查詢詳情）──────────────────────────────
        if _awaiting_prospect_selection.get(_scope) and user_msg.strip().isdigit():
            rows = _awaiting_prospect_selection[_scope]
            idx = int(user_msg.strip())
            if 1 <= idx <= len(rows):
                detail = _format_prospect_detail(rows[idx - 1])
                reply_message(reply_token, detail)
            else:
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(rows)} 的編號，NA 取消")
            continue

        # ── 邀約組合編號選擇 → 產生邀約文宣 ─────────────────────────
        if _awaiting_invite_selection.get(_scope) and user_msg.strip().isdigit():
            combos = _awaiting_invite_selection.pop(_scope)
            idx = int(user_msg.strip())
            if 1 <= idx <= len(combos):
                combo = combos[idx - 1]
                def _run_invite_combo(combo=combo, push_target=push_target):
                    try:
                        course = _load_course_invite()
                        if combo["role"] == "prospect":
                            result = course.generate_prospect_invite_for_meeting(
                                combo["name"], combo["meeting"]
                            )
                        else:
                            result = course.generate_partner_invite_for_meeting(
                                combo["name"], combo["meeting"]
                            )
                        push_message(push_target, result if result else "⚠️ AI 無回應，請稍後再試")
                    except Exception as e:
                        push_message(push_target, f"✗ 邀約文宣產生失敗：{e}")
                reply_message(reply_token, f"⏳ 正在為「{combo['name']} × {combo['meeting']['title']}」產生邀約文宣...")
                threading.Thread(target=_run_invite_combo, daemon=True).start()
            else:
                reply_message(reply_token, f"⚠️ 請輸入 1～{len(combos)} 的編號，NA 取消")
            continue

        # ── 等待人物名稱輸入 → 設定模式 ──────────────────────────────
        if _awaiting_person_for_mode.get(_scope):
            mode_name = _awaiting_person_for_mode.pop(_scope)
            person_name = user_msg.strip()
            try:
                clf_mod = _load_classifier()
                result = clf_mod.ClassifierAgent().set_mode(mode_name, person_name)
                reply_message(reply_token, result)
            except Exception as e:
                reply_message(reply_token, f"⚠️ 設定失敗：{e}")
            continue

        # (999 / 5168 已在上方優先處理)

        # ── 執行選單：數字選擇 / NA 取消 ─────────────────────────
        _exec_scope = group_id or user_id
        if _exec_menu_active.get(_exec_scope) and user_msg.strip().upper() == "NA":
            _exec_menu_active[_exec_scope] = False
            reply_message(reply_token, "↩️ 已取消，返回待機。")
            continue
        if _exec_menu_active.get(_exec_scope) and user_msg.strip().isdigit():
            choice = int(user_msg.strip())
            _exec_menu_active[_exec_scope] = False
            item = EXEC_MENU_ITEMS.get(choice)
            if not item:
                reply_message(reply_token, f"⚠️ 無效選項 {choice}，請輸入 1～{len(EXEC_MENU_ITEMS)}")
            elif item["prompt"]:
                _awaiting_exec_input[_exec_scope] = True
                reply_message(reply_token, item["prompt"])
            elif item.get("ask_person"):
                # 需要先輸入人物名稱再設定模式
                _awaiting_person_for_mode[_exec_scope] = item["ask_person"]
                reply_message(reply_token, f"👤 請輸入人物名稱：")
            elif item.get("prospect_file"):
                # 顯示潛在家人編號清單，等待使用者選擇後設定歸檔模式
                try:
                    market = _load_market_dev()
                    rows = market.MarketDevAgent().list_prospects()
                    if not rows:
                        reply_message(reply_token, "📋 目前沒有潛在家人資料。\n請先新增：小幫手 新增潛在家人 姓名|職業|管道|備註")
                    else:
                        _awaiting_prospect_file[_exec_scope] = rows
                        lines = ["📂 選擇要歸檔的潛在家人\n輸入編號後直接上傳照片或檔案，NA 取消\n"]
                        for i, r in enumerate(rows, 1):
                            star = "⭐" * int(r["AI評分"]) if r.get("AI評分", "").isdigit() else "─"
                            lines.append(f"{i}. {r.get('姓名','')}　{r.get('職業','')}　{star}")
                        reply_message(reply_token, "\n".join(lines))
                except Exception as e:
                    reply_message(reply_token, f"⚠️ 載入名單失敗：{e}")
            elif item.get("reset_person"):
                # 安麗產品分類：直接設定模式，不繼承目前人員
                try:
                    clf_mod = _load_classifier()
                    result = clf_mod.ClassifierAgent().set_mode(item["cmd"], "")
                    reply_message(reply_token, result)
                except Exception as e:
                    reply_message(reply_token, f"⚠️ 設定失敗：{e}")
            else:
                handle_training_command(item["cmd"], reply_token, user_id, group_id)
            continue

        # ── 觸發詞檢查 ─────────────────────────────────────────
        content = extract_trigger(user_msg)
        if content is None:
            if _clf_agent and _mode_info["mode"] == "auto":
                _clf_agent.stage_text(user_msg, pending_scope)
                schedule_pending_menu(_clf_agent, pending_scope, push_target)
                continue
            # 歸類模式：無觸發詞的文字先暫存，回傳選單讓使用者確認
            if _mode_info["mode"] != "auto" and _clf_agent:
                log(f"  歸類模式({_mode_info['mode']})：暫存文字，等待確認")
                _clf_agent.stage_text(user_msg, pending_scope)
                schedule_pending_menu(_clf_agent, pending_scope, push_target)
            else:
                log("  略過（無觸發詞）")
            continue

        log(f"  觸發詞符合，內容：{content[:40]}")
        _awaiting_exec_input.pop(group_id or user_id, None)

        # 執行選單 — 顯示數字選單並進入等待狀態
        if content.strip() == "執行選單":
            _exec_scope = group_id or user_id
            _exec_menu_active[_exec_scope] = True
            reply_message(reply_token, EXEC_MENU_TEXT)
            continue

        # 查詢指令 — 回傳所有可用指令說明
        if content.strip() in ("查詢", "指令", "help", "?", "？", "指令集", "所有指令", "commands"):
            reply_message(reply_token, HELP_TEXT)
            continue

        # 培訓記錄指令優先
        group_id = event.get("source", {}).get("groupId", "")
        if handle_training_command(content, reply_token, user_id, group_id):
            continue

        # 一般意圖回覆
        intent = analyze_intent(content)
        log(f"  意圖：{intent['意圖']} | 情緒：{intent['情緒']} | 行動：{intent['建議行動']}")
        update_status(user_id, intent)
        reply_message(reply_token, intent["建議回覆"])

    return "OK"


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
        if state.get("step") == "action" and cmd.strip().isdigit():
            rec = state["record"]
            choice = int(cmd.strip())
            if choice == 1:
                _web_invite_manage_state["web"] = {"step": "confirm_edit", "record": rec}
                return _format_invite_edit_confirm(rec)
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
        # Calendar
        cal = _load_calendar()
        result = cal.handle_calendar_command(cmd)
        if result:
            return result
    except Exception as e:
        pass

    try:
        # Partner
        partner = _load_partner()
        result = partner.handle_partner_command(cmd)
        if result:
            return result
    except Exception as e:
        pass

    try:
        # Classifier modes / archive queries
        clf_mod = _load_classifier()

        if cmd.startswith("歸類模式") or cmd.startswith("關閉歸類模式"):
            clf = clf_mod.ClassifierAgent()
            return clf.handle_command(cmd)

        if cmd.startswith("查詢歸檔"):
            clf = clf_mod.ClassifierAgent()
            person = cmd.replace("查詢歸檔", "").strip() or None
            result = clf.query_archive(person)
            if NGROK_URL:
                result = f"{result}\n\n📁 歸檔瀏覽器：{NGROK_URL}/archive"
            return result

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

        if cmd.startswith("新增潛在家人"):
            return market.MarketDevAgent().handle_add_prospect(cmd)

        if cmd.startswith("查詢潛在家人"):
            keyword = cmd.replace("查詢潛在家人", "").strip() or None
            rows = market.MarketDevAgent().list_prospects(keyword)
            if not rows:
                return "目前沒有潛在家人資料。"
            lines = ["📋 潛在家人名單："]
            for i, r in enumerate(rows, 1):
                star = "⭐" * int(r["AI評分"]) if r.get("AI評分", "").isdigit() else ""
                lines.append(f"{i}. {r.get('姓名','')}　{r.get('職業','')}　{star}")
            return "\n".join(lines)

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
        # Training agent
        training = _load_training_agent()
        if cmd.startswith("培訓"):
            return training.TrainingAgent().handle_query(cmd)
    except Exception as e:
        return f"⚠️ 培訓指令錯誤：{e}"

    try:
        # Course meeting & invite
        _course_prefixes = (
            "新增課程會議", "查詢課程會議", "刪除課程會議", "修改課程會議", "從行事曆加入課程",
            "新增課程文宣", "查詢課程文宣", "優化課程文宣",
            "查詢已產生的今日之後會議邀約文宣", "修改已產生的今日之後會議邀約文宣",
            "邀約文宣 潛在家人", "邀約文宣 跟進夥伴",
            "課程會議", "課程文宣", "課程",
        )
        if any(cmd.startswith(p) for p in _course_prefixes):
            course = _load_course_invite()

            if cmd.strip() == "查詢已產生的今日之後會議邀約文宣":
                rows = course.list_upcoming_invites(today_only_after=True)
                if not rows:
                    return "目前沒有今日之後已產生的會議邀約文宣。"
                _web_invite_manage_state["web"] = {"step": "select", "rows": rows}
                return _format_invite_manage_list(rows)

            # 無姓名 → 顯示組合清單
            if cmd.strip() in ("邀約文宣 潛在家人", "邀約文宣 跟進夥伴"):
                if cmd.strip() == "邀約文宣 跟進夥伴":
                    _web_partner_invite_state["web"] = {"step": "category"}
                    return _partner_category_menu()
                role = "prospect" if "潛在家人" in cmd else "partner"
                meetings = course.list_meetings()
                if not meetings:
                    return "⚠️ 目前沒有排定的課程會議，請先新增課程會議。"
                import csv as _csv_web
                if role == "prospect":
                    prospects_csv = BASE_DIR / "output" / "csv_data" / "market_list.csv"
                    person_key = "姓名"
                    people = []
                    if prospects_csv.exists():
                        with open(prospects_csv, encoding="utf-8-sig", newline="") as _f:
                            people = list(_csv_web.DictReader(_f))
                    if not people:
                        return "⚠️ 目前沒有潛在家人資料，請先新增。"
                else:
                    import json as _json_pw
                    partners_json = BASE_DIR / "output" / "partners" / "partners.json"
                    person_key = "姓名"
                    raw_partners = []
                    if partners_json.exists():
                        with open(partners_json, encoding="utf-8") as _f:
                            raw_partners = _json_pw.load(_f)
                    people = [{"姓名": p.get("name", "")} for p in raw_partners if p.get("name")]
                    if not people:
                        return "⚠️ 目前沒有夥伴資料，請先新增夥伴。"
                combos = []
                for p in people:
                    for m in meetings:
                        combos.append({"name": p.get(person_key, ""), "role": role, "meeting": m})
                        if len(combos) >= 20:
                            break
                    if len(combos) >= 20:
                        break
                _web_invite_combos["web"] = combos
                lines = [f"📋 邀約組合清單（共 {len(combos)} 組）\n輸入編號產生邀約文宣，NA 取消\n"]
                for i, c in enumerate(combos, 1):
                    when = c["meeting"]["date"] + (f" {c['meeting']['time']}" if c["meeting"].get("time") else "")
                    existing = course.get_invite(c["meeting"]["id"], c["name"])
                    marker = f"[EXISTS:{c['meeting']['id']}:{c['name']}]" if existing else ""
                    lines.append(f"{i}. {c['name']} × {c['meeting']['title']}（{when}）{marker}")
                return "\n".join(lines)

            result = course.CourseInviteAgent().handle_command(cmd)
            return result if result else "⚠️ 課程指令無結果"
    except Exception as e:
        return f"⚠️ 課程邀約指令錯誤：{e}"

    try:
        # Followup
        followup = _load_followup()
        if cmd.startswith("跟進報告"):
            return followup.FollowupAgent().generate_report_text()
    except Exception as e:
        return f"⚠️ 跟進報告錯誤：{e}"

    try:
        # Motivation
        motivation = _load_motivation()
        if cmd.startswith("激勵") or cmd.startswith("里程碑"):
            return motivation.MotivationAgent().handle_realtime(cmd)
    except Exception as e:
        return f"⚠️ 激勵指令錯誤：{e}"

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


def _render_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Yisheng 助理</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --blue: #007AFF;
    --blue-light: #E3F0FF;
    --green: #34C759;
    --green-light: #E6F9ED;
    --bg: #F2F2F7;
    --surface: #FFFFFF;
    --border: #D1D1D6;
    --text: #1C1C1E;
    --text-secondary: #6C6C70;
    --sidebar-width: 280px;
    --header-height: 56px;
    --bottom-bar-height: 64px;
  }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); height: 100dvh; overflow: hidden; display: flex; flex-direction: column; }

  /* Header */
  #header {
    position: sticky; top: 0; z-index: 100;
    height: var(--header-height);
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px; padding: 0 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
  }
  #header h1 { font-size: 17px; font-weight: 600; flex: 1; }
  #status-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 3px var(--green-light);
    transition: background .3s;
  }
  #status-dot.loading { background: #FF9500; box-shadow: 0 0 0 3px #FFF3E0; }
  #archive-btn {
    font-size: 13px; color: var(--blue);
    background: var(--blue-light); border: none; border-radius: 8px;
    padding: 5px 10px; cursor: pointer; text-decoration: none;
    display: flex; align-items: center; gap: 4px;
  }
  #archive-btn:hover { opacity: .85; }

  /* Layout */
  #layout { flex: 1; display: flex; overflow: hidden; }

  /* Sidebar */
  #sidebar {
    width: var(--sidebar-width);
    background: var(--surface);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    flex-shrink: 0;
    display: flex; flex-direction: column;
  }
  .sidebar-section { border-bottom: 1px solid var(--border); }
  .sidebar-section-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; cursor: pointer;
    font-size: 13px; font-weight: 600; color: var(--text-secondary);
    user-select: none;
    background: #FAFAFA;
  }
  .sidebar-section-header:hover { background: var(--blue-light); color: var(--blue); }
  .sidebar-section-header .arrow { transition: transform .2s; font-size: 11px; }
  .sidebar-section-header.open .arrow { transform: rotate(90deg); }
  .sidebar-items { display: none; padding: 4px 0; }
  .sidebar-items.open { display: block; }
  .sidebar-item {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 18px; cursor: pointer;
    font-size: 14px; border: none; background: transparent;
    width: 100%; text-align: left; color: var(--text);
    transition: background .15s;
  }
  .sidebar-item:hover { background: var(--blue-light); color: var(--blue); }
  .sidebar-item.exec { color: var(--blue); font-weight: 500; }

  /* Chat area */
  #chat-wrapper { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  #chat {
    flex: 1; overflow-y: auto; padding: 16px 12px;
    display: flex; flex-direction: column; gap: 10px;
  }
  .msg { display: flex; max-width: 80%; animation: fadeIn .25s ease; }
  .msg.user { align-self: flex-end; flex-direction: row-reverse; }
  .msg.bot  { align-self: flex-start; }
  .bubble {
    padding: 10px 14px; border-radius: 16px;
    font-size: 14px; line-height: 1.55; white-space: pre-wrap; word-break: break-word;
  }
  .msg.user .bubble { background: var(--blue); color: #fff; border-bottom-right-radius: 4px; }
  .msg.bot  .bubble { background: var(--blue-light); color: var(--text); border-bottom-left-radius: 4px; }
  .msg-time { font-size: 11px; color: var(--text-secondary); margin: 4px 6px; align-self: flex-end; }

  /* Pending menu */
  #pending-panel {
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 10px 12px;
    display: none;
  }
  #pending-panel.visible { display: block; }
  #pending-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }
  #pending-btns { display: flex; flex-wrap: wrap; gap: 6px; }
  .pending-btn {
    background: var(--blue); color: #fff;
    border: none; border-radius: 8px; padding: 7px 12px;
    font-size: 13px; cursor: pointer; transition: opacity .15s;
  }
  .pending-btn:hover { opacity: .85; }

  /* Bottom bar */
  #bottom-bar {
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 8px 12px;
    display: flex; gap: 8px; align-items: flex-end;
    min-height: var(--bottom-bar-height);
  }
  #cmd-input {
    flex: 1; border: 1.5px solid var(--border); border-radius: 12px;
    padding: 9px 14px; font-size: 15px; background: var(--bg);
    resize: none; outline: none; max-height: 120px; overflow-y: auto;
    font-family: inherit; transition: border-color .2s;
  }
  #cmd-input:focus { border-color: var(--blue); }
  #send-btn {
    background: var(--blue); color: #fff; border: none;
    border-radius: 50%; width: 40px; height: 40px;
    font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: opacity .2s;
  }
  #send-btn:hover { opacity: .85; }
  #send-btn:disabled { opacity: .4; cursor: default; }
  #upload-btn {
    background: var(--bg); border: 1.5px solid var(--border); color: var(--text-secondary);
    border-radius: 50%; width: 40px; height: 40px;
    font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: background .2s;
  }
  #upload-btn:hover { background: var(--blue-light); color: var(--blue); border-color: var(--blue); }
  #file-input { display: none; }

  /* Spinner */
  .spinner-msg .bubble {
    display: flex; align-items: center; gap: 6px;
    background: var(--bg); border: 1px solid var(--border);
  }
  .spinner {
    width: 16px; height: 16px; border: 2px solid var(--border);
    border-top-color: var(--blue); border-radius: 50%;
    animation: spin .7s linear infinite;
  }

  @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Mobile */
  @media (max-width: 640px) {
    #sidebar { display: none; }
    #mobile-tabs {
      display: flex; overflow-x: auto; background: var(--surface);
      border-bottom: 1px solid var(--border); padding: 0 4px;
      flex-shrink: 0; gap: 4px;
    }
    .tab-btn {
      flex-shrink: 0; padding: 8px 12px; border: none; background: transparent;
      font-size: 13px; color: var(--text-secondary); cursor: pointer; white-space: nowrap;
      border-bottom: 2px solid transparent; transition: color .2s, border-color .2s;
    }
    .tab-btn.active { color: var(--blue); border-bottom-color: var(--blue); }
    #mobile-drawer {
      background: var(--surface); border-bottom: 1px solid var(--border);
      padding: 8px 0; display: none; max-height: 200px; overflow-y: auto;
    }
    #mobile-drawer.open { display: block; }
    .drawer-item {
      display: block; padding: 9px 18px; width: 100%; text-align: left;
      border: none; background: transparent; font-size: 14px; cursor: pointer;
    }
    .drawer-item:hover { background: var(--blue-light); color: var(--blue); }
  }
  @media (min-width: 641px) {
    #mobile-tabs, #mobile-drawer { display: none !important; }
  }
</style>
</head>
<body>

<div id="header">
  <h1>🤖 Yisheng 助理</h1>
  <div id="status-dot" title="就緒"></div>
  <a href="/archive" id="archive-btn" target="_blank">📁 歸檔</a>
</div>

<!-- Mobile tabs -->
<div id="mobile-tabs">
  <button class="tab-btn active" onclick="openTab('市場開發')">🎯 市場</button>
  <button class="tab-btn" onclick="openTab('培訓系統')">📚 培訓</button>
  <button class="tab-btn" onclick="openTab('夥伴陪伴')">🤝 夥伴</button>
  <button class="tab-btn" onclick="openTab('行事曆')">🗓️ 行事曆</button>
  <button class="tab-btn" onclick="openTab('歸類模式')">📂 歸類</button>
  <button class="tab-btn" onclick="openTab('培訓記錄')">📖 記錄</button>
  <button class="tab-btn" onclick="openTab('安麗產品歸檔')">🛍️ 安麗</button>
  <button class="tab-btn" onclick="openTab('故事分類')">📝 故事</button>
  <button class="tab-btn" onclick="openTab('課程邀約')">🎓 課程</button>
  <button class="tab-btn" onclick="openTab('說明')">❓ 說明</button>
</div>
<div id="mobile-drawer"></div>

<div id="layout">
  <!-- Sidebar -->
  <div id="sidebar" id="sidebar-desktop"></div>

  <!-- Chat + panels -->
  <div id="chat-wrapper">
    <div id="chat"></div>

    <!-- Pending menu panel -->
    <div id="pending-panel">
      <div id="pending-title">📋 待處理選項</div>
      <div id="pending-btns"></div>
    </div>

    <!-- Bottom bar -->
    <div id="bottom-bar">
      <input type="file" id="file-input" accept="*/*">
      <button id="upload-btn" title="上傳檔案" onclick="document.getElementById('file-input').click()">📎</button>
      <textarea id="cmd-input" rows="1" placeholder="輸入指令…" onkeydown="handleKey(event)"></textarea>
      <button id="send-btn" onclick="sendCommand()" title="送出">➤</button>
    </div>
  </div>
</div>

<script>
// ── Menu data ──
const MENU_GROUPS = [
  {
    label: "🎯 市場開發",
    key: "市場開發",
    items: [
      { label: "新增潛在家人", prompt: "新增潛在家人 姓名|職業|管道|備註" },
      { label: "查詢潛在家人", cmd: "查詢潛在家人" },
      { label: "加入潛在家人資訊", prompt: "潛在家人資料 " },
    ]
  },
  {
    label: "📚 培訓系統",
    key: "培訓系統",
    items: [
      { label: "查詢培訓進度", prompt: "培訓 " },
    ]
  },
  {
    label: "🤝 夥伴陪伴",
    key: "夥伴陪伴",
    items: [
      { label: "跟進報告", cmd: "跟進報告" },
      { label: "激勵夥伴", prompt: "激勵 " },
      { label: "里程碑記錄", prompt: "里程碑 " },
      { label: "查詢所有夥伴", cmd: "查詢夥伴" },
      { label: "查詢待跟進夥伴", cmd: "查詢待跟進夥伴" },
      { label: "新增夥伴", prompt: "新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類" },
      { label: "更新夥伴", prompt: "更新夥伴 姓名 | 層級 | 近況 | 下次跟進日期 | 聯絡資訊 | 備註 | 類型 | 編號 | 合夥人 | 推薦人 | 到期日 | 年月 | 一年內新上獎銜 | 首次獎金% | 現金抵用券 | 購物積點 | 優惠券 | 本月購貨 | 上月購貨 | 前2月購貨 | 前3月購貨 | 分類" },
      { label: "跟進夥伴", prompt: "跟進夥伴 姓名 | 狀態 | 下次跟進日期 | 備註" },
    ]
  },
  {
    label: "🗓️ 行事曆",
    key: "行事曆",
    items: [
      { label: "查詢今日行事曆", cmd: "查詢行事曆" },
      { label: "查詢過往行事曆", cmd: "查詢過往行事曆" },
      { label: "新增行事曆事件", prompt: "新增行事曆 YYYY-MM-DD HH:MM 標題 | 備註" },
    ]
  },
  {
    label: "📂 歸類模式",
    key: "歸類模式",
    items: [
      { label: "查詢目前歸類模式", cmd: "歸類模式" },
      { label: "設定歸類模式", prompt: "歸類模式 " },
      { label: "關閉歸類模式", cmd: "關閉歸類模式" },
      { label: "查詢所有歸檔", cmd: "查詢歸檔" },
      { label: "查詢指定人員歸檔", prompt: "查詢歸檔 " },
    ]
  },
  {
    label: "📖 培訓記錄",
    key: "培訓記錄",
    items: [
      { label: "整理今日培訓記錄", cmd: "整理" },
      { label: "再次整理培訓記錄", cmd: "再次整理" },
    ]
  },
  {
    label: "🛍️ 安麗產品歸檔",
    key: "安麗產品歸檔",
    items: [
      { label: "💊 營養保健 (Nutrilite)", cmd: "營養保健歸檔" },
      { label: "💄 美容保養 (Artistry)", cmd: "美容保養歸檔" },
      { label: "🧹 居家清潔 (Amway Home)", cmd: "居家清潔歸檔" },
      { label: "🪥 個人護理 (Glister)", cmd: "個人護理歸檔" },
      { label: "🍳 廚具與生活用品", cmd: "廚具生活歸檔" },
      { label: "💧 空氣與水處理設備", cmd: "空水設備歸檔" },
      { label: "⚖️ 體重管理與運動營養", cmd: "體重管理歸檔" },
      { label: "🌸 香氛與個人風格", cmd: "香氛風格歸檔" },
      { label: "🛠️ 事業工具與教育系統", cmd: "事業工具歸檔" },
    ]
  },
  {
    label: "📝 故事分類",
    key: "故事分類",
    items: [
      { label: "👤 人物故事歸檔", prompt: "潛在家人資料 " },
      { label: "📖 產品故事歸檔", cmd: "產品故事歸檔" },
    ]
  },
  {
    label: "🎓 課程邀約",
    key: "課程邀約",
    items: [
      { label: "查詢課程會議", cmd: "查詢課程會議" },
      { label: "新增課程會議", prompt: "新增課程會議 YYYY-MM-DD HH:MM 標題|地點|說明" },
      { label: "從行事曆加入課程", prompt: "從行事曆加入課程 " },
      { label: "刪除課程會議", prompt: "刪除課程會議 COURSE-" },
      { label: "查詢課程文宣", cmd: "查詢課程文宣" },
      { label: "新增課程文宣", prompt: "新增課程文宣 標題|內文" },
      { label: "優化課程文宣", prompt: "優化課程文宣 PROMO-" },
      { label: "邀約文宣－潛在家人", prompt: "邀約文宣 潛在家人 " },
      { label: "邀約文宣－跟進夥伴", prompt: "邀約文宣 跟進夥伴 " },
      { label: "查詢已產生的邀約文宣", cmd: "查詢已產生的今日之後會議邀約文宣" },
      { label: "修改已產生的邀約文宣", prompt: "修改已產生的今日之後會議邀約文宣 COURSE-XXXX | 姓名 | 新內容" },
    ]
  },
  {
    label: "❓ 說明",
    key: "說明",
    items: [
      { label: "顯示所有指令", cmd: "指令集" },
      { label: "執行選單", cmd: "執行選單" },
    ]
  },
];

// ── Build sidebar ──
function buildSidebar(container) {
  container.innerHTML = '';
  MENU_GROUPS.forEach((group, gi) => {
    const section = document.createElement('div');
    section.className = 'sidebar-section';

    const hdr = document.createElement('div');
    hdr.className = 'sidebar-section-header';
    hdr.innerHTML = `${group.label} <span class="arrow">▶</span>`;
    hdr.onclick = () => {
      hdr.classList.toggle('open');
      items.classList.toggle('open');
      // Update mobile tabs active state
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    };

    const items = document.createElement('div');
    items.className = 'sidebar-items';
    group.items.forEach(item => {
      const btn = document.createElement('button');
      btn.className = 'sidebar-item' + (item.cmd && !item.prompt ? ' exec' : '');
      btn.textContent = item.label;
      btn.onclick = () => clickMenuItem(item);
      items.appendChild(btn);
    });

    section.appendChild(hdr);
    section.appendChild(items);
    container.appendChild(section);
  });
}

buildSidebar(document.getElementById('sidebar'));

// ── Mobile tabs ──
let currentTab = null;
function openTab(key) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  const activeBtn = [...document.querySelectorAll('.tab-btn')].find(b => b.textContent.includes(
    key === '市場開發' ? '市場' : key === '培訓系統' ? '培訓' : key === '夥伴陪伴' ? '夥伴' :
    key === '行事曆' ? '行事曆' : key === '歸類模式' ? '歸類' : key === '培訓記錄' ? '記錄' :
    key === '安麗產品歸檔' ? '安麗' : key === '故事分類' ? '故事' : key === '課程邀約' ? '課程' : '說明'
  ));
  if (activeBtn) activeBtn.classList.add('active');

  const drawer = document.getElementById('mobile-drawer');
  if (currentTab === key) {
    drawer.classList.remove('open');
    currentTab = null;
    return;
  }
  currentTab = key;
  drawer.innerHTML = '';
  const group = MENU_GROUPS.find(g => g.key === key);
  if (!group) return;
  group.items.forEach(item => {
    const btn = document.createElement('button');
    btn.className = 'drawer-item';
    btn.textContent = item.label;
    btn.onclick = () => { drawer.classList.remove('open'); currentTab = null; clickMenuItem(item); };
    drawer.appendChild(btn);
  });
  drawer.classList.add('open');
}

// ── Menu item click ──
function clickMenuItem(item) {
  if (item.cmd && !item.prompt) {
    sendCommand(item.cmd);
  } else if (item.prompt) {
    const input = document.getElementById('cmd-input');
    input.value = item.prompt;
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
    autoResize(input);
  }
}

// ── Chat helpers ──
function now() {
  return new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
}

function addMessage(text, role) {
  const chat = document.getElementById('chat');
  const wrap = document.createElement('div');
  wrap.className = 'msg ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  const time = document.createElement('div');
  time.className = 'msg-time';
  time.textContent = now();
  wrap.appendChild(bubble);
  wrap.appendChild(time);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

function addSpinner() {
  const chat = document.getElementById('chat');
  const wrap = document.createElement('div');
  wrap.className = 'msg bot spinner-msg';
  wrap.innerHTML = '<div class="bubble"><div class="spinner"></div><span>處理中…</span></div>';
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

function setLoading(on) {
  const dot = document.getElementById('status-dot');
  const btn = document.getElementById('send-btn');
  const inp = document.getElementById('cmd-input');
  dot.className = on ? 'loading' : '';
  btn.disabled = on;
  inp.disabled = on;
}

// ── Send command ──
async function sendCommand(forcedCmd) {
  const input = document.getElementById('cmd-input');
  const cmd = (forcedCmd !== undefined ? forcedCmd : input.value).trim();
  if (!cmd) return;

  if (!forcedCmd) input.value = '';
  autoResize(input);
  addMessage(cmd, 'user');
  setLoading(true);
  const spinner = addSpinner();

  try {
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd })
    });
    const data = await res.json();
    spinner.remove();
    addMessage(data.result || '（無回應）', 'bot');
  } catch(e) {
    spinner.remove();
    addMessage('⚠️ 連線失敗：' + e.message, 'bot');
  } finally {
    setLoading(false);
  }
}

// ── File upload ──
document.getElementById('file-input').addEventListener('change', async function() {
  const file = this.files[0];
  if (!file) return;
  this.value = '';
  await handleFileUpload(file);
});

async function handleFileUpload(file) {
  addMessage('📎 上傳：' + file.name, 'user');
  setLoading(true);
  const spinner = addSpinner();
  const fd = new FormData();
  fd.append('file', file, file.name);
  try {
    const res = await fetch('/api/upload', { method: 'POST', body: fd });
    const data = await res.json();
    spinner.remove();
    if (data.result) {
      addMessage(data.result, 'bot');
      await refreshPending();
    } else {
      addMessage('（上傳完成，無待處理選項）', 'bot');
    }
  } catch(e) {
    spinner.remove();
    addMessage('⚠️ 上傳失敗：' + e.message, 'bot');
  } finally {
    setLoading(false);
  }
}

// ── Pending menu ──
async function refreshPending() {
  try {
    const res = await fetch('/api/pending');
    const data = await res.json();
    if (data.result) {
      showPendingMenu(data.result);
    } else {
      hidePendingMenu();
    }
  } catch(e) {}
}

function showPendingMenu(menuText) {
  const panel = document.getElementById('pending-panel');
  const btns = document.getElementById('pending-btns');
  btns.innerHTML = '';
  // Parse numbered options from menu text
  const lines = menuText.split('\\n');
  lines.forEach(line => {
    const m = line.match(/^(\\d+)[.)、]/);
    if (m) {
      const choice = parseInt(m[1]);
      const btn = document.createElement('button');
      btn.className = 'pending-btn';
      btn.textContent = line.trim();
      btn.onclick = () => executePending(choice);
      btns.appendChild(btn);
    }
  });
  // Also add a cancel button
  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'pending-btn';
  cancelBtn.style.background = '#8E8E93';
  cancelBtn.textContent = '✕ 取消';
  cancelBtn.onclick = () => { executePending(0); hidePendingMenu(); };
  btns.appendChild(cancelBtn);
  panel.classList.add('visible');
}

function hidePendingMenu() {
  document.getElementById('pending-panel').classList.remove('visible');
  document.getElementById('pending-btns').innerHTML = '';
}

async function executePending(choice) {
  setLoading(true);
  const spinner = addSpinner();
  try {
    const res = await fetch('/api/pending/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ choice: choice })
    });
    const data = await res.json();
    spinner.remove();
    addMessage(data.result || '（已執行）', 'bot');
    hidePendingMenu();
  } catch(e) {
    spinner.remove();
    addMessage('⚠️ 執行失敗：' + e.message, 'bot');
  } finally {
    setLoading(false);
  }
}

// ── Input helpers ──
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendCommand();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

document.getElementById('cmd-input').addEventListener('input', function() {
  autoResize(this);
});

// ── Init ──
addMessage('你好！我是 Yisheng 助理 🤖 請使用左側選單或直接輸入指令。', 'bot');
refreshPending();
</script>
</body>
</html>"""


def _render_dashboard_html_v2() -> str:
    return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Yisheng 助理</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --blue:#007AFF;--blue-lt:#E3F0FF;--green:#34C759;--green-lt:#E6F9ED;
  --red:#FF3B30;--gray:#8E8E93;--bg:#F2F2F7;--surface:#FFF;
  --border:#D1D1D6;--text:#1C1C1E;--text2:#6C6C70;--radius:12px;
  --sidebar:270px;--hdr:52px;
}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg);color:var(--text);height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#hdr{height:var(--hdr);background:var(--surface);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:10px;padding:0 16px;
  box-shadow:0 1px 3px rgba(0,0,0,.07);flex-shrink:0;z-index:50}
#hdr h1{font-size:16px;font-weight:700;flex:1}
.hbtn{font-size:12px;color:var(--blue);background:var(--blue-lt);
  border:none;border-radius:8px;padding:5px 10px;cursor:pointer;text-decoration:none}
#dot{width:9px;height:9px;border-radius:50%;background:var(--green);
  box-shadow:0 0 0 3px var(--green-lt);transition:all .3s;flex-shrink:0}
#dot.busy{background:#FF9500;box-shadow:0 0 0 3px #FFF3E0}
#body{flex:1;display:flex;overflow:hidden}
#sidebar{width:var(--sidebar);background:var(--surface);
  border-right:1px solid var(--border);overflow-y:auto;flex-shrink:0}
.sg{border-bottom:1px solid var(--border)}
.sghdr{display:flex;align-items:center;justify-content:space-between;
  padding:10px 14px;cursor:pointer;font-size:11px;font-weight:700;
  color:var(--text2);text-transform:uppercase;letter-spacing:.4px;
  background:#FAFAFA;user-select:none}
.sghdr:hover,.sghdr.open{background:var(--blue-lt);color:var(--blue)}
.sghdr .arr{font-size:10px;transition:transform .2s}
.sghdr.open .arr{transform:rotate(90deg)}
.sgitems{display:none;padding:3px 0}
.sgitems.open{display:block}
.sbtn{width:100%;text-align:left;border:none;background:transparent;
  padding:9px 16px 9px 20px;font-size:13px;color:var(--text);cursor:pointer;
  display:flex;align-items:center;justify-content:space-between;
  transition:background .12s;gap:6px}
.sbtn:hover{background:var(--blue-lt);color:var(--blue)}
.sbtn.direct .lbl{color:var(--blue);font-weight:500}
.sbtn .tag{font-size:10px;background:var(--blue);color:#fff;border-radius:4px;
  padding:1px 6px;flex-shrink:0}
.sbtn.form-btn .tag{background:var(--gray)}
#main{flex:1;display:flex;flex-direction:column;overflow:hidden}
#chat{flex:1;overflow-y:auto;padding:14px 10px;
  display:flex;flex-direction:column;gap:8px}
.msg{display:flex;max-width:88%;animation:fi .2s ease}
.msg.u{align-self:flex-end;flex-direction:row-reverse}
.msg.b{align-self:flex-start}
.bbl{padding:9px 13px;border-radius:16px;font-size:14px;
  line-height:1.6;white-space:pre-wrap;word-break:break-word}
.msg.u .bbl{background:var(--blue);color:#fff;border-bottom-right-radius:3px}
.msg.b .bbl{background:var(--blue-lt);color:var(--text);border-bottom-left-radius:3px}
.mt{font-size:10px;color:var(--text2);margin:3px 5px;align-self:flex-end}
.smsg .bbl{background:var(--bg);border:1px solid var(--border);
  display:flex;align-items:center;gap:7px}
.spin{width:15px;height:15px;border:2px solid var(--border);
  border-top-color:var(--blue);border-radius:50%;animation:sp .7s linear infinite;flex-shrink:0}
#pend{background:var(--surface);border-top:2px solid var(--blue);
  padding:10px 12px;display:none}
#pend.on{display:block}
#pendtitle{font-size:12px;font-weight:700;color:var(--blue);margin-bottom:8px}
#pendbtns{display:flex;flex-wrap:wrap;gap:6px}
.pbtn{background:var(--blue);color:#fff;border:none;border-radius:8px;
  padding:7px 11px;font-size:12px;cursor:pointer}
.pbtn:hover{opacity:.85}
.pbtn.cancel{background:var(--gray)}
#bar{background:var(--surface);border-top:1px solid var(--border);
  padding:8px 10px;display:flex;gap:7px;align-items:center;flex-shrink:0}
#upld{border:1.5px solid var(--border);border-radius:50%;width:38px;height:38px;
  font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;
  background:var(--bg);color:var(--text2);flex-shrink:0}
#upld:hover{background:var(--blue-lt);border-color:var(--blue);color:var(--blue)}
#finput{display:none}
#inp{flex:1;border:1.5px solid var(--border);border-radius:10px;
  padding:8px 12px;font-size:14px;background:var(--bg);
  outline:none;font-family:inherit;transition:border-color .2s}
#inp:focus{border-color:var(--blue)}
#sendbtn{background:var(--blue);color:#fff;border:none;border-radius:50%;
  width:38px;height:38px;font-size:16px;cursor:pointer;flex-shrink:0;
  display:flex;align-items:center;justify-content:center}
#sendbtn:disabled{opacity:.35;cursor:default}
#overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);
  z-index:200;display:none;align-items:flex-end;justify-content:center;padding:0}
#overlay.on{display:flex}
#mbox{background:var(--surface);border-radius:20px 20px 0 0;
  width:100%;max-width:520px;max-height:90dvh;overflow-y:auto;
  box-shadow:0 -4px 30px rgba(0,0,0,.2);animation:su .25s ease}
#mtitle{font-size:15px;font-weight:700;padding:18px 18px 10px;
  display:flex;align-items:center;justify-content:space-between}
#mtitle button{border:none;background:var(--bg);border-radius:50%;
  width:28px;height:28px;font-size:14px;cursor:pointer;color:var(--text2)}
#mfields{padding:6px 18px 8px;display:flex;flex-direction:column;gap:12px}
.mf label{display:block;font-size:12px;font-weight:600;color:var(--text2);margin-bottom:4px}
.mf input,.mf select,.mf textarea{
  width:100%;border:1.5px solid var(--border);border-radius:10px;
  padding:9px 12px;font-size:14px;outline:none;font-family:inherit;
  transition:border-color .2s;background:var(--bg)}
.mf input:focus,.mf select:focus,.mf textarea:focus{border-color:var(--blue)}
.mf textarea{resize:vertical;min-height:70px}
.mf input.err,.mf select.err{border-color:var(--red)!important}
#macts{display:flex;gap:8px;padding:12px 18px 20px}
#mcancel{flex:1;padding:12px;border:1.5px solid var(--border);border-radius:10px;
  background:transparent;font-size:14px;cursor:pointer;font-family:inherit}
#mok{flex:2;padding:12px;background:var(--blue);color:#fff;
  border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
#fab{display:none;position:fixed;bottom:72px;right:16px;z-index:100;
  width:54px;height:54px;border-radius:50%;background:var(--blue);color:#fff;
  border:none;font-size:24px;box-shadow:0 4px 16px rgba(0,0,0,.25);cursor:pointer;
  align-items:center;justify-content:center}
#mobmenu{position:fixed;inset:0;z-index:150;display:none;flex-direction:column}
#mobmenu.on{display:flex}
#mobbg{flex:0 0 80px;background:rgba(0,0,0,.45)}
#mobsheet{flex:1;background:var(--surface);overflow-y:auto;
  border-radius:20px 20px 0 0;padding-bottom:env(safe-area-inset-bottom,16px)}
#mobclose{width:100%;padding:14px;border:none;background:transparent;
  font-size:13px;color:var(--text2);cursor:pointer;border-bottom:1px solid var(--border)}
.mgg{border-bottom:1px solid var(--border)}
.mgghdr{font-size:11px;font-weight:700;color:var(--text2);text-transform:uppercase;
  letter-spacing:.4px;padding:12px 18px 4px}
.mgbtn{width:100%;text-align:left;border:none;background:transparent;
  padding:12px 18px;font-size:14px;cursor:pointer;display:flex;align-items:center;
  justify-content:space-between;border-bottom:1px solid #F2F2F7}
.mgbtn:active,.mgbtn:hover{background:var(--blue-lt)}
.mgbtn.direct .lbl{color:var(--blue);font-weight:500}
.mgbtn .mtag{font-size:11px;color:var(--text2)}
@keyframes fi{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
@keyframes su{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:none}}
@keyframes sp{to{transform:rotate(360deg)}}
@media(max-width:639px){#sidebar{display:none}#fab{display:flex}}
@media(min-width:640px){#fab,#mobmenu{display:none!important}}
</style>
</head>
<body>
<div id="hdr">
  <h1>🤖 Yisheng 助理</h1>
  <div id="dot"></div>
  <a href="/archive" class="hbtn" target="_blank">📁 歸檔瀏覽器</a>
</div>
<div id="body">
  <div id="sidebar"></div>
  <div id="main">
    <div id="chat"></div>
    <div id="pend"><div id="pendtitle">📋 待歸檔選項</div><div id="pendbtns"></div></div>
    <div id="bar">
      <input type="file" id="finput" accept="*/*">
      <button id="upld" title="上傳檔案" onclick="document.getElementById('finput').click()">📎</button>
      <input id="inp" type="text" placeholder="或直接輸入指令…" onkeydown="if(event.key==='Enter')doSend()">
      <button id="sendbtn" onclick="doSend()">➤</button>
    </div>
  </div>
</div>
<div id="overlay" onclick="if(event.target===this)closeModal()">
  <div id="mbox">
    <div id="mtitle"><span id="mtitletext"></span><button onclick="closeModal()">✕</button></div>
    <div id="mfields"></div>
    <div id="macts">
      <button id="mcancel" onclick="closeModal()">取消</button>
      <button id="mok" onclick="submitModal()">執行 ➤</button>
    </div>
  </div>
</div>
<button id="fab" onclick="openMob()">☰</button>
<div id="mobmenu">
  <div id="mobbg" onclick="closeMob()"></div>
  <div id="mobsheet">
    <button id="mobclose" onclick="closeMob()">✕ 關閉選單</button>
    <div id="mobcont"></div>
  </div>
</div>
<script>
const AMODES=["會議記錄","行事曆","夥伴跟進","市場開發","培訓資料","一般歸檔",
  "整理會議心得","歸檔會議紀錄","歸檔行動紀錄","歸檔文件","421故事歸檔","課程文宣歸檔"];
const GROUPS=[
  {label:"🎯 市場開發",items:[
    {label:"新增潛在家人",tag:"表單",form:{title:"新增潛在家人",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"例：張三"},
              {id:"j",lbl:"職業",type:"text",ph:"例：業務員"},
              {id:"c",lbl:"接觸管道",type:"text",ph:"例：朋友介紹"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"}],
      build:function(v){return "新增潛在家人 "+v.n+"|"+v.j+"|"+v.c+"|"+v.r;}}},
    {label:"查詢潛在家人",tag:"執行",cmd:"查詢潛在家人"},
    {label:"加入潛在家人資訊",tag:"表單",form:{title:"加入潛在家人資訊",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"請輸入潛在家人姓名"}],
      build:function(v){return "潛在家人資料 "+v.n;}}},
  ]},
  {label:"📚 培訓系統",items:[
    {label:"查詢培訓進度",tag:"表單",form:{title:"查詢培訓進度",
      fields:[{id:"n",lbl:"夥伴名稱",type:"text",req:1,ph:"例：建德"}],
      build:function(v){return "培訓 "+v.n;}}},
  ]},
  {label:"🤝 夥伴陪伴",items:[
    {label:"跟進報告",tag:"執行",cmd:"跟進報告"},
    {label:"激勵夥伴",tag:"表單",form:{title:"激勵夥伴",
      fields:[{id:"n",lbl:"夥伴名稱",type:"text",req:1,ph:"例：建德"},
              {id:"s",lbl:"情境說明（選填）",type:"textarea",ph:"例：最近業績下滑"}],
      build:function(v){return "激勵 "+v.n+(v.s?" "+v.s:"");}}},
    {label:"里程碑記錄",tag:"表單",form:{title:"里程碑記錄",
      fields:[{id:"n",lbl:"夥伴名稱",type:"text",req:1,ph:"例：建德"},
              {id:"a",lbl:"成就描述",type:"textarea",ph:"例：首次達成業績目標"}],
      build:function(v){return "里程碑 "+v.n+(v.a?" "+v.a:"");}}},
    {label:"查詢所有夥伴",tag:"執行",cmd:"查詢夥伴"},
    {label:"查詢待跟進夥伴",tag:"執行",cmd:"查詢待跟進夥伴"},
    {label:"新增夥伴",tag:"表單",form:{title:"新增夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"姓名"},
              {id:"g",lbl:"目標",type:"text",ph:"例：月入三萬"},
              {id:"d",lbl:"下次跟進日期",type:"date"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"},
              {id:"c",lbl:"分類",type:"select",opts:["A","B","C"]}],
      build:function(v){return "新增夥伴 "+v.n+" | "+v.g+" | "+v.d+" | "+v.r+" | "+v.c;}}},
    {label:"更新夥伴",tag:"表單",form:{title:"更新夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"姓名"},
              {id:"l",lbl:"層級",type:"text",ph:"例：1"},
              {id:"s",lbl:"近況",type:"text",ph:"例：持續跟進"},
              {id:"d",lbl:"下次跟進日期",type:"date"},
              {id:"ci",lbl:"聯絡資訊",type:"text",ph:"例：LINE:abc123"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"},
              {id:"t",lbl:"類型",type:"text",ph:"例：直銷商"},
              {id:"no",lbl:"編號",type:"text",ph:"例：7519213"},
              {id:"p",lbl:"合夥人",type:"text",ph:"例：王小明"},
              {id:"sp",lbl:"推薦人",type:"text",ph:"例：陳薾云"},
              {id:"ed",lbl:"到期日",type:"date"},
              {id:"ym",lbl:"年月",type:"text",ph:"例：2026-03"},
              {id:"rt",lbl:"一年內新上獎銜",type:"text",ph:"例：翡翠"},
              {id:"fb",lbl:"首次獎金%",type:"text",ph:"例：3%"},
              {id:"cv",lbl:"現金抵用券",type:"text",ph:"例：有"},
              {id:"sp2",lbl:"購物積點",type:"text",ph:"例：2821"},
              {id:"cp",lbl:"優惠券",type:"text",ph:"例：有"},
              {id:"m1",lbl:"本月購貨",type:"text",ph:"例：V"},
              {id:"m2",lbl:"上月購貨",type:"text",ph:"例：V"},
              {id:"m3",lbl:"前2月購貨",type:"text",ph:"例：V"},
              {id:"m4",lbl:"前3月購貨",type:"text",ph:"例：V"},
              {id:"cg",lbl:"分類",type:"select",opts:["","A","B","C"]}],
      build:function(v){return "更新夥伴 "+v.n+" | "+v.l+" | "+v.s+" | "+v.d+" | "+v.ci+" | "+v.r+" | "+v.t+" | "+v.no+" | "+v.p+" | "+v.sp+" | "+v.ed+" | "+v.ym+" | "+v.rt+" | "+v.fb+" | "+v.cv+" | "+v.sp2+" | "+v.cp+" | "+v.m1+" | "+v.m2+" | "+v.m3+" | "+v.m4+" | "+v.cg;}}},
    {label:"跟進夥伴",tag:"表單",form:{title:"跟進夥伴",
      fields:[{id:"n",lbl:"姓名",type:"text",req:1,ph:"姓名"},
              {id:"s",lbl:"狀態",type:"text",ph:"例：持續跟進"},
              {id:"d",lbl:"下次跟進日期",type:"date"},
              {id:"r",lbl:"備註",type:"textarea",ph:"補充資訊"}],
      build:function(v){return "跟進夥伴 "+v.n+" | "+v.s+" | "+v.d+" | "+v.r;}}},
  ]},
  {label:"🗓️ 行事曆",items:[
    {label:"查詢今日行事曆",tag:"執行",cmd:"查詢行事曆"},
    {label:"查詢過往行事曆",tag:"執行",cmd:"查詢過往行事曆"},
    {label:"查詢全部行事曆",tag:"執行",cmd:"查詢全部行事曆"},
    {label:"新增行事曆事件",tag:"表單",form:{title:"新增行事曆事件",
      fields:[{id:"d",lbl:"日期",type:"date",req:1},
              {id:"t",lbl:"時間（選填）",type:"time"},
              {id:"ti",lbl:"標題",type:"text",req:1,ph:"活動名稱"},
              {id:"r",lbl:"備註（選填）",type:"textarea",ph:"補充說明"}],
      build:function(v){return "新增行事曆 "+v.d+(v.t?" "+v.t:"")+" "+v.ti+(v.r?" | "+v.r:"");}}},
  ]},
  {label:"📂 歸類模式",items:[
    {label:"查詢目前歸類模式",tag:"執行",cmd:"歸類模式"},
    {label:"設定歸類模式",tag:"表單",form:{title:"設定歸類模式",
      fields:[{id:"m",lbl:"歸類模式",type:"select",req:1,opts:AMODES},
              {id:"p",lbl:"人員名稱（選填）",type:"text",ph:"例：建德"},
              {id:"d",lbl:"日期（選填）",type:"date"}],
      build:function(v){var c="歸類模式";if(v.p)c+=" "+v.p;c+=" "+v.m;if(v.d)c+=" "+v.d;return c;}}},
    {label:"關閉歸類模式",tag:"執行",cmd:"關閉歸類模式"},
    {label:"查詢所有歸檔",tag:"執行",cmd:"查詢歸檔"},
    {label:"查詢指定人員歸檔",tag:"表單",form:{title:"查詢指定人員歸檔",
      fields:[{id:"n",lbl:"人員名稱",type:"text",req:1,ph:"例：建德"}],
      build:function(v){return "查詢歸檔 "+v.n;}}},
  ]},
  {label:"📖 培訓記錄",items:[
    {label:"整理今日培訓記錄",tag:"執行",cmd:"整理"},
    {label:"整理指定日期記錄",tag:"表單",form:{title:"整理指定日期記錄",
      fields:[{id:"d",lbl:"日期",type:"date",req:1}],
      build:function(v){return "整理 "+v.d.replace(/-/g,"");}}},
    {label:"再次整理（強制覆蓋）",tag:"執行",cmd:"再次整理"},
    {label:"查詢培訓記錄",tag:"表單",form:{title:"查詢指定日期培訓記錄",
      fields:[{id:"d",lbl:"日期",type:"date",req:1}],
      build:function(v){return "MTG-"+v.d.replace(/-/g,"");}}},
  ]},
  {label:"🛍️ 安麗產品歸檔",items:[
    {label:"💊 營養保健 (Nutrilite)",tag:"執行",cmd:"營養保健歸檔"},
    {label:"💄 美容保養 (Artistry)",tag:"執行",cmd:"美容保養歸檔"},
    {label:"🧹 居家清潔 (Amway Home)",tag:"執行",cmd:"居家清潔歸檔"},
    {label:"🪥 個人護理 (Glister)",tag:"執行",cmd:"個人護理歸檔"},
    {label:"🍳 廚具與生活用品",tag:"執行",cmd:"廚具生活歸檔"},
    {label:"💧 空氣與水處理設備",tag:"執行",cmd:"空水設備歸檔"},
    {label:"⚖️ 體重管理與運動營養",tag:"執行",cmd:"體重管理歸檔"},
    {label:"🌸 香氛與個人風格",tag:"執行",cmd:"香氛風格歸檔"},
    {label:"🛠️ 事業工具與教育系統",tag:"執行",cmd:"事業工具歸檔"},
  ]},
  {label:"📝 故事分類",items:[
    {label:"👤 人物故事歸檔",tag:"表單",form:{title:"人物故事歸檔",
      fields:[{id:"n",lbl:"人物名稱",type:"text",req:1,ph:"例：建德"}],
      build:function(v){return "潛在家人資料 "+v.n;}}},
    {label:"📖 產品故事歸檔",tag:"執行",cmd:"產品故事歸檔"},
  ]},
  {label:"🎓 課程邀約",items:[
    {label:"查詢課程會議",tag:"執行",cmd:"查詢課程會議"},
    {label:"新增課程會議",tag:"表單",form:{title:"新增課程會議",
      fields:[{id:"d",lbl:"日期",type:"date",req:1},
              {id:"t",lbl:"時間（選填）",type:"time"},
              {id:"ti",lbl:"標題",type:"text",req:1,ph:"例：四月OPP說明會"},
              {id:"lo",lbl:"地點（選填）",type:"text",ph:"例：台中大里店"},
              {id:"r",lbl:"說明（選填）",type:"textarea",ph:"例：歡迎帶朋友"},
              {id:"sp",lbl:"演講貴賓（選填）",type:"text",ph:"例：鑽石李大明"},
              {id:"spb",lbl:"貴賓介紹（選填）",type:"textarea",ph:"例：20年資深鑽石，擅長事業說明與激勵"},
              {id:"tp",lbl:"課程主題（選填）",type:"text",ph:"例：Amway事業機會介紹"},
              {id:"tpd",lbl:"主題介紹（選填）",type:"textarea",ph:"例：從零到鑽石的實戰分享，含產品體驗與收入模型"}],
      build:function(v){
        var s="新增課程會議 "+v.d+(v.t?" "+v.t:"")+" "+v.ti;
        var ext=[v.lo||"",v.r||"",v.sp||"",v.spb||"",v.tp||"",v.tpd||""];
        var last=-1;
        for(var i=ext.length-1;i>=0;i--){if(ext[i]){last=i;break;}}
        if(last>=0){for(var i=0;i<=last;i++)s+="|"+(ext[i]||"");}
        return s;}}},
    {label:"從行事曆加入課程",tag:"表單",form:{title:"從行事曆加入課程",
      fields:[{id:"k",lbl:"關鍵字（選填）",type:"text",ph:"例：OPP、培訓"}],
      build:function(v){return "從行事曆加入課程"+(v.k?" "+v.k:"");}}},
    {label:"修改課程會議",tag:"表單",form:{title:"修改課程會議",
      fields:[{id:"id",lbl:"課程 ID（COURSE-XXXX）",type:"text",req:1,ph:"先查詢課程會議取得 ID"},
              {id:"ti",lbl:"標題（選填）",type:"text",ph:"留空＝不修改"},
              {id:"d",lbl:"日期（選填）",type:"date"},
              {id:"t",lbl:"時間（選填）",type:"time"},
              {id:"lo",lbl:"地點（選填）",type:"text",ph:"留空＝不修改"},
              {id:"r",lbl:"說明（選填）",type:"textarea",ph:"留空＝不修改"},
              {id:"sp",lbl:"演講貴賓（選填）",type:"text",ph:"留空＝不修改"},
              {id:"spb",lbl:"貴賓介紹（選填）",type:"textarea",ph:"留空＝不修改"},
              {id:"tp",lbl:"課程主題（選填）",type:"text",ph:"留空＝不修改"},
              {id:"tpd",lbl:"主題介紹（選填）",type:"textarea",ph:"留空＝不修改"}],
      build:function(v){
        var MAP={ti:"標題",d:"日期",t:"時間",lo:"地點",r:"說明",sp:"演講貴賓",spb:"貴賓介紹",tp:"課程主題",tpd:"主題介紹"};
        var pairs=[];
        Object.keys(MAP).forEach(function(k){if(v[k])pairs.push(MAP[k]+":"+v[k]);});
        if(!pairs.length)return "修改課程會議 "+v.id+" 標題:（請填寫至少一個欄位）";
        return "修改課程會議 "+v.id+" "+pairs.join("|");}}},
    {label:"刪除課程會議",tag:"表單",form:{title:"刪除課程會議",
      fields:[{id:"id",lbl:"課程 ID（COURSE-XXXX）",type:"text",req:1,ph:"先查詢課程會議取得 ID"}],
      build:function(v){return "刪除課程會議 "+v.id;}}},
    {label:"查詢課程文宣",tag:"執行",cmd:"查詢課程文宣"},
    {label:"新增課程文宣",tag:"表單",form:{title:"新增課程文宣",
      fields:[{id:"ti",lbl:"標題",type:"text",req:1,ph:"例：四月OPP邀約文宣"},
              {id:"c",lbl:"內文",type:"textarea",req:1,ph:"輸入文宣內容"}],
      build:function(v){return "新增課程文宣 "+v.ti+"|"+v.c;}}},
    {label:"優化課程文宣（AI）",tag:"表單",form:{title:"優化課程文宣",
      fields:[{id:"id",lbl:"文宣 ID（PROMO-XXXX）",type:"text",req:1,ph:"先查詢課程文宣取得 ID"}],
      build:function(v){return "優化課程文宣 "+v.id;}}},
    {label:"邀約文宣－潛在家人（AI）",tag:"表單",form:{title:"潛在家人邀約文宣",
      fields:[{id:"n",lbl:"姓名（選填，空白＝通用）",type:"text",ph:"例：Amy"}],
      build:function(v){return "邀約文宣 潛在家人"+(v.n?" "+v.n:"");}}},
    {label:"邀約文宣－跟進夥伴（AI）",tag:"表單",form:{title:"跟進夥伴邀約文宣",
      fields:[{id:"n",lbl:"姓名（選填，空白＝通用）",type:"text",ph:"例：建德"}],
      build:function(v){return "邀約文宣 跟進夥伴"+(v.n?" "+v.n:"");}}},
    {label:"查詢已產生的邀約文宣",tag:"執行",cmd:"查詢已產生的今日之後會議邀約文宣"},
    {label:"修改已產生的邀約文宣",tag:"表單",form:{title:"修改已產生的邀約文宣",
      fields:[{id:"id",lbl:"課程 ID（COURSE-XXXX）",type:"text",req:1,ph:"先查詢已產生的邀約文宣取得 ID"},
              {id:"n",lbl:"姓名",type:"text",req:1,ph:"例：吳建德"},
              {id:"c",lbl:"新內容",type:"textarea",req:1,ph:"輸入修改後的邀約文宣"}],
      build:function(v){return "修改已產生的今日之後會議邀約文宣 "+v.id+" | "+v.n+" | "+v.c;}}},
  ]},
  {label:"❓ 說明",items:[
    {label:"顯示所有指令",tag:"執行",cmd:"指令集"},
  ]},
];
// Build sidebar
function buildSB(){
  var sb=document.getElementById("sidebar");sb.innerHTML="";
  GROUPS.forEach(function(g){
    var sec=document.createElement("div");sec.className="sg";
    var hdr=document.createElement("div");hdr.className="sghdr";
    hdr.innerHTML=g.label+' <span class="arr">▶</span>';
    var items=document.createElement("div");items.className="sgitems";
    hdr.onclick=function(){hdr.classList.toggle("open");items.classList.toggle("open");};
    g.items.forEach(function(item){
      var b=document.createElement("button");
      b.className="sbtn"+(item.cmd&&!item.form?" direct":"")+(item.form?" form-btn":"");
      b.innerHTML='<span class="lbl">'+item.label+'</span><span class="tag">'+item.tag+'</span>';
      b.onclick=function(){clickItem(item);};
      items.appendChild(b);
    });
    sec.appendChild(hdr);sec.appendChild(items);sb.appendChild(sec);
  });
}
buildSB();
// Build mobile menu
function buildMob(){
  var c=document.getElementById("mobcont");c.innerHTML="";
  GROUPS.forEach(function(g){
    var gh=document.createElement("div");gh.className="mgg";
    var ghl=document.createElement("div");ghl.className="mgghdr";ghl.textContent=g.label;
    gh.appendChild(ghl);
    g.items.forEach(function(item){
      var b=document.createElement("button");
      b.className="mgbtn"+(item.cmd&&!item.form?" direct":"");
      b.innerHTML='<span class="lbl">'+item.label+'</span><span class="mtag">'+item.tag+'</span>';
      b.onclick=function(){closeMob();clickItem(item);};
      gh.appendChild(b);
    });
    c.appendChild(gh);
  });
}
buildMob();
function openMob(){document.getElementById("mobmenu").classList.add("on");}
function closeMob(){document.getElementById("mobmenu").classList.remove("on");}
// Modal
var _build=null;
function clickItem(item){
  if(item.cmd&&!item.form){doSend(item.cmd);}
  else if(item.form){openModal(item.form);}
}
function openModal(f){
  _build=f.build;
  document.getElementById("mtitletext").textContent=f.title||"";
  var mf=document.getElementById("mfields");mf.innerHTML="";
  f.fields.forEach(function(fd){
    var w=document.createElement("div");w.className="mf";
    var l=document.createElement("label");
    l.textContent=fd.lbl+(fd.req?" *":"");l.setAttribute("for","mf_"+fd.id);
    w.appendChild(l);
    var el;
    if(fd.type==="select"){
      el=document.createElement("select");el.id="mf_"+fd.id;
      if(!fd.req){var o=document.createElement("option");o.value="";o.textContent="（選填）";el.appendChild(o);}
      (fd.opts||[]).forEach(function(o){var oe=document.createElement("option");oe.value=o;oe.textContent=o;el.appendChild(oe);});
    } else if(fd.type==="textarea"){
      el=document.createElement("textarea");el.id="mf_"+fd.id;
      el.placeholder=fd.ph||"";el.rows=3;
    } else {
      el=document.createElement("input");el.id="mf_"+fd.id;
      el.type=fd.type||"text";el.placeholder=fd.ph||"";
      if(fd.req)el.required=true;
      if(fd.type==="date")el.value=new Date().toISOString().split("T")[0];
    }
    w.appendChild(el);mf.appendChild(w);
  });
  document.getElementById("overlay").classList.add("on");
  var first=mf.querySelector("input,select,textarea");
  if(first)setTimeout(function(){first.focus();},120);
}
function closeModal(){
  document.getElementById("overlay").classList.remove("on");_build=null;
}
function submitModal(){
  var mf=document.getElementById("mfields");
  var vals={};var ok=true;
  mf.querySelectorAll("input,select,textarea").forEach(function(el){
    var id=el.id.replace("mf_","");
    el.classList.remove("err");
    if(el.required&&!el.value.trim()){el.classList.add("err");ok=false;}
    else{vals[id]=el.value.trim();}
  });
  if(!ok){mf.querySelector(".err").focus();return;}
  var cmd=_build(vals);
  closeModal();doSend(cmd);
}
// Chat
function nt(){return new Date().toLocaleTimeString("zh-TW",{hour:"2-digit",minute:"2-digit"});}
function addMsg(text,role){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg "+role;
  var b=document.createElement("div");b.className="bbl";b.textContent=text;
  var t=document.createElement("div");t.className="mt";t.textContent=nt();
  w.appendChild(b);w.appendChild(t);chat.appendChild(w);
  chat.scrollTop=chat.scrollHeight;return w;
}
function addSpin(){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b smsg";
  w.innerHTML='<div class="bbl"><div class="spin"></div><span>處理中…</span></div>';
  chat.appendChild(w);chat.scrollTop=chat.scrollHeight;return w;
}
function setBusy(on){
  document.getElementById("dot").className=on?"busy":"";
  document.getElementById("sendbtn").disabled=on;
  document.getElementById("inp").disabled=on;
}
async function doSend(forced){
  var inp=document.getElementById("inp");
  var cmd=(forced!==undefined?forced:inp.value).trim();
  if(!cmd)return;
  if(forced===undefined)inp.value="";
  addMsg(cmd,"u");setBusy(true);var sp=addSpin();
  try{
    var r=await fetch("/api/command",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({command:cmd})});
    var d=await r.json();sp.remove();
    var txt=d.result||"（無回應）";
    addMsg(txt,"b");
    if(txt.startsWith("📋 邀約組合清單")){addInviteComboButtons(txt);}
    else if(txt.startsWith("📨 今日之後已產生的會議邀約文宣")){addInviteManageButtons(txt);}
    else if(txt.startsWith("🛠️ 邀約文宣管理")){addInviteManageActionButtons();}
    else if(txt.startsWith("📝 是否修改這份邀約文宣")){addInviteEditConfirmButtons();}
    else if(txt.startsWith("📋 潛在家人名單")){addListButtons(txt,"潛在家人詳情");}
    else if(txt.startsWith("👤 ")){var nm=txt.split("\\n")[0].replace("👤 ","").split(/[\s　]/)[0];if(nm)addDetailButtons(nm);}
  }catch(e){sp.remove();addMsg("⚠️ 連線失敗："+e.message,"b");}
  finally{setBusy(false);}
}
function addInviteManageButtons(txt){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;flex-direction:column;gap:6px;padding:4px 0";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\d+)\.\s+(.+)/);
    if(!m)return;
    var n=m[1],desc=m[2];
    var b=document.createElement("button");
    b.style.cssText="background:#007AFF;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;width:100%";
    b.textContent=n+". "+desc+"  👉 管理這筆文宣";
    (function(ni){b.onclick=function(){doSend(ni);};})(n);
    wrap.appendChild(b);
  });
  if(wrap.children.length>0){w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;}
}
function addInviteManageActionButtons(){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;gap:8px;flex-wrap:wrap;padding:4px 0";
  [["1","📝 修改已產生文宣"],["2","🔁 強制重新產生"]].forEach(function(it){
    var b=document.createElement("button");
    b.style.cssText="background:#5856D6;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
    b.textContent=it[1];
    b.onclick=function(){doSend(it[0]);};
    wrap.appendChild(b);
  });
  w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;
}
function addInviteEditConfirmButtons(){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;gap:8px;flex-wrap:wrap;padding:4px 0";
  [["1","✅ 確定修改"],["2","取消"]].forEach(function(it){
    var b=document.createElement("button");
    b.style.cssText="background:#34C759;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
    if(it[0]==="2"){b.style.background="#8E8E93";}
    b.textContent=it[1];
    b.onclick=function(){doSend(it[0]);};
    wrap.appendChild(b);
  });
  w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;
}
function addDetailButtons(name){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");wrap.style.cssText="display:flex;gap:8px;flex-wrap:wrap;padding:4px 0";
  var eb=document.createElement("button");
  eb.style.cssText="background:#34C759;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
  eb.textContent="✏️ 編輯基本資料";eb.onclick=function(){openEditProspect(name);};
  var xb=document.createElement("button");
  xb.style.cssText="background:#FF9500;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer";
  xb.textContent="📝 新增體驗記錄";xb.onclick=function(){openAddExperience(name);};
  wrap.appendChild(eb);wrap.appendChild(xb);w.appendChild(wrap);
  chat.appendChild(w);chat.scrollTop=chat.scrollHeight;
}
async function openEditProspect(name){
  setBusy(true);
  try{
    var r=await fetch("/api/prospect/"+encodeURIComponent(name));
    var d=await r.json();var row=d.result||{};
    document.getElementById("mtitletext").textContent="✏️ 維護 "+name+" 的資料";
    var mf=document.getElementById("mfields");mf.innerHTML="";
    [{id:"電話",lbl:"電話",type:"text",ph:"手機號碼"},
     {id:"地區",lbl:"地區",type:"text",ph:"例：台中市西屯區"},
     {id:"地址",lbl:"地址",type:"text",ph:"完整地址"},
     {id:"接觸狀態",lbl:"接觸狀態",type:"text",ph:"例：持續跟進"},
     {id:"下次跟進日",lbl:"下次跟進日期",type:"date"},
     {id:"使用產品",lbl:"使用產品（逗號或頓號分隔）",type:"text",ph:"例：益生菌、魚油"},
     {id:"淨水器型號",lbl:"淨水器型號",type:"text",ph:"例：eSpring E-9255"},
     {id:"濾心上次換",lbl:"濾心上次更換日期",type:"date"},
     {id:"濾心下次換",lbl:"濾心下次更換日期",type:"date"},
     {id:"備註",lbl:"備註",type:"textarea"}
    ].forEach(function(fd){
      var ww=document.createElement("div");ww.className="mf";
      var l=document.createElement("label");l.textContent=fd.lbl;ww.appendChild(l);
      var el;
      if(fd.type==="textarea"){el=document.createElement("textarea");el.rows=3;}
      else{el=document.createElement("input");el.type=fd.type;}
      el.id="mf_"+fd.id;el.placeholder=fd.ph||"";
      el.value=row[fd.id]||"";
      ww.appendChild(el);mf.appendChild(ww);
    });
    document.getElementById("overlay").classList.add("on");
    document.getElementById("mok").onclick=async function(){
      var updates={name:name};
      mf.querySelectorAll("input,textarea").forEach(function(el){updates[el.id.replace("mf_","")]=el.value.trim();});
      document.getElementById("overlay").classList.remove("on");
      document.getElementById("mok").onclick=submitModal;
      setBusy(true);var sp=addSpin();
      try{var r2=await fetch("/api/prospect/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(updates)});
        var d2=await r2.json();sp.remove();addMsg(d2.result||"（已更新）","b");
      }catch(e){sp.remove();addMsg("⚠️ "+e.message,"b");}finally{setBusy(false);}
    };
  }catch(e){addMsg("⚠️ 載入失敗："+e.message,"b");}
  finally{setBusy(false);}
}
function openAddExperience(name){
  document.getElementById("mtitletext").textContent="📝 新增體驗記錄 — "+name;
  var mf=document.getElementById("mfields");mf.innerHTML="";
  [{id:"product",lbl:"產品/食品名稱",type:"text",req:1,ph:"例：益生菌、魚油、eSpring"},
   {id:"note",lbl:"備註",type:"textarea",ph:"例：每天早上服用 2 顆，效果明顯"},
   {id:"filter_last",lbl:"濾心上次更換（若適用）",type:"date"},
   {id:"filter_next",lbl:"濾心下次更換（若適用）",type:"date"}
  ].forEach(function(fd){
    var ww=document.createElement("div");ww.className="mf";
    var l=document.createElement("label");l.textContent=fd.lbl+(fd.req?" *":"");ww.appendChild(l);
    var el;
    if(fd.type==="textarea"){el=document.createElement("textarea");el.rows=3;}
    else{el=document.createElement("input");el.type=fd.type;}
    el.id="mfe_"+fd.id;el.placeholder=fd.ph||"";if(fd.req)el.required=true;
    ww.appendChild(el);mf.appendChild(ww);
  });
  document.getElementById("overlay").classList.add("on");
  var first=mf.querySelector("input");if(first)setTimeout(function(){first.focus();},120);
  document.getElementById("mok").onclick=async function(){
    var prod=document.getElementById("mfe_product");
    if(!prod.value.trim()){prod.classList.add("err");prod.focus();return;}
    var body={name:name,product:prod.value.trim(),
      note:(document.getElementById("mfe_note")||{}).value||"",
      filter_last:(document.getElementById("mfe_filter_last")||{}).value||"",
      filter_next:(document.getElementById("mfe_filter_next")||{}).value||""};
    document.getElementById("overlay").classList.remove("on");
    document.getElementById("mok").onclick=submitModal;
    setBusy(true);var sp=addSpin();
    try{var r=await fetch("/api/prospect/experience",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      var d=await r.json();sp.remove();addMsg(d.result||"（已記錄）","b");
    }catch(e){sp.remove();addMsg("⚠️ "+e.message,"b");}finally{setBusy(false);}
  };
}
function addInviteComboButtons(txt){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;flex-direction:column;gap:6px;padding:4px 0";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\d+)\.\s+(.+)/);
    if(!m)return;
    var n=m[1];var rawDesc=m[2];
    // Parse EXISTS marker
    var existsMatch=rawDesc.match(/\[EXISTS:([^:]+):(.+)\]$/);
    var hasInvite=!!existsMatch;
    var meetingId=hasInvite?existsMatch[1]:"";
    var personName=hasInvite?existsMatch[2]:"";
    var desc=rawDesc.replace(/\[EXISTS:[^\]]+\]$/,"").trim();
    var row=document.createElement("div");
    row.style.cssText="display:flex;gap:6px;align-items:center";
    var btn=document.createElement("button");
    if(hasInvite){
      btn.style.cssText="background:#34C759;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;flex:1";
      btn.textContent=n+". "+desc+" 👉 觀看已產生的邀約文宣";
      (function(mid,pname){
        btn.onclick=function(){openInviteModal(mid,pname);};
      })(meetingId,personName);
      var genBtn=document.createElement("button");
      genBtn.style.cssText="background:#5856D6;color:#fff;border:none;border-radius:10px;padding:9px 12px;font-size:12px;cursor:pointer;white-space:nowrap";
      genBtn.textContent="重新產生";
      (function(ni){genBtn.onclick=function(){doSend(ni);};})(n);
      row.appendChild(btn);row.appendChild(genBtn);
    } else {
      btn.style.cssText="background:#5856D6;color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;flex:1";
      btn.textContent=n+". "+desc+" 👉 產生邀約文宣";
      (function(ni){btn.onclick=function(){doSend(ni);};})(n);
      row.appendChild(btn);
    }
    wrap.appendChild(row);
  });
  if(wrap.children.length>0){w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;}
}
async function openInviteModal(meetingId,name){
  var r=await fetch("/api/course-invite?id="+encodeURIComponent(meetingId)+"&name="+encodeURIComponent(name));
  var d=await r.json();
  if(!d.result){addMsg("⚠️ 找不到邀約記錄","b");return;}
  var rec=d.result;
  // Build modal
  var ov=document.createElement("div");
  ov.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:2000;display:flex;align-items:center;justify-content:center";
  var box=document.createElement("div");
  box.style.cssText="background:#fff;border-radius:16px;padding:24px;width:min(92vw,560px);display:flex;flex-direction:column;gap:12px;max-height:80vh";
  var title=document.createElement("div");
  title.style.cssText="font-weight:700;font-size:16px;color:#1c1c1e";
  title.textContent="邀約文宣 — "+name;
  var ta=document.createElement("textarea");
  ta.style.cssText="width:100%;flex:1;min-height:220px;border:1px solid #ddd;border-radius:10px;padding:10px;font-size:14px;resize:vertical;font-family:inherit;box-sizing:border-box";
  ta.value=rec.content||"";
  var meta=document.createElement("div");
  meta.style.cssText="font-size:11px;color:#8e8e93";
  meta.textContent="最後更新："+(rec.updated_at||"").replace("T"," ").slice(0,16);
  var btns=document.createElement("div");
  btns.style.cssText="display:flex;gap:10px;justify-content:flex-end";
  var saveBtn=document.createElement("button");
  saveBtn.style.cssText="background:#007AFF;color:#fff;border:none;border-radius:10px;padding:10px 20px;font-size:14px;cursor:pointer";
  saveBtn.textContent="儲存修改";
  saveBtn.onclick=async function(){
    var res=await fetch("/api/course-invite/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({meeting_id:meetingId,name:name,content:ta.value.trim()})});
    var rd=await res.json();
    addMsg(rd.result||"✅ 已更新","b");
    document.body.removeChild(ov);
  };
  var closeBtn=document.createElement("button");
  closeBtn.style.cssText="background:#f2f2f7;color:#1c1c1e;border:none;border-radius:10px;padding:10px 20px;font-size:14px;cursor:pointer";
  closeBtn.textContent="關閉";
  closeBtn.onclick=function(){document.body.removeChild(ov);};
  btns.appendChild(closeBtn);btns.appendChild(saveBtn);
  box.appendChild(title);box.appendChild(ta);box.appendChild(meta);box.appendChild(btns);
  ov.appendChild(box);
  ov.onclick=function(e){if(e.target===ov)document.body.removeChild(ov);};
  document.body.appendChild(ov);
  setTimeout(function(){ta.focus();},100);
}
function addListButtons(txt,prefix){
  var chat=document.getElementById("chat");
  var w=document.createElement("div");w.className="msg b";
  var wrap=document.createElement("div");
  wrap.style.cssText="display:flex;flex-direction:column;gap:6px;padding:4px 0";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\d+)\./);
    if(!m)return;
    var n=parseInt(m[1]);
    var btn=document.createElement("button");
    btn.style.cssText="background:var(--blue);color:#fff;border:none;border-radius:10px;padding:9px 14px;font-size:13px;cursor:pointer;text-align:left;width:100%";
    btn.textContent=line.trim()+" 👉 查看詳情";
    btn.onclick=function(){doSend(prefix+" "+n);};
    wrap.appendChild(btn);
  });
  if(wrap.children.length>0){w.appendChild(wrap);chat.appendChild(w);chat.scrollTop=chat.scrollHeight;}
}
// Upload
document.getElementById("finput").addEventListener("change",async function(){
  var f=this.files[0];if(!f)return;this.value="";
  addMsg("📎 "+f.name,"u");setBusy(true);var sp=addSpin();
  var fd=new FormData();fd.append("file",f,f.name);
  try{
    var r=await fetch("/api/upload",{method:"POST",body:fd});
    var d=await r.json();sp.remove();
    if(d.result){addMsg(d.result,"b");await refreshPend();}
    else{addMsg("✅ 上傳完成","b");}
  }catch(e){sp.remove();addMsg("⚠️ 上傳失敗："+e.message,"b");}
  finally{setBusy(false);}
});
// Pending
async function refreshPend(){
  try{var r=await fetch("/api/pending");var d=await r.json();
    if(d.result){showPend(d.result);}else{hidePend();}}catch(e){}
}
function showPend(txt){
  var btns=document.getElementById("pendbtns");btns.innerHTML="";
  txt.split("\\n").forEach(function(line){
    var m=line.match(/^(\\d+)[.)、:：]/);
    if(m){var n=parseInt(m[1]);
      var b=document.createElement("button");b.className="pbtn";
      b.textContent=line.trim();b.onclick=function(){execPend(n);};btns.appendChild(b);}
  });
  var cb=document.createElement("button");cb.className="pbtn cancel";
  cb.textContent="✕ 取消";cb.onclick=function(){execPend(0);hidePend();};btns.appendChild(cb);
  document.getElementById("pend").classList.add("on");
}
function hidePend(){
  document.getElementById("pend").classList.remove("on");
  document.getElementById("pendbtns").innerHTML="";
}
async function execPend(n){
  setBusy(true);var sp=addSpin();
  try{var r=await fetch("/api/pending/execute",{method:"POST",
      headers:{"Content-Type":"application/json"},body:JSON.stringify({choice:n})});
    var d=await r.json();sp.remove();addMsg(d.result||"（已執行）","b");hidePend();
  }catch(e){sp.remove();addMsg("⚠️ 執行失敗："+e.message,"b");}
  finally{setBusy(false);}
}
// Init
addMsg("你好！我是 Yisheng 助理 🤖\\n手機：點右下角 ☰ 開啟選單\\n電腦：點左側選單按鈕\\n上傳檔案：點 📎 按鈕","b");
refreshPend();
</script>
</body>
</html>"""


@app.route("/web")
def web_dashboard():
    return _render_dashboard_html_v2(), 200, {"Content-Type": "text/html; charset=utf-8"}


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

        clf_mod = _load_classifier()
        clf = clf_mod.ClassifierAgent()
        clf.stage_file(data, filename, file_type, "web_user",
                       content_type=content_type, source_name=filename)
        menu = clf.format_pending_menu("web_user")
        return {"result": menu}
    except Exception as e:
        return {"result": f"⚠️ 上傳失敗：{e}"}, 500


@app.route("/api/pending", methods=["GET"])
def api_pending():
    try:
        clf_mod = _load_classifier()
        clf = clf_mod.ClassifierAgent()
        menu = clf.format_pending_menu("web_user")
        return {"result": menu if menu else None}
    except Exception as e:
        return {"result": None}


@app.route("/api/pending/execute", methods=["POST"])
def api_pending_execute():
    try:
        data = request.get_json(force=True) or {}
        choice = int(data.get("choice", 0))
        clf_mod = _load_classifier()
        clf = clf_mod.ClassifierAgent()
        result = clf.execute_pending_option("web_user", choice)
        return {"result": result}
    except Exception as e:
        return {"result": f"⚠️ 執行失敗：{e}"}, 500


@app.route("/api/prospect/<name>", methods=["GET"])
def api_prospect_get(name):
    try:
        market = _load_market_dev()
        row = market.MarketDevAgent().get_prospect_by_name(name)
        if row:
            return {"result": row}
        return {"result": None}, 404
    except Exception as e:
        return {"result": None, "error": str(e)}, 500


@app.route("/api/course-invite", methods=["GET"])
def api_course_invite_get():
    try:
        meeting_id = request.args.get("id", "").strip()
        name = request.args.get("name", "").strip()
        if not meeting_id or not name:
            return {"result": None, "error": "缺少 id 或 name"}, 400
        course = _load_course_invite()
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
        course = _load_course_invite()
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
        market = _load_market_dev()
        result = market.MarketDevAgent().update_prospect_fields(name, data)
        return {"result": result}
    except Exception as e:
        return {"result": f"⚠️ 更新失敗：{e}"}, 500


@app.route("/api/prospect/experience", methods=["POST"])
def api_prospect_experience():
    try:
        data = request.get_json(force=True) or {}
        name    = data.get("name", "").strip()
        product = data.get("product", "").strip()
        if not name or not product:
            return {"result": "⚠️ 姓名和產品為必填"}, 400
        market = _load_market_dev()
        result = market.MarketDevAgent().add_experience(
            name, product,
            note=data.get("note", ""),
            filter_last=data.get("filter_last", ""),
            filter_next=data.get("filter_next", ""),
        )
        return {"result": result}
    except Exception as e:
        return {"result": f"⚠️ 新增失敗：{e}"}, 500


# ============================================================
# 📝 更新跟進狀態
# ============================================================

def update_status(user_id: str, intent: dict):
    """根據 AI 分析結果更新追蹤紀錄"""
    try:
        if SENT_LOG.exists():
            with open(SENT_LOG, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        data[f"reply_{user_id}"] = {
            "時間":    datetime.now().isoformat(),
            "意圖":    intent["意圖"],
            "情緒":    intent["情緒"],
            "建議行動": intent["建議行動"],
        }

        with open(SENT_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"  ⚠️ 狀態更新失敗：{e}")


# ============================================================
# 🚀 啟動伺服器
# ============================================================

if __name__ == "__main__":
    log("🚀 LINE Webhook 伺服器啟動")
    log("📡 本地地址：http://localhost:5000/webhook")
    log("💡 對外存取：請執行 ngrok http 5000")
    log("   複製 ngrok URL 設定到 LINE Console → Webhook URL")
    app.run(host="0.0.0.0", port=5000, debug=False)
