"""
Orchestrator Agent
File: C:/Users/user/claude AI_Agent/agents/10_orchestrator.py
Function: 總調度 — 協調市場開發、培訓、夥伴跟進、夥伴激勵四大 Agent
Schedule:
  - 09:00 每日 (morning): 市場開發 + 培訓推播 + 激勵排程
  - 17:00 每日 (evening): 夥伴跟進報告
Usage:
  python 10_orchestrator.py --mode morning|evening|market|training|followup|motivation
"""

import argparse
import importlib.util
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

try:
    from common_runtime import BASE_DIR
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR

LOG_FILE = BASE_DIR / "logs" / "orchestrator_log.txt"

load_dotenv(dotenv_path=BASE_DIR / ".env")


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [ORCHESTRATOR] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        name, str(BASE_DIR / "agents" / filename)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"無法載入模組：{filename}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ============================================================
# 執行模式
# ============================================================

def run_morning():
    """09:00 早班：市場開發 + 培訓推播 + 激勵排程"""
    log("=" * 50)
    log("早班任務開始 (morning mode)")

    for label, filename, method in [
        ("市場開發", "11_market_dev_agent.py", "MarketDevAgent"),
        ("培訓推播", "12_training_agent.py",   "TrainingAgent"),
        ("激勵排程", "14_motivation_agent.py",  "MotivationAgent"),
    ]:
        try:
            log(f"▶ 啟動 {label}...")
            mod = _load(label, filename)
            agent = getattr(mod, method)()
            if label == "激勵排程":
                agent.run_scheduled()
            else:
                agent.run()
            log(f"✓ {label} 完成")
        except Exception as e:
            log(f"✗ {label} 失敗：{e}")

    log("早班任務完成")
    log("=" * 50)


def run_evening():
    """17:00 晚班：夥伴跟進報告"""
    log("=" * 50)
    log("晚班任務開始 (evening mode)")

    try:
        log("▶ 啟動 夥伴跟進...")
        mod = _load("跟進", "13_followup_agent.py")
        mod.FollowupAgent().run()
        log("✓ 夥伴跟進 完成")
    except Exception as e:
        log(f"✗ 夥伴跟進 失敗：{e}")

    log("晚班任務完成")
    log("=" * 50)


def run_single(mode: str):
    mapping = {
        "market":     ("市場開發", "11_market_dev_agent.py", "MarketDevAgent",  "run"),
        "training":   ("培訓推播", "12_training_agent.py",   "TrainingAgent",   "run"),
        "followup":   ("夥伴跟進", "13_followup_agent.py",   "FollowupAgent",   "run"),
        "motivation": ("激勵排程", "14_motivation_agent.py",  "MotivationAgent", "run_scheduled"),
    }
    label, filename, cls, method = mapping[mode]
    log(f"▶ 單獨執行 {label}...")
    mod = _load(label, filename)
    getattr(getattr(mod, cls)(), method)()
    log(f"✓ {label} 完成")


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrator Agent")
    parser.add_argument(
        "--mode",
        choices=["morning", "evening", "market", "training", "followup", "motivation"],
        default="morning",
        help="執行模式"
    )
    args = parser.parse_args()

    log(f"執行模式：{args.mode}")

    if args.mode == "morning":
        run_morning()
    elif args.mode == "evening":
        run_evening()
    else:
        run_single(args.mode)
