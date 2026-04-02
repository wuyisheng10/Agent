try:
    from webhook_common import NGROK_URL
except ModuleNotFoundError:
    from agents.webhook_common import NGROK_URL


TRIGGER_WORDS = ["小幫手", "@Yisheng助理", "@Yisheng", "/yisheng"]


HELP_TEXT = """\
🤖 Yisheng 助理 指令集總覽
觸發詞：小幫手 / @Yisheng / /yisheng
────────────────────
📝 培訓記錄
  整理
    → 整理今天收到的逐字稿與圖片
  整理 YYYYMMDD
    → 整理指定日期的培訓資料
  查詢整理 [日期]
    → 查詢已整理的培訓摘要與網址
  再次整理
    → 強制重新整理今天的培訓記錄
  再次整理 [日期]
    → 強制重新整理指定日期

🔎 培訓記錄查詢
  MTG-YYYYMMDD
    → 依培訓代碼查詢摘要與網頁
    範例：MTG-20260329

📦 歸檔查詢
  查詢歸檔
    → 查詢目前已歸檔的內容與路徑

❓說明
  指令集 / help / ?
    → 顯示所有功能說明
────────────────────
摘要網頁格式：
""" + (NGROK_URL + "/summary/YYYYMMDD" if NGROK_URL else "（尚未設定 NGROK_URL）")

HELP_TEXT += """

📅 行事曆
  查詢行事曆
  查詢過往行事曆
  查詢行事曆 YYYY-MM-DD
  查詢行事曆 YYYY-MM-DD 到 YYYY-MM-DD
  查詢全部行事曆
  上傳行事曆圖片
    → 進入行事曆圖檔模式，直接上傳圖片自動整理
  新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註
  修改行事曆 EVT-xxxx YYYY-MM-DD [HH:MM] 標題 | 備註
  刪除行事曆 EVT-xxxx

🗂️ 歸檔分類
  圖片 / 音檔 / 影片 / 文件
    → 先暫存，之後再跳出分類選單
  待歸檔 / 查詢待歸檔
    → 查看目前待歸檔項目
"""

HELP_TEXT += """

🥗 營養評估系統（衛福部第八版 DRI）
  查詢營養素標準 性別 年齡 [餐別]
  營養素運作原理 營養素名稱
  列出營養素
  下載營養素標準
  開始飲食評估 性別 年齡
  設定餐別 早餐/午餐/晚餐
  評估飲食 喝水量XXXml
  飲食評估狀態
  清除飲食評估
"""

HELP_TEXT += """

🎓 課程會議邀約
  新增課程會議 YYYY-MM-DD [HH:MM] 標題|地點|說明
  查詢課程會議
  刪除課程會議 COURSE-XXXX
  從行事曆加入課程 [關鍵字]
  新增課程文宣 標題|內文
  查詢課程文宣
  優化課程文宣 PROMO-XXXX
  邀約文宣 潛在家人 [姓名]
  邀約文宣 跟進夥伴 [姓名]
  查詢已產生的今日之後會議邀約文宣
  修改已產生的今日之後會議邀約文宣 COURSE-XXXX | 姓名 | 新內容
"""

HELP_TEXT += """

🤝 夥伴經營
  新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類
  新增跟進夥伴 姓名 | 下次跟進日期 | 備註
  更新夥伴 姓名 | 層級 | 近況 | 下次跟進日期 | 聯絡資訊 | 備註 | 類型 | 編號 | 合夥人 | 推薦人 | 到期日 | 年月 | 一年內新上獎銜 | 首次獎金% | 現金抵用券 | 購物積點 | 優惠券 | 本月購貨 | 上月購貨 | 前2月購貨 | 前3月購貨 | 分類
  邀約夥伴 姓名 | 活動名稱 | 下次跟進日期 | 備註
  跟進夥伴 姓名 | 狀態 | 下次跟進日期 | 備註
  語音新增跟進夥伴
  激勵夥伴 姓名
  查詢夥伴
  查詢待跟進夥伴
  查詢夥伴 姓名
  刪除夥伴 姓名
  分類建議：A / B / C
"""

HELP_TEXT += """

👥 市場開發補充
  更新潛在家人 姓名|欄位:值|欄位:值
    可用欄位：電話、地區、地址、接觸狀態、下次跟進日、使用產品、淨水器型號、備註
"""


