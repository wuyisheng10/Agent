import json
from datetime import datetime

SENT_LOG = None
log = print


def configure(sent_log, log_func):
    global SENT_LOG, log
    SENT_LOG = sent_log
    log = log_func


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
