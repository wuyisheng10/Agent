"""Local test: CSV agents (market_dev / training / followup / motivation)"""
import sys, csv, shutil
from pathlib import Path
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')

BASE    = Path(r"C:\Users\user\claude AI_Agent")
CSV_DIR = BASE / "output" / "csv_data"
sys.path.insert(0, str(BASE / "agents"))

import importlib.util as ilu
def load(name, file):
    spec = ilu.spec_from_file_location(name, str(BASE / "agents" / file))
    m = ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

results = []
def chk(name, cond):
    results.append((name, bool(cond)))
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}")

# ── 備份 & 建立測試 CSV ─────────────────────────────────────────
CSV_DIR.mkdir(parents=True, exist_ok=True)
MARKET_CSV   = CSV_DIR / "market_list.csv"
PARTNERS_CSV = CSV_DIR / "partners.csv"
MOTIV_CSV    = CSV_DIR / "motivation_log.csv"

orig_market   = MARKET_CSV.read_bytes()   if MARKET_CSV.exists()   else None
orig_partners = PARTNERS_CSV.read_bytes() if PARTNERS_CSV.exists() else None
orig_motiv    = MOTIV_CSV.read_bytes()    if MOTIV_CSV.exists()    else None

today            = date.today().strftime("%Y-%m-%d")
joined_3days_ago = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
last_4days       = (date.today() - timedelta(days=4)).strftime("%Y-%m-%d")
last_7days       = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")

MARKET_FIELDS = ["姓名","電話","職業","接觸管道","備註",
                 "AI評分","需求標籤","話術_健康型","話術_收入型","話術_好奇型",
                 "接觸狀態","最後更新","下次跟進日"]
PARTNER_FIELDS = ["姓名","LINE_UID","電話","加入日期",
                  "已完成培訓天","最後培訓推播日","最後聯絡日",
                  "本週動作數","風險等級","里程碑","備註"]

with open(MARKET_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=MARKET_FIELDS)
    w.writeheader()
    w.writerow({"姓名":"測試潛客A","電話":"0912345678","職業":"上班族",
                "接觸管道":"Facebook","備註":"喜歡健康產品",
                "AI評分":"","需求標籤":"","話術_健康型":"","話術_收入型":"","話術_好奇型":"",
                "接觸狀態":"待評分","最後更新":today,"下次跟進日":""})
    w.writerow({"姓名":"測試潛客B","電話":"0987654321","職業":"家庭主婦",
                "接觸管道":"Instagram","備註":"有副業需求",
                "AI評分":"4","需求標籤":"收入型","話術_健康型":"A","話術_收入型":"B","話術_好奇型":"C",
                "接觸狀態":"初接觸","最後更新":today,"下次跟進日":""})

with open(PARTNERS_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=PARTNER_FIELDS)
    w.writeheader()
    # 正常
    w.writerow({"姓名":"正常夥伴","LINE_UID":"Uabc001","電話":"0911111111",
                "加入日期":joined_3days_ago,"已完成培訓天":"1,3",
                "最後培訓推播日":today,"最後聯絡日":today,
                "本週動作數":"3","風險等級":"","里程碑":"","備註":"積極參與"})
    # 黃色
    w.writerow({"姓名":"中風險夥伴","LINE_UID":"Uabc002","電話":"0922222222",
                "加入日期":(date.today()-timedelta(days=10)).strftime("%Y-%m-%d"),
                "已完成培訓天":"1",
                "最後培訓推播日":last_4days,"最後聯絡日":last_7days,
                "本週動作數":"2","風險等級":"","里程碑":"","備註":"需要關注"})
    # 紅色
    w.writerow({"姓名":"高風險夥伴","LINE_UID":"Uabc003","電話":"0933333333",
                "加入日期":(date.today()-timedelta(days=14)).strftime("%Y-%m-%d"),
                "已完成培訓天":"1,3",
                "最後培訓推播日":last_4days,"最後聯絡日":last_4days,
                "本週動作數":"0","風險等級":"","里程碑":"","備註":"沉默中"})

# ── 11_market_dev_agent ────────────────────────────────────────
print("\n=== [1] 11_market_dev_agent ===")
try:
    mkt = load("market", "11_market_dev_agent.py")
    rows = mkt.read_csv()
    chk("read_csv returns 2 rows", len(rows) == 2)
    unscored = [r for r in rows if not r.get("AI評分","").strip()]
    chk("unscored count == 1", len(unscored) == 1)
    chk("unscored row is 測試潛客A", unscored[0]["姓名"] == "測試潛客A")

    mkt.append_row({"姓名":"新增測試C","電話":"","職業":"學生",
                    "接觸管道":"LINE","備註":"測試新增",
                    "AI評分":"","需求標籤":"","話術_健康型":"","話術_收入型":"","話術_好奇型":"",
                    "接觸狀態":"待評分","最後更新":today,"下次跟進日":""})
    rows2 = mkt.read_csv()
    chk("append_row increases count to 3", len(rows2) == 3)
    chk("appended row name correct", rows2[-1]["姓名"] == "新增測試C")
except Exception as e:
    chk("market_dev_agent import", False)
    print(f"  ERROR: {e}")

