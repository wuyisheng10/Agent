"""
Nutrition Assessment Agent (Agent 19)
File: agents/19_nutrition_assessment_agent.py
Purpose: Analyze meal photos with Codex CLI, compare against DRI, email and archive the report
Commands:
  開始飲食評估 / 設定餐別 / 設定評估對象 / 評估飲食 / 清除飲食評估 / 飲食評估狀態
"""

from __future__ import annotations

import importlib.util as _ilu
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
REPORT_DIR = BASE_DIR / "output" / "nutrition_reports"
LOGS_DIR = BASE_DIR / "logs"

DEFAULT_RECIPIENT = "wuyisheng10@gmail.com"
MEAL_LABELS = ("早餐", "午餐", "晚餐")


def _load_dri_agent():
    spec = _ilu.spec_from_file_location(
        "nutrition_dri_agent",
        str(BASE_DIR / "agents" / "18_nutrition_dri_agent.py"),
    )
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_email():
    spec = _ilu.spec_from_file_location(
        "email_notify",
        str(BASE_DIR / "agents" / "email_notify.py"),
    )
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_classifier():
    spec = _ilu.spec_from_file_location(
        "classifier_agent",
        str(BASE_DIR / "agents" / "15_classifier_agent.py"),
    )
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_codex_cli() -> list[str]:
    appdata = Path(os.getenv("APPDATA", r"C:\Users\user\AppData\Roaming"))
    node_exe = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    script_path = appdata / "npm" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
    if Path(node_exe).exists() and script_path.exists():
        return [node_exe, str(script_path)]
    codex_cmd = shutil.which("codex") or shutil.which("codex.cmd")
    if codex_cmd:
        return [codex_cmd]
    raise FileNotFoundError("找不到 Codex CLI，請確認已安裝且 PATH 可用")


def _run_codex_cli(prompt: str, timeout: int = 120, image_path: str | None = None) -> str:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    response_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False, dir=str(LOGS_DIR)
        ) as fh:
            response_path = fh.name

        command = [
            *_resolve_codex_cli(),
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--color",
            "never",
            "-C",
            str(BASE_DIR),
            "-o",
            response_path,
        ]
        if image_path:
            command.extend(["--image", image_path])
        command.append("-")

        result = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "codex CLI 回傳非零")

        output = ""
        if response_path and os.path.exists(response_path):
            output = Path(response_path).read_text(encoding="utf-8").strip()
        return output or result.stdout.strip()
    finally:
        if response_path and os.path.exists(response_path):
            try:
                os.unlink(response_path)
            except OSError:
                pass


def _analyze_image_with_codex(img_bytes: bytes, meal_label: str, timeout: int = 120) -> str:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    img_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".jpg", delete=False, dir=str(LOGS_DIR)) as fh:
            fh.write(img_bytes)
            img_path = fh.name

        prompt = (
            f"You are analyzing a meal photo for {meal_label}. "
            "Answer in Traditional Chinese.\n"
            "Please provide:\n"
            "1. Visible foods and drinks.\n"
            "2. Estimated macros: protein (g), carbs (g), fat (g), calories (kcal).\n"
            "3. Micronutrients likely to be sufficient in this meal.\n"
            "4. Micronutrients likely to be lacking in this meal.\n"
            "5. A short note about overall balance and obvious risks.\n"
            "Be practical and mention when something is only an estimate."
        )
        return _run_codex_cli(prompt, timeout=timeout, image_path=img_path)
    finally:
        if img_path and os.path.exists(img_path):
            try:
                os.unlink(img_path)
            except OSError:
                pass


def _basic_assessment_text(analyses: list[dict], water_ml: int, gender_label: str, age: int, error: str = "") -> str:
    lines = [
        "## 飲食評估（基本版）",
        f"受評估者：{gender_label} {age} 歲　飲水量：{water_ml} ml",
        "",
        "### 餐點記錄",
    ]
    for item in analyses:
        lines.append(f"- **{item['label']}**：{item['analysis'][:160]}")
    if error:
        lines.extend([
            "",
            f"⚠️ AI 評估暫時無法完整使用（{error[:120]}）",
            "請確認 Codex CLI 已正確安裝並可連線。",
        ])
    return "\n".join(lines)


