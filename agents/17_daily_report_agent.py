"""
每日報告 Agent
File: agents/17_daily_report_agent.py
Function: 每日早上 8:00 寄送業務摘要報告
  a. 潛在家人清單
  b. 跟進夥伴清單
  c. 已產生且在今日後的邀約文宣
  d. 今日後的會議活動清單
Recipients: wuyisheng10@gmail.com, kidmanyeh@gmail.com
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

try:
    from common_runtime import BASE_DIR
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR

load_dotenv(dotenv_path=BASE_DIR / ".env")

RECIPIENTS    = ["wuyisheng10@gmail.com", "kidmanyeh@gmail.com"]
DATA_DIR      = BASE_DIR / "output" / "csv_data"
MARKET_CSV    = DATA_DIR / "market_list.csv"
PARTNERS_JSON = BASE_DIR / "output" / "partners" / "partners.json"
MEETINGS_FILE = DATA_DIR / "course_meetings.json"
INVITES_FILE  = DATA_DIR / "course_invites.json"
CALENDAR_FILE = BASE_DIR / "output" / "calendar" / "calendar_events.json"
LOG_FILE      = BASE_DIR / "logs" / "daily_report_log.txt"


def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [DAILY_REPORT] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# Data Loaders
# ============================================================

def _load_prospects() -> list[dict]:
    if not MARKET_CSV.exists():
        return []
    with open(MARKET_CSV, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _load_partners() -> list[dict]:
    if not PARTNERS_JSON.exists():
        return []
    with open(PARTNERS_JSON, encoding="utf-8") as f:
        return json.load(f)


def _load_meetings() -> dict:
    if not MEETINGS_FILE.exists():
        return {}
    with open(MEETINGS_FILE, encoding="utf-8") as f:
        items = json.load(f)
    return {m["id"]: m for m in items}


def _load_upcoming_invites() -> list[dict]:
    if not INVITES_FILE.exists():
        return []
    with open(INVITES_FILE, encoding="utf-8") as f:
        invites = json.load(f)
    meetings = _load_meetings()
    today = date.today().isoformat()
    rows = []
    for rec in invites.values():
        meeting = meetings.get(rec.get("meeting_id", ""))
        if not meeting or meeting.get("date", "") < today:
            continue
        rows.append({**rec, "meeting": meeting})
    rows.sort(key=lambda r: (
        r["meeting"].get("date", "9999-12-31"),
        r["meeting"].get("time") or "99:99",
        r.get("name", ""),
    ))
    return rows


def _load_upcoming_events() -> list[dict]:
    if not CALENDAR_FILE.exists():
        return []
    with open(CALENDAR_FILE, encoding="utf-8") as f:
        events = json.load(f)
    today = date.today().isoformat()
    upcoming = [e for e in events if e.get("date", "") >= today]
    return sorted(upcoming, key=lambda e: (
        e.get("date", "9999-12-31"),
        e.get("time") or "99:99",
        e.get("title", ""),
    ))


# ============================================================
# Report Builder
# ============================================================

def build_report() -> tuple[str, str]:
    """Return (subject, html_body) for the daily report email."""
    today_str = date.today().strftime("%Y/%m/%d")
    now_str   = datetime.now().strftime("%H:%M:%S")

    prospects = _load_prospects()
    partners  = _load_partners()
    invites   = _load_upcoming_invites()
    events    = _load_upcoming_events()

    sections: list[str] = []

    # ── A: 潛在家人清單 ────────────────────────────────────────
    a = [
        "<h3 style='color:#1a5276;border-bottom:2px solid #1a5276;padding-bottom:4px;margin-top:0;'>"
        "📋 潛在家人清單</h3>"
    ]
    if not prospects:
        a.append("<p style='color:#888;'>目前沒有潛在家人資料。</p>")
    else:
        a.append(
            "<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
            "<tr style='background:#1a5276;color:#fff;'>"
            "<th style='padding:6px 8px;text-align:left;'>姓名</th>"
            "<th style='padding:6px 8px;text-align:left;'>職業</th>"
            "<th style='padding:6px 8px;text-align:left;'>接觸狀態</th>"
            "<th style='padding:6px 8px;text-align:left;'>下次跟進日</th>"
            "<th style='padding:6px 8px;text-align:left;'>AI評分</th>"
            "</tr>"
        )
        for i, p in enumerate(prospects):
            bg = "#f2f9ff" if i % 2 == 0 else "#ffffff"
            a.append(
                f"<tr style='background:{bg};'>"
                f"<td style='padding:5px 8px;'>{p.get('姓名','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('職業','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('接觸狀態','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('下次跟進日','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('AI評分','')}</td>"
                "</tr>"
            )
        a.append("</table>")
        a.append(f"<p style='color:#555;font-size:12px;margin-bottom:0;'>共 {len(prospects)} 筆</p>")
    sections.append("\n".join(a))

    # ── B: 跟進夥伴清單 ────────────────────────────────────────
    b = [
        "<h3 style='color:#1e8449;border-bottom:2px solid #1e8449;padding-bottom:4px;margin-top:0;'>"
        "🤝 跟進夥伴清單</h3>"
    ]
    if not partners:
        b.append("<p style='color:#888;'>目前沒有夥伴資料。</p>")
    else:
        b.append(
            "<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
            "<tr style='background:#1e8449;color:#fff;'>"
            "<th style='padding:6px 8px;text-align:left;'>姓名</th>"
            "<th style='padding:6px 8px;text-align:left;'>層級</th>"
            "<th style='padding:6px 8px;text-align:left;'>狀態</th>"
            "<th style='padding:6px 8px;text-align:left;'>下次跟進日</th>"
            "<th style='padding:6px 8px;text-align:left;'>分類</th>"
            "</tr>"
        )
        for i, p in enumerate(partners):
            bg = "#f0fff4" if i % 2 == 0 else "#ffffff"
            b.append(
                f"<tr style='background:{bg};'>"
                f"<td style='padding:5px 8px;'>{p.get('name','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('level','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('stage','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('next_followup','')}</td>"
                f"<td style='padding:5px 8px;'>{p.get('category','')}</td>"
                "</tr>"
            )
        b.append("</table>")
        b.append(f"<p style='color:#555;font-size:12px;margin-bottom:0;'>共 {len(partners)} 筆</p>")
    sections.append("\n".join(b))

    # ── C: 已產生且今日後的邀約文宣 ────────────────────────────
    c = [
        "<h3 style='color:#884ea0;border-bottom:2px solid #884ea0;padding-bottom:4px;margin-top:0;'>"
        "📣 邀約文宣（今日後）</h3>"
    ]
    if not invites:
        c.append("<p style='color:#888;'>目前沒有已產生的邀約文宣。</p>")
    else:
        for inv in invites:
            meeting = inv.get("meeting", {})
            when = meeting.get("date", "")
            if meeting.get("time"):
                when += f" {meeting['time']}"
            role_label = "潛在家人" if inv.get("role") == "prospect" else "跟進夥伴"
            content_html = (inv.get("content", "") or "").replace("\n", "<br>")
            c.append(
                f"<div style='background:#fdf4ff;border-left:4px solid #884ea0;"
                f"padding:10px 14px;margin:8px 0;border-radius:4px;'>"
                f"<strong>📅 {when}｜{meeting.get('title','')}</strong><br>"
                f"<span style='color:#666;font-size:12px;'>對象：{inv.get('name','')}（{role_label}）</span><br>"
                f"<div style='margin-top:6px;font-size:13px;line-height:1.7;'>{content_html}</div>"
                f"</div>"
            )
        c.append(f"<p style='color:#555;font-size:12px;margin-bottom:0;'>共 {len(invites)} 筆</p>")
    sections.append("\n".join(c))

    # ── D: 今日後的行事曆清單 ──────────────────────────────────
    d = [
        "<h3 style='color:#c0392b;border-bottom:2px solid #c0392b;padding-bottom:4px;margin-top:0;'>"
        "🗓️ 行事曆（今日後）</h3>"
    ]
    if not events:
        d.append("<p style='color:#888;'>目前沒有排定的活動。</p>")
    else:
        d.append(
            "<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
            "<tr style='background:#c0392b;color:#fff;'>"
            "<th style='padding:6px 8px;text-align:left;'>日期</th>"
            "<th style='padding:6px 8px;text-align:left;'>時間</th>"
            "<th style='padding:6px 8px;text-align:left;'>標題</th>"
            "<th style='padding:6px 8px;text-align:left;'>備註</th>"
            "</tr>"
        )
        for i, e in enumerate(events):
            bg = "#fff5f5" if i % 2 == 0 else "#ffffff"
            d.append(
                f"<tr style='background:{bg};'>"
                f"<td style='padding:5px 8px;'>{e.get('date','')}</td>"
                f"<td style='padding:5px 8px;'>{e.get('time','')}</td>"
                f"<td style='padding:5px 8px;'>{e.get('title','')}</td>"
                f"<td style='padding:5px 8px;color:#666;'>{e.get('note','')}</td>"
                "</tr>"
            )
        d.append("</table>")
        d.append(f"<p style='color:#555;font-size:12px;margin-bottom:0;'>共 {len(events)} 筆</p>")
    sections.append("\n".join(d))

    divider = "<hr style='border:none;border-top:1px solid #f0f0f0;margin:20px 0;'>"
    html_body = f"""<html><body>
