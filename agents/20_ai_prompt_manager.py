import json
from pathlib import Path


BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
PROMPT_FILE = BASE_DIR / "config" / "ai_prompts.json"


DEFAULT_PROMPTS = {
    "course_promo_optimize": {
        "label": "優化課程文宣",
        "description": "用來優化既有課程文宣內容的提示詞。",
        "template": (
            "你是專業的中文活動文宣編輯。請用繁體中文優化以下課程文宣。\n\n"
            "近期會議資訊：\n{mtg_summary}\n\n"
            "文宣標題：{promo_title}\n"
            "原始文宣：\n{promo_content}\n\n"
            "請輸出一版更適合 LINE / 社群分享的文案，要求：\n"
            "- 開頭更吸引人，但不要誇大\n"
            "- 保留原始重點與課程價值\n"
            "- 文字自然、口語、好轉貼\n"
            "- 可以使用少量 emoji，但不要太多\n"
            "- 長度控制在 250 字內\n"
            "- 只輸出優化後文案，不要額外解釋"
        ),
    },
    "course_invite_prospect_general": {
        "label": "潛在家人通用邀約文宣",
        "description": "針對潛在家人產生一般邀約文宣的提示詞。",
        "template": (
            "你是專業的繁體中文邀約文案助手，請根據以下內容，"
            "幫我寫一段適合傳給潛在家人的邀約訊息。\n\n"
            "近期培訓摘要：\n{mtg_summary}\n\n"
            "可用課程文宣內容：\n{promo_section}\n\n"
            "對象描述：{target_desc}\n"
            "對象資訊：\n{person_block}\n\n"
            "要求：\n"
            "- 用自然真誠語氣\n"
            "- 讓對方感受到被理解，而不是被推銷\n"
            "- 可提到生活改善、機會、學習，但不要過度承諾\n"
            "- 長度控制在 200 字內\n"
            "- 只輸出邀約文案"
        ),
    },
    "course_invite_partner_general": {
        "label": "跟進夥伴通用邀約文宣",
        "description": "針對既有夥伴產生一般邀約文宣的提示詞。",
        "template": (
            "你是專業的繁體中文夥伴邀約助手，請根據以下內容，"
            "幫我寫一段適合傳給跟進夥伴的邀約訊息。\n\n"
            "近期培訓摘要：\n{mtg_summary}\n\n"
            "對象描述：{target_desc}\n"
            "對象資訊：\n{person_block}\n\n"
            "要求：\n"
            "- 語氣溫暖、鼓勵、帶支持感\n"
            "- 可強調學習、陪伴、一起前進\n"
            "- 不要寫成官式通知\n"
            "- 長度控制在 200 字內\n"
            "- 只輸出邀約文案"
        ),
    },
    "course_invite_prospect_meeting": {
        "label": "潛在家人指定會議邀約",
        "description": "針對潛在家人與指定會議產生邀約文宣。",
        "template": (
            "你是專業的繁體中文邀約文案助手，請為 {name} 撰寫一段邀約文宣。\n\n"
            "會議資訊：\n"
            "- 標題：{meeting_title}\n"
            "- 時間：{when}\n"
            "- 地點：{loc}\n"
            "- 說明：{desc}\n"
            "- 講師：{speaker}\n"
            "- 講師介紹：{speaker_bio}\n"
            "- 主題：{topics}\n"
            "- 主題補充：{topic_desc}\n\n"
            "可用課程文宣內容：\n{promo_section}\n\n"
            "對象資訊：\n{person_block}\n\n"
            "要求：\n"
            "- 讓對方願意了解這場活動\n"
            "- 文字簡潔、有溫度、不要過度銷售\n"
            "- 有明確時間與行動邀請\n"
            "- 長度控制在 200 字內\n"
            "- 只輸出邀約文案"
        ),
    },
    "course_invite_partner_meeting": {
        "label": "跟進夥伴指定會議邀約",
        "description": "針對跟進夥伴與指定會議產生邀約文宣。",
        "template": (
            "你是專業的繁體中文夥伴邀約助手，請為 {name} 撰寫一段邀約文宣。\n\n"
            "會議資訊：\n"
            "- 標題：{meeting_title}\n"
            "- 時間：{when}\n"
            "- 地點：{loc}\n"
            "- 說明：{desc}\n"
            "- 講師：{speaker}\n"
            "- 講師介紹：{speaker_bio}\n"
            "- 主題：{topics}\n"
            "- 主題補充：{topic_desc}\n\n"
            "對象資訊：\n{person_block}\n\n"
            "要求：\n"
            "- 帶鼓勵、陪伴、一起成長的感覺\n"
            "- 不要寫得太生硬或像公告\n"
            "- 有明確邀約行動\n"
            "- 長度控制在 200 字內\n"
            "- 只輸出邀約文案"
        ),
    },
    "nutrition_meal_image_analysis": {
        "label": "餐點照片 AI 分析",
        "description": "分析單張餐點照片內容的提示詞。",
        "template": (
            "You are analyzing a meal photo for {meal_label}. "
            "Answer in Traditional Chinese.\n"
            "Please provide:\n"
            "1. Visible foods and drinks.\n"
            "2. Estimated macros: protein (g), carbs (g), fat (g), calories (kcal).\n"
            "3. Micronutrients likely to be sufficient in this meal.\n"
            "4. Micronutrients likely to be lacking in this meal.\n"
            "5. A short note about overall balance and obvious risks.\n"
            "Be practical and mention when something only an estimate."
        ),
    },
    "nutrition_daily_assessment": {
        "label": "飲食評估整體報告",
        "description": "彙整三餐分析與 DRI 後產生整體報告的提示詞。",
        "template": (
            "Create a nutrition assessment report in Traditional Chinese for a {gender_label}, age {age}. "
            "The matched Taiwan DRI age group is {dri_group}.\n\n"
            "Meal analysis notes:\n{meals_text}\n"
            "Water intake today: {water_ml} ml. Target water intake: {water_target} ml.\n\n"
            "Taiwan DRI reference values for this person:\n{dri_summary}\n\n"
            "Write a detailed report in Traditional Chinese using Markdown with these sections:\n"
            "1. **整體飲食評估**: 1-2 short paragraphs about overall balance.\n"
            "2. **可能缺乏的營養素**: bullet list, and for each nutrient explain severity, likely reason, and long-term risk.\n"
            "3. **可能足夠的營養素**: bullet list, if any.\n"
            "4. **水分與飲食習慣觀察**.\n"
            "5. **長期這樣飲食可能出現的身體警訊**: specific symptoms in short-term, mid-term, long-term order.\n"
            "6. **改善建議**: 3-5 actionable suggestions.\n"
            "Be practical and state uncertainty when necessary."
        ),
    },
    "followup_individual_report": {
        "label": "個人夥伴跟進報告",
        "description": "針對單一夥伴產出深度跟進策略與訊息草稿。",
        "template": (
            "你是一位擁有 20 年經驗、專精於「陪伴與成長」的事業導師。請針對以下夥伴的現況數據，產出一份「深度跟進建議報告」。\n\n"
            "### 夥伴原始數據\n"
            "- 姓名：{target_name}\n"
            "- 最後聯絡：{last_contact} ({days} 天前)\n"
            "- 本週動作數：{weekly_actions} 次\n"
            "- 目前里程碑：{milestone}\n"
            "- 備註資訊：{note}\n\n"
            "### 要求\n"
            "1. 狀態診斷：分析該夥伴目前的心理與執行狀態（如：動力下降、遭遇挫折、或穩定成長中）。\n"
            "2. 核心切入點：建議導師這次應該以什麼「主題」或「心情」去聯繫他最有效。\n"
            "3. 具體跟進建議：給出 2-3 點具體行動。\n"
            "4. LINE 訊息草稿：產出一段約 80-120 字、溫暖、老朋友口吻的草稿。\n\n"
            "請以繁體中文回傳完整報告，直接顯示內容，不需開場白。"
        )
    }
}


