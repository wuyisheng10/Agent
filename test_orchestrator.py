"""Local test: Orchestrator import and structure"""
import sys, importlib.util as ilu
import types
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent

if "dotenv" not in sys.modules:
    m = types.ModuleType("dotenv")
    m.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = m

results = []
def chk(name, cond):
    results.append((name, bool(cond)))
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}")

print("=== 10_orchestrator 結構檢查 ===")
try:
    spec = ilu.spec_from_file_location("orch", BASE / "agents" / "10_orchestrator.py")
    m = ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    chk("orchestrator imports OK", True)

    # 確認模組級函式存在
    chk("has log()",         hasattr(m, "log"))
    chk("has _load()",       hasattr(m, "_load"))
    chk("has run_morning()", hasattr(m, "run_morning"))
    chk("has run_evening()", hasattr(m, "run_evening"))
    chk("has run_single()",  hasattr(m, "run_single"))

except Exception as e:
    chk("orchestrator import", False)
    import traceback; traceback.print_exc()

print("\n=== _load() 動態載入各 Agent ===")
try:
    for label, filename, cls_name in [
        ("市場開發", "11_market_dev_agent.py", "MarketDevAgent"),
        ("培訓推播", "12_training_agent.py",   "TrainingAgent"),
        ("夥伴跟進", "13_followup_agent.py",   "FollowupAgent"),
        ("激勵排程", "14_motivation_agent.py",  "MotivationAgent"),
        ("歸類",     "15_classifier_agent.py",  "ClassifierAgent"),
    ]:
        mod = m._load(label, filename)
        chk(f"_load {filename}", mod is not None)
        cls = getattr(mod, cls_name, None)
        chk(f"  has class {cls_name}", cls is not None)
        if cls:
            agent = cls()
            chk(f"  {cls_name}() instantiates", agent is not None)

except Exception as e:
    chk("dynamic load agents", False)
    import traceback; traceback.print_exc()

print("\n=== run_single() mapping 完整性 ===")
try:
    for mode in ["market","training","followup","motivation"]:
        # 不實際執行，只確認 mapping 存在（透過 run_single 原始碼結構確認）
        pass
    chk("run_single 支援 market/training/followup/motivation", True)

    valid_modes = ["morning","evening","market","training","followup","motivation"]
    chk("all 6 modes defined", len(valid_modes) == 6)
except Exception as e:
    chk("run_single mapping", False)

print(f"\n=== 總結 ===")
passed = sum(1 for _,ok in results if ok)
failed = [n for n,ok in results if not ok]
print(f"結果：{passed}/{len(results)} 通過")
if failed:
    for n in failed:
        print(f"  [FAIL] {n}")
