"""
Agent 4: 多 Agent 主控腳本（CrewAI）
檔案：C:/Users/user/claude AI_Agent/agents/04_crew_main.py
說明：統一呼叫所有 Agent，也可獨立跑 CrewAI 多 Agent 協作
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

try:
    from email_notify import notify_pipeline_done, notify_crew_done
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
LOG_FILE = BASE_DIR / "logs" / "agent_log.txt"
AGENTS_DIR = BASE_DIR / "agents"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [MAIN] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        safe_line = line.encode("cp950", errors="replace").decode("cp950")
        print(safe_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_agent(script: str) -> bool:
    path = AGENTS_DIR / script
    log(f"▶ 執行：{script}")
    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0:
        stdout_text = (result.stdout or "").strip()
        if stdout_text:
            log(f"ℹ️ {script} 輸出摘要：{stdout_text[:300]}")
        log(f"✅ 完成：{script}")
        return True

    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    details = stderr or stdout or "無錯誤輸出"
    log(f"❌ 失敗：{script}\n{details[:500]}")
    return False


# ============================================================
# 🔄 模式1：Sequential Pipeline（依序執行）
# ============================================================

def already_ran_today() -> bool:
    today = datetime.now().strftime("%Y%m%d")
    scored_dir = BASE_DIR / "output" / "prospects_scored"
    messages_dir = BASE_DIR / "output" / "messages"
    for directory in (scored_dir, messages_dir):
        if any(directory.glob(f"*{today}*.json")):
            return True
    return False


def run_pipeline():
    if already_ran_today():
        log("⏭️ 今日已執行過，略過。明天再跑。")
        return

    log("=" * 60)
    log("🚀 安麗 AI Agent 系統啟動（Pipeline 模式）")
    log(f"⏰ 時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("=" * 60)

    steps = [
        ("01_scraper.py", "爬蟲Agent  — 找潛在客戶"),
        ("02_scoring.py", "評分Agent  — AI篩選評分"),
        ("03_templates.py", "邀約Agent  — 生成個人化訊息"),
    ]

    results = []
    for script, desc in steps:
        log(f"\n📌 步驟：{desc}")
        ok = run_agent(script)
        results.append({"步驟": desc, "狀態": "成功" if ok else "失敗"})
        if not ok:
            log("⚠️ 中止後續步驟")
            break

    summary_path = BASE_DIR / "logs" / f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "執行時間": datetime.now().isoformat(),
                "執行結果": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    log(f"\n📊 執行摘要 → {summary_path}")
    log("=" * 60)
    log("🏁 全部流程完成")

    if EMAIL_AVAILABLE:
        email_results = [
            {"step": desc, "status": "success" if r["狀態"] == "成功" else "failed"}
            for r, (_, desc) in zip(results, steps[:len(results)])
        ]
        notify_pipeline_done(email_results, str(summary_path))
        log("📧 Email notification sent")


# ============================================================
# 🤖 模式2：CrewAI 多Agent協作（進階）
# ============================================================

def run_crewai():
    try:
        from crewai import Agent, Task, Crew, Process, LLM
    except ImportError:
        log("⚠️ 請先安裝：pip install crewai")
        return

    llm = LLM(model="anthropic/claude-sonnet-4-6", temperature=0.7)

    search_agent = Agent(
        role="潛在客戶搜尋專員",
        goal="每日找出100位具副業或健康需求的潛在客戶",
        backstory="你精通台灣社群生態，熟悉 PTT、Dcard、Facebook 社團的搜尋技巧",
        llm=llm,
        verbose=True,
    )
    analysis_agent = Agent(
        role="客戶資料分析師",
        goal="依評分標準篩選出高/中/低潛力客戶",
        backstory="你是數據分析專家，擅長從社群資料判斷需求與潛力",
        llm=llm,
        verbose=True,
    )
    outreach_agent = Agent(
        role="個人化邀約撰寫師",
        goal="針對每位高潛力客戶撰寫自然親切的中文邀約訊息",
        backstory="你是頂尖文案專家，訊息讓人感受真誠而非廣告",
        llm=llm,
        verbose=True,
    )
    followup_agent = Agent(
        role="跟進管理師",
        goal="管理 Day1/Day3/Day7/Day14 的跟進時程，確保零遺漏",
        backstory="你是細心的 CRM 管理專家，追蹤每位客戶狀態",
        llm=llm,
        verbose=True,
    )
    report_agent = Agent(
        role="業績報告分析師",
        goal="每週產出完整的客戶開發報告與改善建議",
        backstory="你擅長將數據轉化為清晰報告",
        llm=llm,
        verbose=True,
    )

    t1 = Task(
        description="搜尋 Dcard 副業版、PTT 兼差版、Facebook 社團，找出100位潛在客戶，輸出 JSON 清單",
        agent=search_agent,
        expected_output="100位潛在客戶的 JSON 清單（含標題、摘要、來源、連結）",
    )
    t2 = Task(
        description="接收 t1 名單，依有副業需求(30)+健康興趣(25)+社群活躍(25)+地區符合(20)評分，分高/中/低潛力",
        agent=analysis_agent,
        expected_output="分類後的評分清單",
        context=[t1],
    )
    t3 = Task(
        description="針對高潛力客戶，依話術類型(上班族副業/全職媽媽/健康意識族群/社群達人/創業斜槓族)撰寫 Day1/Day3/Day7 訊息",
        agent=outreach_agent,
        expected_output="每人三則個人化中文邀約訊息",
        context=[t2],
    )
    t4 = Task(
        description="建立所有客戶的跟進時程表（Day1/3/7/14），含狀態追蹤與下次跟進日期",
        agent=followup_agent,
        expected_output="完整跟進時程表",
        context=[t3],
    )
    t5 = Task(
        description="整合所有資料，產出繁體中文週報：接觸總數、各分類佔比、預估回覆率、下週優化建議3點以上",
        agent=report_agent,
        expected_output="完整繁體中文週報",
        context=[t1, t2, t3, t4],
    )

    crew = Crew(
        agents=[search_agent, analysis_agent, outreach_agent, followup_agent, report_agent],
        tasks=[t1, t2, t3, t4, t5],
        process=Process.sequential,
        verbose=True,
    )

    log("🚀 CrewAI 多Agent協作啟動...")
    result = crew.kickoff()
    log("✅ CrewAI 執行完成")

    output_path = BASE_DIR / "output" / f"crew_result_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"result": str(result), "generated_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    log(f"📁 結果已儲存 → {output_path}")

    if EMAIL_AVAILABLE:
        notify_crew_done(str(output_path))
        log("📧 Email notification sent")


# ============================================================
# 🚀 主程式
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="安麗 AI Agent 主控")
    parser.add_argument("--mode", choices=["pipeline", "crew"], default="pipeline", help="pipeline=依序執行 | crew=CrewAI多Agent")
    args = parser.parse_args()

    if args.mode == "crew":
        run_crewai()
    else:
        run_pipeline()
