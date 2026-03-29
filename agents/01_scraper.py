"""
Agent 1: Scraper Agent
File: C:/Users/user/claude AI_Agent/agents/01_scraper.py
Output: C:/Users/user/claude AI_Agent/output/prospects_raw/YYYYMMDD_HHMM.json
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

# ============================================================
# ⚙️ 設定（讀取 settings.json）
# ============================================================

BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
OUTPUT_DIR = BASE_DIR / "output" / "prospects_raw"
LOG_FILE   = BASE_DIR / "logs" / "agent_log.txt"
CONFIG     = BASE_DIR / "config" / "settings.json"

def load_config() -> dict:
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "daily_limit": 100,
            "keywords": ["副業推薦","兼職機會","在家工作","斜槓收入","媽媽副業"],
        }

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [SCRAPER] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        safe_line = line.encode("cp950", errors="replace").decode("cp950")
        print(safe_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 📡 Tavily Search（主要搜尋引擎）
# ============================================================

class TavilySearcher:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "")
        self.url = "https://api.tavily.com/search"

    def search(self, keyword: str, limit: int = 10) -> list:
        if not self.api_key:
            log("⚠️ 未設定 TAVILY_API_KEY，跳過搜尋")
            return []

        payload = {
            "api_key": self.api_key,
            "query": f"{keyword} 台灣 site:dcard.tw OR site:ptt.cc",
            "search_depth": "basic",
            "max_results": limit,
        }
        try:
            r = requests.post(self.url, json=payload, timeout=15)
            items = r.json().get("results", [])
            results = []
            for item in items:
                results.append({
                    "來源": "Tavily",
                    "標題": item.get("title", ""),
                    "摘要": item.get("content", "")[:200],
                    "連結": item.get("url", ""),
                    "搜尋關鍵字": keyword,
                    "爬取時間": datetime.now().isoformat(),
                })
            log(f"  Tavily [{keyword}] → {len(results)} 筆")
            return results
        except Exception as e:
            log(f"  Tavily 錯誤：{e}")
            return []


# ============================================================
# 📡 Dcard API（免費，無需 Key）
# ============================================================

class DcardScraper:
    API = "https://www.dcard.tw/_api/posts"
    FORUMS = ["part-time", "salary", "money", "entrepreneurship"]
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.dcard.tw/"
    }

    def scrape(self, keywords: list, limit: int = 50) -> list:
        results = []
        for forum in self.FORUMS:
            try:
                r = requests.get(
                    self.API,
                    params={"forum": forum, "limit": 30},
                    headers=self.HEADERS,
                    timeout=10
                )
                if r.status_code != 200:
                    continue
                posts = r.json()
                for post in posts:
                    content = f"{post.get('title','')} {post.get('excerpt','')}".lower()
                    if any(kw in content for kw in keywords):
                        results.append({
                            "來源": "Dcard",
                            "版面": forum,
                            "標題": post.get("title", ""),
                            "摘要": post.get("excerpt", "")[:200],
                            "連結": f"https://www.dcard.tw/f/{forum}/p/{post.get('id','')}",
                            "留言數": post.get("commentCount", 0),
                            "收藏數": post.get("likeCount", 0),
                            "爬取時間": datetime.now().isoformat(),
                        })
                time.sleep(1.5)
            except Exception as e:
                log(f"  Dcard [{forum}] 錯誤：{e}")

        log(f"  Dcard → {len(results)} 筆")
        return results[:limit]


# ============================================================
# 💾 儲存為 JSON（供 C# Watcher 監看）
# ============================================================

def save_json(data: list) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = OUTPUT_DIR / f"prospects_raw_{ts}.json"

    payload = {
        "generated_at": datetime.now().isoformat(),
        "total": len(data),
        "status": "raw",          # C# Watcher 用此欄位判斷階段
        "next_step": "scoring",
        "data": data
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    log(f"✅ 已輸出 {len(data)} 筆 → {filepath}")
    return filepath


# ============================================================
# 🚀 主程式
# ============================================================

def main():
    log("=" * 50)
    log("🚀 爬蟲Agent 啟動")

    cfg = load_config()
    keywords = cfg.get("keywords", ["副業推薦"])
    limit = cfg.get("daily_limit", 100)

    all_results = []

    # 1. Dcard
    log("📡 爬取 Dcard...")
    dcard = DcardScraper()
    all_results.extend(dcard.scrape(keywords, limit=50))

    # 2. Tavily
    log("📡 Tavily 搜尋...")
    tavily = TavilySearcher()
    for kw in keywords[:5]:
        all_results.extend(tavily.search(kw, limit=10))
        time.sleep(1)

    # 去重
    seen = set()
    unique = []
    for r in all_results:
        key = r.get("連結", r.get("標題", ""))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    log(f"📊 去重後共 {len(unique)} 筆潛在客戶")
    filepath = save_json(unique[:limit])

    log(f"🏁 爬蟲完成 → {filepath}")
    log("=" * 50)
    return str(filepath)


if __name__ == "__main__":
    main()