EXEC_MENU_ITEMS = {
    1: {"label": "新增潛在家人", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 新增潛在家人 姓名|分類|需求|備註"},
    2: {"label": "查詢潛在家人近況", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 查詢潛在家人"},
    3: {"label": "潛在家人總表", "cmd": "潛在家人總表", "prompt": None},
    4: {"label": "加入潛在家人資訊", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 潛在家人資料 姓名"},
    5: {"label": "潛在家人體驗紀錄", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 體驗紀錄 潛在家人 [姓名]"},
    6: {"label": "潛在家人濾心提醒", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 換濾心 潛在家人 [日期或天數]"},
    71: {"label": "修改潛在家人資訊", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 更新潛在家人 姓名|地區:台中西屯|地址:民生路123號|電話:0912345678"},
    7: {"label": "查詢培訓進度", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 培訓 夥伴姓名"},
    8: {"label": "跟進報告", "cmd": "跟進報告", "prompt": None},
    9: {"label": "激勵夥伴", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 激勵夥伴 姓名"},
    10: {"label": "里程碑記錄", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 里程碑 姓名 成就內容"},
    11: {"label": "查詢所有夥伴", "cmd": "查詢夥伴", "prompt": None},
    12: {"label": "查詢待跟進夥伴", "cmd": "查詢待跟進夥伴", "prompt": None},
    13: {"label": "新增夥伴", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類"},
    72: {"label": "新增跟進夥伴", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 新增跟進夥伴 姓名 | 下次跟進日期 | 備註"},
    14: {"label": "更新夥伴", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 更新夥伴 姓名 | 層級 | 近況 | 下次跟進日期 | 聯絡資訊 | 備註 | 類型 | 編號 | 合夥人 | 推薦人 | 到期日 | 年月 | 一年內新上獎銜 | 首次獎金% | 現金抵用券 | 購物積點 | 優惠券 | 本月購貨 | 上月購貨 | 前2月購貨 | 前3月購貨 | 分類"},
    15: {"label": "查詢指定夥伴", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 查詢夥伴 姓名"},
    16: {"label": "跟進夥伴", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 跟進夥伴 姓名 | 狀態 | 下次跟進日期 | 備註"},
    73: {"label": "語音新增跟進夥伴", "cmd": "語音新增跟進夥伴", "prompt": None},
    17: {"label": "刪除夥伴", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 刪除夥伴 姓名"},
    18: {"label": "查詢今日行事曆", "cmd": "查詢行事曆", "prompt": None},
    19: {"label": "查詢過往行事曆", "cmd": "查詢過往行事曆", "prompt": None},
    20: {"label": "查詢全部行事曆", "cmd": "查詢全部行事曆", "prompt": None},
    21: {"label": "上傳行事曆圖片", "cmd": "上傳行事曆圖片", "prompt": None},
    22: {"label": "手動新增行事曆", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註"},
    23: {"label": "修改行事曆", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 修改行事曆 EVT-XXXX YYYY-MM-DD [HH:MM] 標題 | 備註"},
    24: {"label": "刪除行事曆", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 刪除行事曆 EVT-XXXX"},
    25: {"label": "查詢目前歸類模式", "cmd": "歸類模式", "prompt": None},
    26: {"label": "設定歸類模式", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 歸類模式 [模式名稱]\n可用模式：會議記錄 / 行事曆 / 夥伴跟進 / 市場開發 / 培訓資料 / 一般歸檔"},
    27: {"label": "設定人員＋歸類模式", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 歸類模式 [人員名稱] [模式名稱]"},
    28: {"label": "關閉歸類模式", "cmd": "關閉歸類模式", "prompt": None},
    29: {"label": "查詢所有歸檔", "cmd": "查詢歸檔", "prompt": None},
    30: {"label": "查詢指定人員歸檔", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 查詢歸檔 [人員名稱]"},
    31: {"label": "整理今日培訓記錄", "cmd": "整理", "prompt": None},
    32: {"label": "整理指定日期記錄", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 整理 YYYYMMDD"},
    33: {"label": "再次整理（強制覆蓋）", "cmd": "再次整理", "prompt": None},
    34: {"label": "查詢培訓記錄", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 MTG-YYYYMMDD"},
    35: {"label": "顯示所有指令", "cmd": "指令集", "prompt": None},
    36: {"label": "營養保健 (Nutrilite)", "cmd": "營養保健歸檔", "prompt": None},
    37: {"label": "美容保養 (Artistry)", "cmd": "美容保養歸檔", "prompt": None},
    38: {"label": "居家清潔 (Home)", "cmd": "居家清潔歸檔", "prompt": None},
    39: {"label": "個人護理 (Glister)", "cmd": "個人護理歸檔", "prompt": None},
    40: {"label": "廚具與生活用品", "cmd": "廚具生活歸檔", "prompt": None},
    41: {"label": "空氣與水處理設備", "cmd": "空水設備歸檔", "prompt": None},
    42: {"label": "體重管理與運動營養", "cmd": "體重管理歸檔", "prompt": None},
    43: {"label": "香氛與個人風格", "cmd": "香氛風格歸檔", "prompt": None},
    44: {"label": "事業工具與教育系統", "cmd": "事業工具歸檔", "prompt": None},
    45: {"label": "人物故事歸檔", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 潛在家人資料 人物姓名"},
    46: {"label": "產品故事歸檔", "cmd": "產品故事歸檔", "prompt": None},
    47: {"label": "421故事歸檔", "cmd": "421故事歸檔", "prompt": None},
    48: {"label": "課程文宣歸檔", "cmd": "課程文宣歸檔", "prompt": None},
    49: {"label": "查詢課程會議", "cmd": "查詢課程會議", "prompt": None},
    50: {"label": "新增課程會議", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 新增課程會議 YYYY-MM-DD HH:MM 標題|地點|說明"},
    51: {"label": "從行事曆加入課程", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 從行事曆加入課程 [關鍵字]"},
    52: {"label": "刪除課程會議", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 刪除課程會議 COURSE-XXXX"},
    53: {"label": "查詢課程文宣", "cmd": "查詢課程文宣", "prompt": None},
    54: {"label": "新增課程文宣", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 新增課程文宣 標題|內文"},
    55: {"label": "優化課程文宣（AI）", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 優化課程文宣 PROMO-XXXX"},
    56: {"label": "邀約文宣－潛在家人（AI）", "cmd": "邀約文宣 潛在家人", "prompt": None},
    57: {"label": "邀約文宣－跟進夥伴（AI）", "cmd": "邀約文宣 跟進夥伴", "prompt": None},
    58: {"label": "查詢已產生的邀約文宣", "cmd": "查詢已產生的今日之後會議邀約文宣", "prompt": None},
    59: {"label": "修改已產生的邀約文宣", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 修改已產生的今日之後會議邀約文宣 COURSE-XXXX | 姓名 | 新內容"},
    60: {"label": "寄送每日報告", "cmd": "寄送每日報告", "prompt": None},
    61: {"label": "查詢營養素標準", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 查詢營養素標準 男 30\n（可加餐別：早餐/午餐/晚餐）"},
    62: {"label": "營養素運作原理", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 營養素運作原理 鈣"},
    63: {"label": "列出所有營養素", "cmd": "列出營養素", "prompt": None},
    64: {"label": "更新官方營養素標準", "cmd": "下載營養素標準", "prompt": None},
    65: {"label": "開始飲食評估", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 開始飲食評估 男 30"},
    66: {"label": "執行飲食評估（AI分析＋寄報告）", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 評估飲食 喝水量1500ml"},
    67: {"label": "設定下一張餐別", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 設定餐別 早餐"},
    68: {"label": "飲食評估狀態", "cmd": "飲食評估狀態", "prompt": None},
    69: {"label": "清除飲食評估", "cmd": "清除飲食評估", "prompt": None},
    70: {"label": "設定歸檔對象", "cmd": None, "prompt": "請複製後修改再送出：\n小幫手 設定評估對象 王小明"},
}


EXEC_MENU_TEXT = """\
📚 Yisheng 執行選單

👥 市場開發
  1. 新增潛在家人
  2. 查詢潛在家人近況
  3. 潛在家人總表 ▶
  4. 加入潛在家人資訊
  5. 潛在家人體驗紀錄
  6. 潛在家人濾心提醒
 71. 修改潛在家人資訊

📚 培訓系統
  7. 查詢培訓進度

🤝 夥伴陪伴
  8. 跟進報告 ▶
  9. 激勵夥伴
 10. 里程碑記錄
 11. 查詢所有夥伴 ▶
  12. 查詢待跟進夥伴 ▶
  13. 新增夥伴
  72. 新增跟進夥伴
  14. 更新夥伴
  15. 查詢指定夥伴
  16. 跟進夥伴
  73. 語音新增跟進夥伴 ▶
  17. 刪除夥伴

🗓️ 行事曆
 18. 查詢今日行事曆 ▶
 19. 查詢過往行事曆 ▶
 20. 查詢全部行事曆 ▶
 21. 上傳行事曆圖片 ▶
 22. 手動新增行事曆
 23. 修改行事曆
 24. 刪除行事曆

📂 歸類模式
 25. 查詢目前歸類模式 ▶
 26. 設定歸類模式
 27. 設定人員＋歸類模式
 28. 關閉歸類模式 ▶
 29. 查詢所有歸檔 ▶
 30. 查詢指定人員歸檔

📝 培訓記錄
 31. 整理今日培訓記錄 ▶
 32. 整理指定日期記錄
 33. 再次整理（強制覆蓋） ▶
 34. 查詢培訓記錄
 35. 顯示所有指令 ▶

🛍️ 產品歸檔（設定模式）
 36. 營養保健 (Nutrilite) ▶
 37. 美容保養 (Artistry) ▶
 38. 居家清潔 (Home) ▶
 39. 個人護理 (Glister) ▶
 40. 廚具與生活用品 ▶
 41. 空氣與水處理設備 ▶
 42. 體重管理與運動營養 ▶
 43. 香氛與個人風格 ▶
 44. 事業工具與教育系統 ▶

📖 故事分類
 45. 人物故事歸檔
 46. 產品故事歸檔 ▶
 47. 421故事歸檔 ▶
 48. 課程文宣歸檔 ▶

🎓 課程會議邀約
 49. 查詢課程會議 ▶
 50. 新增課程會議
 51. 從行事曆加入課程
 52. 刪除課程會議
 53. 查詢課程文宣 ▶
 54. 新增課程文宣
 55. 優化課程文宣（AI）
 56. 邀約文宣－潛在家人（AI）
 57. 邀約文宣－跟進夥伴（AI）
 58. 查詢已產生的邀約文宣 ▶
 59. 修改已產生的邀約文宣

📧 每日報告
 60. 寄送每日報告 ▶

🥗 營養評估（衛福部第八版 DRI）
 61. 查詢營養素標準
 62. 營養素運作原理
 63. 列出所有營養素 ▶
 64. 更新官方營養素標準 ▶
 65. 開始飲食評估
 66. 執行飲食評估（AI分析＋寄報告）
 67. 設定下一張餐別
 68. 飲食評估狀態 ▶
 69. 清除飲食評估 ▶
 70. 設定歸檔對象

══════════════════
▶ 直接執行　其餘顯示輸入範本
回覆數字即可　NA = 取消返回"""

EXEC_MENU_ITEMS[74] = {"label": "查詢AI提示詞", "cmd": "查詢AI提示詞", "prompt": None}
EXEC_MENU_ITEMS[75] = {"label": "修改AI提示詞", "cmd": None, "prompt": "請輸入：更新AI提示詞 key | 新內容"}

EXEC_MENU_TEXT += "\n\n🤖 AI 提示詞管理\n 74. 查詢AI提示詞 ▶\n 75. 修改AI提示詞"

HELP_TEXT += "\n\n🤖 AI 提示詞管理\n  查詢AI提示詞\n  查詢AI提示詞 key\n  更新AI提示詞 key | 新內容\n"

EXEC_MENU_ITEMS[76] = {"label": "跟進建議－潛在家人", "cmd": None, "prompt": "請輸入：跟進建議 潛在家人\n\n系統會先列出清單，再用姓名產生建議。"}
EXEC_MENU_ITEMS[77] = {"label": "跟進建議－夥伴", "cmd": None, "prompt": "請輸入：跟進建議 夥伴\n\n系統會先列出清單，再用姓名產生建議。"}
EXEC_MENU_ITEMS[78] = {"label": "查詢夥伴狀態定義", "cmd": "查詢夥伴狀態定義", "prompt": None}

EXEC_MENU_TEXT += "\n\n🧭 跟進建議\n 76. 跟進建議－潛在家人\n 77. 跟進建議－夥伴"
EXEC_MENU_TEXT += "\n\n📚 夥伴狀態\n 78. 查詢夥伴狀態定義"

HELP_TEXT += "\n\n🧭 跟進建議\n  跟進建議 潛在家人\n  跟進建議 潛在家人 姓名\n  跟進建議 夥伴\n  跟進建議 夥伴 姓名\n"
HELP_TEXT += "\n📚 夥伴狀態\n  查詢夥伴狀態定義\n  夥伴狀態說明\n"

EXEC_MENU_ITEMS[81] = {"label": "新增培訓模組", "cmd": None, "prompt": "請輸入：新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要"}
EXEC_MENU_ITEMS[82] = {"label": "查詢培訓模組", "cmd": "查詢培訓模組", "prompt": None}
EXEC_MENU_ITEMS[83] = {"label": "新增培訓課程", "cmd": None, "prompt": "請輸入：新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象"}
EXEC_MENU_ITEMS[84] = {"label": "查詢培訓課程", "cmd": "查詢培訓課程", "prompt": None}
EXEC_MENU_ITEMS[85] = {"label": "新增培訓反思", "cmd": None, "prompt": "請輸入：新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標"}
EXEC_MENU_ITEMS[86] = {"label": "查詢培訓進度", "cmd": None, "prompt": "請輸入：查詢培訓進度 姓名"}
EXEC_MENU_ITEMS[87] = {"label": "查詢培訓總表", "cmd": "查詢培訓總表", "prompt": None}

EXEC_MENU_TEXT += "\n\n🎓 培訓系統 2.0\n 81. 新增培訓模組\n 82. 查詢培訓模組 ▶\n 83. 新增培訓課程\n 84. 查詢培訓課程 ▶\n 85. 新增培訓反思\n 86. 查詢培訓進度 ▶\n 87. 查詢培訓總表 ▶"

HELP_TEXT += "\n\n🎓 培訓系統 2.0\n  新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要\n  查詢培訓模組 [模組名稱]\n  新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象\n  查詢培訓課程 [日期或模組名稱]\n  新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標\n  查詢培訓進度 姓名\n  查詢培訓總表\n"

# Training system clean overrides
EXEC_MENU_ITEMS[81] = {"label": "新增培訓模組", "cmd": None, "prompt": "請輸入：新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要"}
EXEC_MENU_ITEMS[82] = {"label": "查詢培訓模組", "cmd": "查詢培訓模組", "prompt": None}
EXEC_MENU_ITEMS[83] = {"label": "新增培訓課程", "cmd": None, "prompt": "請輸入：新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象"}
EXEC_MENU_ITEMS[84] = {"label": "查詢培訓課程", "cmd": "查詢培訓課程", "prompt": None}
EXEC_MENU_ITEMS[85] = {"label": "新增培訓反思", "cmd": None, "prompt": "請輸入：新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標"}
EXEC_MENU_ITEMS[86] = {"label": "查詢培訓進度", "cmd": None, "prompt": "請輸入：查詢培訓進度 姓名"}
EXEC_MENU_ITEMS[87] = {"label": "查詢培訓總表", "cmd": "查詢培訓總表", "prompt": None}
EXEC_MENU_ITEMS[88] = {"label": "啟動七天法則", "cmd": None, "prompt": "請輸入：啟動七天法則 姓名 | 開始日期 | 教練備註"}
EXEC_MENU_ITEMS[89] = {"label": "七天法則回報", "cmd": None, "prompt": "請輸入：七天法則回報 姓名 | 第幾天 | 任務內容 | 已完成/未完成 | 備註"}
EXEC_MENU_ITEMS[90] = {"label": "查詢七天法則", "cmd": None, "prompt": "請輸入：查詢七天法則 姓名"}
EXEC_MENU_ITEMS[91] = {"label": "新增課後行動", "cmd": None, "prompt": "請輸入：新增課後行動 姓名 | 課程名稱 | 行動內容 | 截止日期"}
EXEC_MENU_ITEMS[92] = {"label": "回報課後行動", "cmd": None, "prompt": "請輸入：回報課後行動 姓名 | ACTION-ID | 狀態 | 備註"}
EXEC_MENU_ITEMS[93] = {"label": "查詢課後行動", "cmd": None, "prompt": "請輸入：查詢課後行動 姓名"}
EXEC_MENU_TEXT += "\n\n🎓 培訓系統 2.0（新版）\n 81. 新增培訓模組\n 82. 查詢培訓模組 ▶\n 83. 新增培訓課程\n 84. 查詢培訓課程 ▶\n 85. 新增培訓反思\n 86. 查詢培訓進度 ▶\n 87. 查詢培訓總表 ▶\n 88. 啟動七天法則\n 89. 七天法則回報\n 90. 查詢七天法則 ▶\n 91. 新增課後行動\n 92. 回報課後行動\n 93. 查詢課後行動 ▶"
HELP_TEXT += "\n\n🎓 培訓系統 2.0（新版）\n  新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要\n  查詢培訓模組 [模組名稱]\n  新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象\n  查詢培訓課程 [日期或模組名稱]\n  新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標\n  查詢培訓進度 姓名\n  查詢培訓總表\n  啟動七天法則 姓名 | 開始日期 | 教練備註\n  七天法則回報 姓名 | 第幾天 | 任務內容 | 已完成/未完成 | 備註\n  查詢七天法則 姓名\n  新增課後行動 姓名 | 課程名稱 | 行動內容 | 截止日期\n  回報課後行動 姓名 | ACTION-ID | 狀態 | 備註\n  查詢課後行動 姓名\n"

# Training system clean overrides
EXEC_MENU_ITEMS[81] = {"label": "新增培訓模組", "cmd": None, "prompt": "請輸入：新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要"}
EXEC_MENU_ITEMS[82] = {"label": "查詢培訓模組", "cmd": "查詢培訓模組", "prompt": None}
EXEC_MENU_ITEMS[83] = {"label": "新增培訓課程", "cmd": None, "prompt": "請輸入：新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象"}
EXEC_MENU_ITEMS[84] = {"label": "查詢培訓課程", "cmd": "查詢培訓課程", "prompt": None}
EXEC_MENU_ITEMS[85] = {"label": "新增培訓反思", "cmd": None, "prompt": "請輸入：新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標"}
EXEC_MENU_ITEMS[86] = {"label": "查詢培訓進度", "cmd": None, "prompt": "請輸入：查詢培訓進度 姓名"}
EXEC_MENU_ITEMS[87] = {"label": "查詢培訓總表", "cmd": "查詢培訓總表", "prompt": None}
EXEC_MENU_ITEMS[88] = {"label": "啟動七天法則", "cmd": None, "prompt": "請輸入：啟動七天法則 姓名 | 開始日期 | 教練備註"}
EXEC_MENU_ITEMS[89] = {"label": "七天法則回報", "cmd": None, "prompt": "請輸入：七天法則回報 姓名 | 第幾天 | 任務內容 | 已完成/未完成 | 備註"}
EXEC_MENU_ITEMS[90] = {"label": "查詢七天法則", "cmd": None, "prompt": "請輸入：查詢七天法則 姓名"}
EXEC_MENU_ITEMS[91] = {"label": "新增課後行動", "cmd": None, "prompt": "請輸入：新增課後行動 姓名 | 課程名稱 | 行動內容 | 截止日期"}
EXEC_MENU_ITEMS[92] = {"label": "回報課後行動", "cmd": None, "prompt": "請輸入：回報課後行動 姓名 | ACTION-ID | 狀態 | 備註"}
EXEC_MENU_ITEMS[93] = {"label": "查詢課後行動", "cmd": None, "prompt": "請輸入：查詢課後行動 姓名"}
EXEC_MENU_TEXT += "\n\n🎓 培訓系統 2.0（新版）\n 81. 新增培訓模組\n 82. 查詢培訓模組 ▶\n 83. 新增培訓課程\n 84. 查詢培訓課程 ▶\n 85. 新增培訓反思\n 86. 查詢培訓進度 ▶\n 87. 查詢培訓總表 ▶\n 88. 啟動七天法則\n 89. 七天法則回報\n 90. 查詢七天法則 ▶\n 91. 新增課後行動\n 92. 回報課後行動\n 93. 查詢課後行動 ▶"
HELP_TEXT += "\n\n🎓 培訓系統 2.0（新版）\n  新增培訓模組 模組名稱 | 模組類型 | 學習目標 | 核心摘要\n  查詢培訓模組 [模組名稱]\n  新增培訓課程 課程名稱 | 模組名稱 | 日期 | 時間 | 地點 | 講師 | 對象\n  查詢培訓課程 [日期或模組名稱]\n  新增培訓反思 姓名 | 課程名稱 | 悟到 | 學到 | 做到 | 目標\n  查詢培訓進度 姓名\n  查詢培訓總表\n  啟動七天法則 姓名 | 開始日期 | 教練備註\n  七天法則回報 姓名 | 第幾天 | 任務內容 | 已完成/未完成 | 備註\n  查詢七天法則 姓名\n  新增課後行動 姓名 | 課程名稱 | 行動內容 | 截止日期\n  回報課後行動 姓名 | ACTION-ID | 狀態 | 備註\n  查詢課後行動 姓名\n"


# Clean training system overrides appended last so line menu/help stay readable.
EXEC_MENU_ITEMS[81] = {"label": "??????", "cmd": None, "prompt": "?????????? ???? | ???? | ???? | ??"}
EXEC_MENU_ITEMS[82] = {"label": "??????", "cmd": "??????", "prompt": None}
EXEC_MENU_ITEMS[83] = {"label": "??????", "cmd": None, "prompt": "?????????? ???? | ???? | ?? | ?? | ?? | ?? | ??"}
EXEC_MENU_ITEMS[84] = {"label": "??????", "cmd": "??????", "prompt": None}
EXEC_MENU_ITEMS[85] = {"label": "??????", "cmd": None, "prompt": "?????????? ?? | ???? | ?? | ?? | ?? | ??"}
EXEC_MENU_ITEMS[86] = {"label": "??????", "cmd": None, "prompt": "?????????? ??"}
EXEC_MENU_ITEMS[87] = {"label": "??????", "cmd": "??????", "prompt": None}
EXEC_MENU_ITEMS[88] = {"label": "??????", "cmd": None, "prompt": "?????????? ?? | ???? | ????"}
EXEC_MENU_ITEMS[89] = {"label": "??????", "cmd": None, "prompt": "?????????? ?? | ??? | ???? | ???/??? | ??"}
EXEC_MENU_ITEMS[90] = {"label": "??????", "cmd": None, "prompt": "?????????? ??"}
EXEC_MENU_ITEMS[91] = {"label": "??????", "cmd": None, "prompt": "?????????? ?? | ???? | ???? | ????"}
EXEC_MENU_ITEMS[92] = {"label": "??????", "cmd": None, "prompt": "?????????? ?? | ACTION-ID | ?? | ??"}
EXEC_MENU_ITEMS[93] = {"label": "??????", "cmd": None, "prompt": "?????????? ??"}
EXEC_MENU_TEXT += "\n\n?? ???? 2.0?????\n 81. ??????\n 82. ?????? ?\n 83. ??????\n 84. ?????? ?\n 85. ??????\n 86. ?????? ?\n 87. ?????? ?\n 88. ??????\n 89. ??????\n 90. ?????? ?\n 91. ??????\n 92. ??????\n 93. ?????? ?"
HELP_TEXT += "\n\n?? ???? 2.0?????\n  ?????? ???? | ???? | ???? | ??\n  ?????? [????]\n  ?????? ???? | ???? | ?? | ?? | ?? | ?? | ??\n  ?????? [????]\n  ?????? ?? | ???? | ?? | ?? | ?? | ??\n  ?????? ??\n  ??????\n  ?????? ?? | ???? | ????\n  ?????? ?? | ??? | ???? | ???/??? | ??\n  ?????? ??\n  ?????? ?? | ???? | ???? | ????\n  ?????? ?? | ACTION-ID | ?? | ??\n  ?????? ??\n"


# Unicode-safe training system overrides.
EXEC_MENU_ITEMS[81] = {"label": "\u65b0\u589e\u57f9\u8a13\u6a21\u7d44", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u65b0\u589e\u57f9\u8a13\u6a21\u7d44 \u6a21\u7d44\u540d\u7a31 | \u6a21\u7d44\u985e\u578b | \u5b78\u7fd2\u76ee\u6a19 | \u6458\u8981"}
EXEC_MENU_ITEMS[82] = {"label": "\u67e5\u8a62\u57f9\u8a13\u6a21\u7d44", "cmd": "\u67e5\u8a62\u57f9\u8a13\u6a21\u7d44", "prompt": None}
EXEC_MENU_ITEMS[83] = {"label": "\u65b0\u589e\u57f9\u8a13\u8ab2\u7a0b", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u65b0\u589e\u57f9\u8a13\u8ab2\u7a0b \u8ab2\u7a0b\u540d\u7a31 | \u6a21\u7d44\u540d\u7a31 | \u65e5\u671f | \u6642\u9593 | \u5730\u9ede | \u8b1b\u5e2b | \u5c0d\u8c61"}
EXEC_MENU_ITEMS[84] = {"label": "\u67e5\u8a62\u57f9\u8a13\u8ab2\u7a0b", "cmd": "\u67e5\u8a62\u57f9\u8a13\u8ab2\u7a0b", "prompt": None}
EXEC_MENU_ITEMS[85] = {"label": "\u65b0\u589e\u57f9\u8a13\u53cd\u601d", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u65b0\u589e\u57f9\u8a13\u53cd\u601d \u59d3\u540d | \u8ab2\u7a0b\u540d\u7a31 | \u609f\u5230 | \u5b78\u5230 | \u505a\u5230 | \u76ee\u6a19"}
EXEC_MENU_ITEMS[86] = {"label": "\u67e5\u8a62\u57f9\u8a13\u9032\u5ea6", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u67e5\u8a62\u57f9\u8a13\u9032\u5ea6 \u59d3\u540d"}
EXEC_MENU_ITEMS[87] = {"label": "\u67e5\u8a62\u57f9\u8a13\u7e3d\u8868", "cmd": "\u67e5\u8a62\u57f9\u8a13\u7e3d\u8868", "prompt": None}
EXEC_MENU_ITEMS[88] = {"label": "\u555f\u52d5\u4e03\u5929\u6cd5\u5247", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u555f\u52d5\u4e03\u5929\u6cd5\u5247 \u59d3\u540d | \u958b\u59cb\u65e5\u671f | \u6559\u7df4\u5099\u8a3b"}
EXEC_MENU_ITEMS[89] = {"label": "\u4e03\u5929\u6cd5\u5247\u56de\u5831", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u4e03\u5929\u6cd5\u5247\u56de\u5831 \u59d3\u540d | \u7b2c\u5e7e\u5929 | \u4efb\u52d9\u5167\u5bb9 | \u5df2\u5b8c\u6210/\u672a\u5b8c\u6210 | \u5099\u8a3b"}
EXEC_MENU_ITEMS[90] = {"label": "\u67e5\u8a62\u4e03\u5929\u6cd5\u5247", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u67e5\u8a62\u4e03\u5929\u6cd5\u5247 \u59d3\u540d"}
EXEC_MENU_ITEMS[91] = {"label": "\u65b0\u589e\u8ab2\u5f8c\u884c\u52d5", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u65b0\u589e\u8ab2\u5f8c\u884c\u52d5 \u59d3\u540d | \u8ab2\u7a0b\u540d\u7a31 | \u884c\u52d5\u5167\u5bb9 | \u622a\u6b62\u65e5\u671f"}
EXEC_MENU_ITEMS[92] = {"label": "\u56de\u5831\u8ab2\u5f8c\u884c\u52d5", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u56de\u5831\u8ab2\u5f8c\u884c\u52d5 \u59d3\u540d | ACTION-ID | \u72c0\u614b | \u5099\u8a3b"}
EXEC_MENU_ITEMS[93] = {"label": "\u67e5\u8a62\u8ab2\u5f8c\u884c\u52d5", "cmd": None, "prompt": "\u8acb\u8f38\u5165\uff1a\u67e5\u8a62\u8ab2\u5f8c\u884c\u52d5 \u59d3\u540d"}