# ── 12_training_agent ─────────────────────────────────────────
print("\n=== [2] 12_training_agent ===")
try:
    tra = load("training", "12_training_agent.py")
    rows = tra.read_csv()
    chk("read_csv returns 3 rows", len(rows) == 3)

    agent = tra.TrainingAgent()

    r = agent.handle_query("培訓 正常夥伴")
    chk("handle_query found partner", "正常夥伴" in r)
    chk("handle_query has day/training info", any(k in r for k in ["Day","天","培訓","完成"]))

    r_miss = agent.handle_query("培訓 不存在夥伴")
    chk("handle_query not found msg", any(k in r_miss for k in ["找不到","⚠","沒有"]))

    days = tra.days_since(joined_3days_ago)
    chk("days_since == 3", days == 3)

    chk("CURRICULUM has day1", 1 in tra.CURRICULUM)
    chk("CURRICULUM has day7", 7 in tra.CURRICULUM)
    chk("CURRICULUM has day30", 30 in tra.CURRICULUM)
except Exception as e:
    chk("training_agent import", False)
    import traceback; traceback.print_exc()

# ── 13_followup_agent ─────────────────────────────────────────
print("\n=== [3] 13_followup_agent ===")
try:
    fol = load("followup", "13_followup_agent.py")
    rows = fol.read_csv()
    chk("read_csv returns 3 rows", len(rows) == 3)

    agent = fol.FollowupAgent()
    risk0 = fol.classify_risk(rows[0], agent.red_days, agent.yellow_days)
    risk1 = fol.classify_risk(rows[1], agent.red_days, agent.yellow_days)
    risk2 = fol.classify_risk(rows[2], agent.red_days, agent.yellow_days)
    chk("正常夥伴 => green", risk0 == "green")
    chk("中風險夥伴 7days => yellow", risk1 == "yellow")
    chk("高風險夥伴 4days+0actions => red", risk2 == "red")

    # monkey-patch Claude call
    fol.generate_followup_draft = lambda partner, days: "(測試草稿)"
    report = agent.generate_report_text()
    chk("report contains 🔴", "🔴" in report)
    chk("report contains 🟡", "🟡" in report)
    chk("report contains 🟢", "🟢" in report)
    chk("report has 高風險夥伴 in red", "高風險夥伴" in report)
    chk("report has 中風險夥伴 in yellow", "中風險夥伴" in report)
    chk("report has 正常夥伴 in green", "正常夥伴" in report)
    chk("report has draft content", "測試草稿" in report)

    # 風險等級寫回 CSV
    rows_after = fol.read_csv()
    risk_levels = {r["姓名"]: r.get("風險等級","") for r in rows_after}
    chk("CSV 風險等級 正常夥伴 updated", "🟢" in risk_levels.get("正常夥伴",""))
    chk("CSV 風險等級 高風險夥伴 updated", "🔴" in risk_levels.get("高風險夥伴",""))
except Exception as e:
    chk("followup_agent import", False)
    import traceback; traceback.print_exc()

# ── 14_motivation_agent ───────────────────────────────────────
print("\n=== [4] 14_motivation_agent ===")
try:
    mot = load("motivation", "14_motivation_agent.py")
    rows = mot.read_partners()
    chk("read_partners returns 3", len(rows) == 3)

    p = mot.get_partner("正常夥伴")
    chk("get_partner found", p["姓名"] == "正常夥伴")
    p_miss = mot.get_partner("不存在")
    chk("get_partner missing => dict with name", p_miss["姓名"] == "不存在")

    agent = mot.MotivationAgent()

    r_bad = agent.handle_realtime("激勵")
    chk("handle_realtime 無名稱 => error msg", any(k in r_bad for k in ["格式","⚠"]))

    mot.append_motivation_log("正常夥伴","test","情境","回應")
    chk("motivation_log created", MOTIV_CSV.exists())
    with open(MOTIV_CSV, encoding="utf-8-sig") as f:
        log_rows = list(csv.DictReader(f))
    chk("motivation_log has entry", len(log_rows) >= 1)
    chk("motivation_log content ok", log_rows[-1]["夥伴姓名"] == "正常夥伴")

    # monkey-patch Claude
    mot.generate_milestone_celebration = lambda p, a: "恭喜達成里程碑！測試訊息"
    r_ms = agent._handle_milestone("正常夥伴", "第一單")
    chk("milestone reply has partner name", "正常夥伴" in r_ms)
    chk("milestone reply has content", "里程碑" in r_ms or "慶賀" in r_ms)
    rows_upd = mot.read_partners()
    p_upd = next((r for r in rows_upd if r["姓名"] == "正常夥伴"), {})
    chk("milestone CSV 里程碑 updated", "第一單" in p_upd.get("里程碑",""))

    # monkey-patch emotion support
    mot.generate_emotion_support = lambda p, c: "加油！你做得到的，測試鼓勵文"
    r_em = agent._handle_emotion("正常夥伴", "感覺好累")
    chk("emotion reply has partner name", "正常夥伴" in r_em)
    chk("emotion reply has content", "加油" in r_em or "激勵" in r_em)
except Exception as e:
    chk("motivation_agent import", False)
    import traceback; traceback.print_exc()

# ── 還原 CSV ──────────────────────────────────────────────────
if orig_market:   MARKET_CSV.write_bytes(orig_market)
else:             MARKET_CSV.unlink(missing_ok=True)
if orig_partners: PARTNERS_CSV.write_bytes(orig_partners)
else:             PARTNERS_CSV.unlink(missing_ok=True)
if orig_motiv:    MOTIV_CSV.write_bytes(orig_motiv)
else:             MOTIV_CSV.unlink(missing_ok=True)
print("\n  (原始 CSV 已還原)")

print("\n=== CSV Agents 總結 ===")
passed = sum(1 for _,ok in results if ok)
failed = [(n,ok) for n,ok in results if not ok]
print(f"結果：{passed}/{len(results)} 通過")
if failed:
    print("失敗項目：")
    for n, _ in failed:
        print(f"  [FAIL] {n}")