def _assess_deficiencies(analyses: list[dict], water_ml: int, gender: str, age: int) -> dict:
    gender_key = "M" if str(gender).upper() in ("M", "男") else "F"
    gender_label = "男性" if gender_key == "M" else "女性"

    dri_mod = _load_dri_agent()
    dri_agent = dri_mod.NutritionDRIAgent()
    dri_group, dri_values = dri_agent._match_age_group(age, gender_key)
    dri_summary = json.dumps(dri_values, ensure_ascii=False)

    meals_text = ""
    for item in analyses:
        meals_text += f"\n【{item['label']}】\n{item['analysis']}\n"

    prompt = (
        f"Create a nutrition assessment report in Traditional Chinese for a {gender_label}, age {age}. "
        f"The matched Taiwan DRI age group is {dri_group}.\n\n"
        f"Meal analysis notes:\n{meals_text}\n"
        f"Water intake today: {water_ml} ml. Target water intake: {dri_values.get('水', 2000)} ml.\n\n"
        f"Taiwan DRI reference values for this person:\n{dri_summary}\n\n"
        "Write a detailed report in Traditional Chinese using Markdown with these sections:\n"
        "1. **總體評估**: 1-2 short paragraphs about overall balance.\n"
        "2. **可能缺乏的營養素**: bullet list, and for each nutrient explain severity, likely reason, and long-term risk.\n"
        "3. **可能過剩的營養素**: bullet list, if any.\n"
        "4. **飲水狀況評估**.\n"
        "5. **長期維持這種飲食模式的身體警訊**: specific symptoms in short-term, mid-term, long-term order.\n"
        "6. **改善建議**: 3-5 actionable suggestions.\n"
        "Be practical and state uncertainty when necessary."
    )

    try:
        assessment_text = _run_codex_cli(prompt, timeout=180)
        if not assessment_text:
            raise RuntimeError("Codex CLI 沒有回傳內容")
    except Exception as exc:
        assessment_text = _basic_assessment_text(analyses, water_ml, gender_label, age, str(exc))

    return {
        "gender": gender_label,
        "age": age,
        "dri_group": dri_group,
        "water_ml": water_ml,
        "water_target": dri_values.get("水", 2000),
        "meals": analyses,
        "assessment_md": assessment_text,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _format_report_html(assessment: dict) -> str:
    import re

    markdown = assessment.get("assessment_md", "")

    def md_to_html(text: str) -> str:
        lines = text.splitlines()
        html_parts = []
        in_list = False
        for line in lines:
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
            if line.startswith("### "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("## "):
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("- ") or line.startswith("* "):
                if not in_list:
                    html_parts.append("<ul>")
                    in_list = True
                html_parts.append(f"<li>{line[2:]}</li>")
            elif line.strip():
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                html_parts.append(f"<p>{line}</p>")
        if in_list:
            html_parts.append("</ul>")
        return "\n".join(html_parts)

    meal_blocks = []
    for meal in assessment.get("meals", []):
        meal_blocks.append(
            "<div style='background:#f8f9fa;border-left:4px solid #4a90d9;padding:12px 16px;"
            "margin:10px 0;border-radius:0 8px 8px 0'>"
            f"<strong>{meal['label']}</strong><br>"
            f"<span style='font-size:13px;color:#555;line-height:1.7'>{meal['analysis'].replace(chr(10), '<br>')}</span>"
            "</div>"
        )

    water_ml = assessment.get("water_ml", 0)
    water_target = assessment.get("water_target", 2000)
    water_pct = min(100, int(water_ml / water_target * 100)) if water_target else 0
    water_color = "#4caf50" if water_pct >= 80 else "#ff9800" if water_pct >= 50 else "#f44336"

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>飲食營養評估報告</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:700px;margin:0 auto;padding:24px;color:#333">
<div style="background:linear-gradient(135deg,#1a3a5c,#2c5f8a);color:white;padding:24px;border-radius:12px;margin-bottom:24px">
  <h1 style="margin:0;font-size:22px">🥗 飲食營養評估報告</h1>
  <p style="margin:8px 0 0;opacity:.85">{assessment.get("gender","")} {assessment.get("age","")} 歲 / DRI 組別：{assessment.get("dri_group","")}</p>
  <p style="margin:4px 0 0;font-size:13px;opacity:.7">產生時間：{assessment.get("generated_at","")}</p>
</div>

<div style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:20px;margin-bottom:20px">
  <h2 style="color:#1a3a5c;margin-top:0;border-bottom:2px solid #e0e0e0;padding-bottom:8px">餐點紀錄</h2>
  {''.join(meal_blocks) if meal_blocks else '<p style="color:#888">沒有餐點資料</p>'}
  <div style="margin-top:16px;padding:12px;background:#e8f4fd;border-radius:8px">
    <strong>飲水量</strong>：{water_ml} ml / {water_target} ml（{water_pct}%）
    <div style="background:#ddd;border-radius:4px;height:8px;margin-top:8px">
      <div style="background:{water_color};width:{water_pct}%;height:8px;border-radius:4px"></div>
    </div>
  </div>
</div>

<div style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:20px;margin-bottom:20px">
  {md_to_html(markdown)}
</div>

<div style="text-align:center;color:#999;font-size:12px;margin-top:20px;padding-top:16px;border-top:1px solid #eee">
  <p>本報告由 Yisheng AI 助理依據台灣衛生福利部國人膳食營養素參考攝取量第八版(2022)生成</p>
  <p>僅供參考，如有健康疑慮請諮詢醫師或營養師</p>
</div>
</body>
</html>"""


class NutritionAssessmentAgent:
    def start_session(self, gender: str, age: int, person_name: str = "") -> dict:
        return {
            "gender": gender,
            "age": age,
            "person_name": person_name,
            "photos": [],
            "water_ml": 0,
            "awaiting_photo": True,
            "next_meal_label": None,
        }

    def add_photo(self, session: dict, img_bytes: bytes, meal_label: str | None = None) -> str:
        photos = session.setdefault("photos", [])
        if len(photos) >= 3:
            return "⚠️ 已達上限（3 張），請先執行評估：\n小幫手 評估飲食 喝水量XXXml"

        if not meal_label:
            next_label = session.get("next_meal_label")
            if next_label:
                meal_label = next_label
            else:
                meal_label = MEAL_LABELS[min(len(photos), len(MEAL_LABELS) - 1)]

        photos.append({"bytes": img_bytes, "label": meal_label})
        session["next_meal_label"] = None

        count = len(photos)
        next_hint = ""
        if count < 3:
            next_hint = f"\n➡️ 繼續上傳 {MEAL_LABELS[count]}（或其他餐）"

        return (
            f"📸 已收到{meal_label}照片（{count}/3）"
            f"{next_hint}\n\n"
            "完成後輸入：\n小幫手 評估飲食 喝水量XXXml"
        )

    def set_next_meal_label(self, session: dict, meal: str) -> str:
        session["next_meal_label"] = meal
        return f"✅ 已設定：下一張照片將標記為「{meal}」\n請上傳{meal}的照片"

    def _archive_session_files(self, photos: list, html: str, person_name: str, ts: str) -> list[Path]:
        try:
            clf_mod = _load_classifier()
            clf = clf_mod.ClassifierAgent()
            date_str = ts[:8]
            archived = []
            for photo in photos:
                label = photo.get("label", "餐點")
                data = photo.get("bytes", b"")
                if not data:
                    continue
                archived.append(
                    clf.archive_file(data, f"photo_{label}.jpg", "飲食評估", person=person_name, date_str=date_str)
                )
            archived.append(
                clf.archive_file(html.encode("utf-8"), f"nutrition_report_{ts[9:]}.html", "飲食評估", person=person_name, date_str=date_str)
            )
            return archived
        except Exception as exc:
            print(f"[NutritionAssessment] Archive failed: {exc}")
            return []

    def send_report_email(self, html_report: str, recipient: str = DEFAULT_RECIPIENT, gender: str = "", age: int = 0) -> bool:
        try:
            email_mod = _load_email()
            subject = f"[營養評估報告] {gender} {age}歲 — {datetime.now().strftime('%Y/%m/%d')}"
            return email_mod.send_email_to(subject, html_report, [recipient])
        except Exception as exc:
            print(f"[NutritionAssessment] Email failed: {exc}")
            return False

    def run_assessment(self, session: dict, water_ml: int) -> tuple[str, str]:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        session["water_ml"] = water_ml
        photos = session.get("photos", [])
        gender = session.get("gender", "M")
        age = session.get("age", 30)

        analyses = []
        for photo in photos:
            label = photo.get("label", "餐點")
            analysis = _analyze_image_with_codex(photo.get("bytes", b""), label)
            analyses.append({"label": label, "analysis": analysis})

        if not analyses:
            return "⚠️ 沒有餐點照片，無法進行評估", ""

        assessment = _assess_deficiencies(analyses, water_ml, gender, age)
        html = _format_report_html(assessment)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORT_DIR / f"nutrition_report_{ts}.html"
        report_path.write_text(html, encoding="utf-8")

        person_name = session.get("person_name", "")
        archived_paths = self._archive_session_files(photos, html, person_name, ts)
        person_tag = f"「{person_name}」" if person_name else ""
        archive_note = f"\n📂 已歸檔{person_tag}（{len(archived_paths)} 個檔案）" if archived_paths else ""

        summary_lines = [line for line in assessment.get("assessment_md", "").splitlines() if line.strip()][:15]
        line_summary = (
            "🥗 飲食評估完成\n"
            "────────────────────\n"
            + "\n".join(summary_lines)
            + "\n────────────────────\n📧 完整報告已寄至信箱"
            + archive_note
        )
        return line_summary, html


def handle_command(cmd: str, sessions: dict, scope_id: str, push_fn=None, reply_fn=None, reply_token: str = "") -> str:
    import re

    agent = NutritionAssessmentAgent()
    cmd = cmd.strip()

    if cmd.startswith("開始飲食評估"):
        rest = cmd.replace("開始飲食評估", "", 1).strip()
        gender = "M"
        age = 30
        person_name = ""
        for token in rest.split():
            if token in ("男", "男性", "M", "m"):
                gender = "M"
            elif token in ("女", "女性", "F", "f"):
                gender = "F"
            elif re.fullmatch(r"\d{1,3}", token):
                age = int(token)
            elif token.startswith("對象:") or token.startswith("對象："):
                person_name = token.split(":", 1)[-1].split("：", 1)[-1].strip()
            elif token not in ("男", "男性", "女", "女性", "M", "m", "F", "f"):
                person_name = token

        sessions[scope_id] = agent.start_session(gender, age, person_name)
        gender_label = "男性" if gender == "M" else "女性"
        person_note = f"\n歸檔對象：{person_name}" if person_name else "\n（未設定歸檔對象，可輸入「設定評估對象 姓名」）"
        return (
            "✅ 飲食評估已開始\n"
            f"設定：{gender_label} {age} 歲"
            f"{person_note}\n\n"
            "請依序上傳今日餐點照片（最多 3 張）\n"
            "可先輸入「小幫手 設定餐別 早餐」指定下一張照片的餐別\n\n"
            "完成後輸入：\n小幫手 評估飲食 喝水量1500ml"
        )

    if cmd.startswith("設定評估對象"):
        name = cmd.replace("設定評估對象", "", 1).strip()
        if not name:
            return "請提供姓名，例如：小幫手 設定評估對象 王小明"
        if scope_id not in sessions:
            return "⚠️ 請先開始評估：\n小幫手 開始飲食評估 男 30"
        sessions[scope_id]["person_name"] = name
        return f"✅ 歸檔對象已設定為「{name}」\n照片與報告將歸入：classified/{name}/飲食評估/"

    if cmd.startswith("設定餐別"):
        meal = cmd.replace("設定餐別", "", 1).strip()
        if not meal:
            return "請指定餐別，例如：小幫手 設定餐別 早餐"
        if scope_id not in sessions:
            return "⚠️ 請先開始評估：\n小幫手 開始飲食評估 男 30"
        return agent.set_next_meal_label(sessions[scope_id], meal)

    if cmd.startswith("評估飲食"):
        if scope_id not in sessions:
            return "⚠️ 請先輸入：\n小幫手 開始飲食評估 性別M 年齡30\n然後上傳餐點照片"
        water_ml = 0
        match = re.search(r"(\d+)\s*ml", cmd, re.IGNORECASE)
        if match:
            water_ml = int(match.group(1))
        line_summary, html = agent.run_assessment(sessions[scope_id], water_ml)
        if html:
            agent.send_report_email(
                html,
                recipient=DEFAULT_RECIPIENT,
                gender=sessions[scope_id].get("gender", "M"),
                age=sessions[scope_id].get("age", 30),
            )
        sessions.pop(scope_id, None)
        return line_summary

    if cmd in ("清除飲食評估", "取消飲食評估"):
        sessions.pop(scope_id, None)
        return "✅ 已清除飲食評估記錄"

    if cmd == "飲食評估狀態":
        if scope_id not in sessions:
            return "目前沒有進行中的飲食評估\n開始：小幫手 開始飲食評估 男 30"
        session = sessions[scope_id]
        photos = session.get("photos", [])
        lines = [
            "📊 飲食評估進行中",
            f"設定：{'男性' if session.get('gender') == 'M' else '女性'} {session.get('age')} 歲",
            f"歸檔對象：{session.get('person_name') or '未設定'}",
            f"已收照片：{len(photos)}/3 張",
        ]
        for photo in photos:
            lines.append(f"  • {photo['label']}")
        lines.extend([
            "",
            "設定歸檔對象：小幫手 設定評估對象 姓名",
            "完成後：小幫手 評估飲食 喝水量XXXml",
        ])
        return "\n".join(lines)

    return ""


def _load_prompt_manager():
    spec = _ilu.spec_from_file_location(
        "ai_prompt_manager",
        str(BASE_DIR / "agents" / "20_ai_prompt_manager.py"),
    )
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_skill_manager():
    spec = _ilu.spec_from_file_location(
        "ai_skill_manager",
        str(BASE_DIR / "agents" / "22_ai_skill_manager.py"),
    )
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _with_nutrition_skill(prompt: str) -> str:
    try:
        skill_text = _load_skill_manager().render_skill("nutrition_assessment_strategy").strip()
    except Exception:
        skill_text = ""
    return f"{skill_text}\n\n{prompt}".strip() if skill_text else prompt


def _analyze_image_with_codex(img_bytes: bytes, meal_label: str, timeout: int = 120) -> str:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    img_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".jpg", delete=False, dir=str(LOGS_DIR)) as fh:
            fh.write(img_bytes)
            img_path = fh.name

        pm = _load_prompt_manager()
        prompt = _with_nutrition_skill(pm.render_prompt("nutrition_meal_image_analysis", meal_label=meal_label))
        return _run_codex_cli(prompt, timeout=timeout, image_path=img_path)
    finally:
        if img_path and os.path.exists(img_path):
            try:
                os.unlink(img_path)
            except OSError:
                pass


def _assess_deficiencies(analyses: list[dict], water_ml: int, gender: str, age: int) -> dict:
    gender_key = "M" if str(gender).upper() in ("M", "男", "男性") else "F"
    gender_label = "男性" if gender_key == "M" else "女性"

    dri_mod = _load_dri_agent()
    dri_agent = dri_mod.NutritionDRIAgent()
    dri_group, dri_values = dri_agent._match_age_group(age, gender_key)
    dri_summary = json.dumps(dri_values, ensure_ascii=False)

    meals_text = ""
    for item in analyses:
        meals_text += f"\n【{item['label']}】\n{item['analysis']}\n"

    pm = _load_prompt_manager()
    prompt = _with_nutrition_skill(pm.render_prompt(
        "nutrition_daily_assessment",
        gender_label=gender_label,
        age=age,
        dri_group=dri_group,
        meals_text=meals_text,
        water_ml=water_ml,
        water_target=dri_values.get("水", 2000),
        dri_summary=dri_summary,
    ))

    try:
        assessment_text = _run_codex_cli(prompt, timeout=180)
        if not assessment_text:
            raise RuntimeError("Codex CLI 沒有回傳內容")
    except Exception as exc:
        assessment_text = _basic_assessment_text(analyses, water_ml, gender_label, age, str(exc))

    return {
        "gender": gender_label,
        "age": age,
        "dri_group": dri_group,
        "water_ml": water_ml,
        "water_target": dri_values.get("水", 2000),
        "meals": analyses,
        "assessment_md": assessment_text,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


if __name__ == "__main__":
    _sessions = {}
    print(handle_command("開始飲食評估 女 30 王小美", _sessions, "test"))
    print(handle_command("設定餐別 早餐", _sessions, "test"))
    print(handle_command("飲食評估狀態", _sessions, "test"))
