import re


def normalize_voice_followup_add(transcript: str) -> str:
    text = (transcript or "").strip()
    if not text:
        raise ValueError("語音內容為空")

    text = re.sub(r"\s+", " ", text.replace("，", ",").replace("：", ":"))
    name = next_followup = note = ""

    m = re.search(r"(?:姓名|夥伴|跟進夥伴)\s*[: ]\s*([^\s,]+)", text)
    if m:
        name = m.group(1).strip()
    else:
        m = re.search(r"新增跟進夥伴\s*([^\s,]+)", text)
        if m:
            name = m.group(1).strip()

    m = re.search(r"(?:下次跟進日期|跟進日期|日期)\s*[: ]\s*([^,]+)", text)
    if m:
        next_followup = m.group(1).strip()

    m = re.search(r"備註\s*[: ]\s*([^,]+)", text)
    if m:
        note = m.group(1).strip()

    next_followup = (
        next_followup.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(" ", "")
    )
    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", next_followup or ""):
        y, mo, d = next_followup.split("-")
        next_followup = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    if not name or not next_followup:
        raise ValueError("語音內容缺少姓名或下次跟進日期")

    return f"新增跟進夥伴 {name} | {next_followup} | {note}"
