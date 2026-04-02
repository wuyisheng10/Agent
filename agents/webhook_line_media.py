def handle_image_message(
    event: dict,
    mode_info: dict,
    clf,
    *,
    download_line_content,
    reply_message,
    push_message,
    nutrition_sessions,
    load_nutrition_assessment,
    load_training,
    schedule_pending_menu,
):
    msg_id = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id = event.get("source", {}).get("userId", "")
    group_id = event.get("source", {}).get("groupId", "")
    scope_id = group_id or user_id
    push_target = group_id or user_id

    img_bytes = download_line_content(msg_id)
    if img_bytes is None:
        reply_message(reply_token, "⚠️ 圖片下載失敗，請重試")
        return

    if scope_id in nutrition_sessions and nutrition_sessions[scope_id].get("awaiting_photo"):
        try:
            na_mod = load_nutrition_assessment()
            session = nutrition_sessions[scope_id]
            meal_label = session.pop("next_meal_label", None)
            result = na_mod.NutritionAssessmentAgent().add_photo(session, img_bytes, meal_label)
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 加入照片失敗：{e}")
        return

    mode = (mode_info or {}).get("mode", "auto")
    person = (mode_info or {}).get("person", "")

    if clf is not None and mode != "auto":
        clf.route_image(img_bytes, msg_id, mode, person, reply_message, push_message, reply_token, push_target)
        return

    if clf is not None:
        clf.stage_file(
            img_bytes,
            f"image_{msg_id}.jpg",
            "image",
            scope_id,
            content_type="image/jpeg",
            source_name=event.get("message", {}).get("type", "image"),
        )
        schedule_pending_menu(clf, scope_id, scope_id)
        return

    tl = load_training()
    date_str = __import__("datetime").datetime.now().strftime("%Y%m%d")
    filename = f"image_{msg_id}.jpg"
    tl.archive_image(img_bytes, filename, date_str)
    reply_message(reply_token, f"📸 圖片已歸檔（{date_str}）")


def handle_audio_message(
    event: dict,
    mode_info: dict,
    clf,
    *,
    download_line_content,
    reply_message,
    schedule_pending_menu,
    awaiting_partner_voice_add,
    load_partner,
):
    msg_id = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id = event.get("source", {}).get("userId", "")
    group_id = event.get("source", {}).get("groupId", "")
    scope_id = group_id or user_id

    data = download_line_content(msg_id, timeout=60)
    if data is None:
        reply_message(reply_token, "⚠️ 音檔下載失敗，請重試")
        return

    if awaiting_partner_voice_add.get(scope_id):
        awaiting_partner_voice_add.pop(scope_id, None)
        try:
            transcript = _transcribe_audio_bytes(data)
            command = normalize_voice_followup_add(transcript)
            result = load_partner().handle_partner_command(command)
            reply_message(
                reply_token,
                "🎙️ 已完成語音新增跟進夥伴\n"
                f"轉文字內容：\n{transcript}\n\n{result}",
            )
        except Exception as e:
            reply_message(
                reply_token,
                "⚠️ 語音新增跟進夥伴失敗\n"
                f"{e}\n\n"
                "請改用這個格式手動送出：\n"
                "新增跟進夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類",
            )
        return

    mode = (mode_info or {}).get("mode", "auto")
    person = (mode_info or {}).get("person", "")
    date_str = (mode_info or {}).get("archive_date", "")
    filename = f"audio_{msg_id}.m4a"

    if mode != "auto":
        saved = clf.archive_file(data, filename, mode, "audio", person, date_str)
        person_tag = f"「{person}」的" if person else ""
        reply_message(reply_token, f"🎤 音檔已歸入{person_tag}「{mode}」\n路徑：.../{'/'.join(saved.parts[-4:])}")
        return

    clf.stage_file(data, filename, "audio", scope_id, content_type="audio/m4a", source_name=event.get("message", {}).get("type", "audio"))
    schedule_pending_menu(clf, scope_id, scope_id)