class AIPromptManager:
    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not PROMPT_FILE.exists():
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_PROMPTS, f, ensure_ascii=False, indent=2)

    def load_prompts(self) -> dict:
        self._ensure_file()
        with open(PROMPT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        merged = {}
        for key, default in DEFAULT_PROMPTS.items():
            item = dict(default)
            item.update(data.get(key, {}))
            merged[key] = item
        for key, item in data.items():
            if key not in merged:
                merged[key] = item
        return merged

    def save_prompts(self, data: dict):
        self._ensure_file()
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_prompt_labels(self) -> list[dict]:
        data = self.load_prompts()
        return [
            {"key": key, "label": item.get("label", key), "description": item.get("description", "")}
            for key, item in data.items()
        ]

    def get_prompt(self, key: str) -> dict | None:
        return self.load_prompts().get(key)

    def render_prompt(self, key: str, **kwargs) -> str:
        item = self.get_prompt(key)
        if not item:
            raise KeyError(key)
        return item["template"].format(**kwargs)

    def update_prompt(self, key: str, content: str) -> str:
        data = self.load_prompts()
        if key not in data:
            return f"找不到提示詞 key：{key}"
        data[key]["template"] = content.strip()
        self.save_prompts(data)
        return f"已更新 AI 提示詞：{key}"

    def format_prompt_list(self) -> str:
        rows = self.list_prompt_labels()
        lines = ["AI 提示詞清單："]
        for item in rows:
            lines.append(f"- {item['key']}｜{item['label']}")
        return "\n".join(lines)

    def format_prompt_detail(self, key: str) -> str:
        item = self.get_prompt(key)
        if not item:
            return f"找不到提示詞 key：{key}"
        return (
            f"AI 提示詞：{key}\n"
            f"名稱：{item.get('label', '')}\n"
            f"說明：{item.get('description', '')}\n\n"
            f"{item.get('template', '')}"
        )

    def handle_command(self, command: str) -> str:
        msg = (command or "").strip()
        if msg == "查詢AI提示詞":
            return self.format_prompt_list()
        if msg.startswith("查詢AI提示詞 "):
            return self.format_prompt_detail(msg.replace("查詢AI提示詞", "", 1).strip())
        if msg.startswith("更新AI提示詞 "):
            raw = msg.replace("更新AI提示詞", "", 1).strip()
            parts = [p.strip() for p in raw.split("|", 1)]
            if len(parts) < 2 or not parts[0] or not parts[1]:
                return "格式：更新AI提示詞 key | 內容"
            return self.update_prompt(parts[0], parts[1])
        return ""


def load_prompts(): return AIPromptManager().load_prompts()
def list_prompt_labels(): return AIPromptManager().list_prompt_labels()
def get_prompt(key): return AIPromptManager().get_prompt(key)
def render_prompt(key, **kwargs): return AIPromptManager().render_prompt(key, **kwargs)
def update_prompt(key, content): return AIPromptManager().update_prompt(key, content)
def format_prompt_list(): return AIPromptManager().format_prompt_list()
def format_prompt_detail(key): return AIPromptManager().format_prompt_detail(key)
def handle_command(command): return AIPromptManager().handle_command(command)