<div style="font-family:Arial,'Microsoft JhengHei',sans-serif;max-width:760px;margin:auto;
            padding:24px;border:1px solid #ddd;border-radius:10px;">
  <h2 style="color:#2c3e50;margin-bottom:4px;">📊 每日業務報告</h2>
  <p style="color:#888;font-size:13px;margin-top:0;">
    報告日期：{today_str}&nbsp;&nbsp;產生時間：{now_str}
  </p>
  <hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
  {divider.join(sections)}
  <hr style="border:none;border-top:1px solid #eee;margin:16px 0;">
  <p style="color:#aaa;font-size:11px;text-align:center;">由 Yisheng AI Agent 自動產生</p>
</div>
</body></html>"""

    subject = f"[每日報告] {today_str} 業務摘要"
    return subject, html_body


# ============================================================
# Agent Class
# ============================================================

class DailyReportAgent:
    def run(self) -> str:
        _log("開始產生每日報告...")
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR / "agents"))
            from email_notify import send_email_to  # noqa: PLC0415

            subject, body = build_report()
            ok = send_email_to(subject, body, RECIPIENTS)
            if ok:
                _log(f"每日報告寄送成功 → {', '.join(RECIPIENTS)}")
                return f"✅ 每日報告已寄送至 {', '.join(RECIPIENTS)}"
            else:
                _log("每日報告寄送失敗")
                return "⚠️ 每日報告寄送失敗，請確認 EMAIL_ENABLED 與信箱設定"
        except Exception as e:
            _log(f"每日報告失敗：{e}")
            return f"✗ 每日報告失敗：{e}"


if __name__ == "__main__":
    result = DailyReportAgent().run()
    print(result)