def handle_video_message(
    event: dict,
    mode_info: dict,
    clf,
    *,
    download_line_content,
    reply_message,
    schedule_pending_menu,
):
    msg_id = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id = event.get("source", {}).get("userId", "")
    group_id = event.get("source", {}).get("groupId", "")
    scope_id = group_id or user_id

    data = download_line_content(msg_id, timeout=120)
    if data is None:
        reply_message(reply_token, "⚠️ 影片下載失敗，請重試")
        return

    mode = (mode_info or {}).get("mode", "auto")
    person = (mode_info or {}).get("person", "")
    date_str = (mode_info or {}).get("archive_date", "")
    filename = f"video_{msg_id}.mp4"

    if mode != "auto":
        saved = clf.archive_file(data, filename, mode, "videos", person, date_str)
        person_tag = f"「{person}」的" if person else ""
        reply_message(reply_token, f"🎬 影片已歸入{person_tag}「{mode}」\n路徑：.../{'/'.join(saved.parts[-4:])}")
        return

    clf.stage_file(data, filename, "video", scope_id, content_type="video/mp4", source_name=event.get("message", {}).get("type", "video"))
    schedule_pending_menu(clf, scope_id, scope_id)


def handle_file_message(
    event: dict,
    mode_info: dict,
    clf,
    *,
    download_line_content,
    reply_message,
    schedule_pending_menu,
):
    msg_id = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id = event.get("source", {}).get("userId", "")
    group_id = event.get("source", {}).get("groupId", "")
    scope_id = group_id or user_id

    orig_name = event["message"].get("fileName", "")
    safe = "".join(c for c in orig_name if c.isalnum() or c in "._- ()[]") or f"file_{msg_id}"
    data = download_line_content(msg_id, timeout=60)
    if data is None:
        reply_message(reply_token, "⚠️ 檔案下載失敗，請重試")
        return

    mode = (mode_info or {}).get("mode", "auto")
    person = (mode_info or {}).get("person", "")
    date_str = (mode_info or {}).get("archive_date", "")

    if mode != "auto":
        saved = clf.archive_file(data, safe, mode, "files", person, date_str)
        person_tag = f"「{person}」的" if person else ""
        reply_message(reply_token, f"📄 檔案已歸入{person_tag}「{mode}」\n路徑：.../{'/'.join(saved.parts[-4:])}")
        return

    clf.stage_file(data, safe, "file", scope_id, content_type=event.get("message", {}).get("fileName", ""), source_name=orig_name)
    schedule_pending_menu(clf, scope_id, scope_id)

import os
import re
from tempfile import NamedTemporaryFile

try:
    from webhook_partner_voice import normalize_voice_followup_add
except Exception:  # pragma: no cover
    from agents.webhook_partner_voice import normalize_voice_followup_add

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


def _transcribe_audio_bytes(audio_bytes: bytes, suffix: str = ".m4a") -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("未設定 OPENAI_API_KEY，無法執行語音轉文字")
    if requests is None:
        raise RuntimeError("缺少 requests，無法執行語音轉文字")
    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            resp = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                data={"model": "gpt-4o-mini-transcribe", "language": "zh"},
                files={"file": (os.path.basename(tmp_path), f, "audio/m4a")},
                timeout=120,
            )
        if not resp.ok:
            raise RuntimeError(f"語音轉文字失敗：{resp.status_code} {resp.text[:200]}")
        return (resp.json().get("text", "") or "").strip()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _normalize_voice_add_command(transcript: str) -> str:
    text = (transcript or "").strip()
    if not text:
        raise ValueError("語音內容為空")
    text = text.replace("，", ",").replace("。", ",").replace("；", ",")
    text = re.sub(r"\s+", " ", text)
    name = goal = next_followup = note = category = ""
    m = re.search(r"(?:姓名|夥伴|跟進夥伴)\s*[:：]?\s*([^\s,]+)", text)
    if m:
        name = m.group(1).strip()
    m = re.search(r"目標\s*[:：]?\s*([^,]+)", text)
    if m:
        goal = m.group(1).strip()
    m = re.search(r"(?:下次跟進|跟進日期|日期)\s*[:：]?\s*([^,]+)", text)
    if m:
        next_followup = m.group(1).strip()
    m = re.search(r"備註\s*[:：]?\s*([^,]+)", text)
    if m:
        note = m.group(1).strip()
    m = re.search(r"分類\s*[:：]?\s*([ABCabc])", text)
    if m:
        category = m.group(1).upper()
    next_followup = (
        next_followup.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(" ", "")
    )
    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", next_followup or ""):
        y, mo, d = next_followup.split("-")
        next_followup = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    if not name or not next_followup:
        raise ValueError("語音內容缺少姓名或日期")
    return f"新增跟進夥伴 {name} | {goal} | {next_followup} | {note} | {category}"
