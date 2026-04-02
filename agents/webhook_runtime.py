import base64
import hashlib
import hmac
import threading
import time

import requests
from datetime import datetime


def extract_trigger(msg: str, trigger_words) -> str | None:
    for tw in trigger_words:
        if msg.startswith(tw):
            return msg[len(tw):].strip()
    return None


def log_message(msg: str, log_file):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [WEBHOOK] {msg}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def verify_signature(body: bytes, signature: str, line_secret: str) -> bool:
    if not line_secret:
        return True
    hash_val = hmac.new(line_secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(hash_val).decode() == signature


def reply_message(reply_token: str, message: str, line_token: str, line_reply: str, log_func):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_token}",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}],
    }
    r = requests.post(line_reply, headers=headers, json=payload, timeout=5)
    if r.status_code != 200:
        log_func(f"  ⚠️ Reply 失敗：{r.status_code} {r.text[:80]}")


def push_message(user_id: str, message: str, line_token: str, line_push: str, log_func):
    max_len = 4900
    chunks = [message[i:i + max_len] for i in range(0, len(message), max_len)]
    messages = [{"type": "text", "text": c} for c in chunks[:5]]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_token}",
    }
    payload = {"to": user_id, "messages": messages}
    r = requests.post(line_push, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        log_func(f"  ⚠️ Push 失敗：{r.status_code} {r.text[:120]}")


def schedule_pending_menu(clf, scope_id: str, push_target: str, push_message_func, delay_sec: int = 3):
    token = clf.mark_pending_menu(scope_id)
    if not token:
        return

    def _worker():
        time.sleep(delay_sec)
        if clf.should_push_pending_menu(scope_id, token):
            push_message_func(push_target, clf.format_pending_menu(scope_id))
            clf.mark_menu_sent(scope_id, token)

    threading.Thread(target=_worker, daemon=True).start()


def download_line_content(msg_id: str, line_token: str, timeout: int = 30) -> bytes | None:
    url = f"https://api-data.line.me/v2/bot/message/{msg_id}/content"
    r = requests.get(url, headers={"Authorization": f"Bearer {line_token}"}, timeout=timeout)
    return r.content if r.status_code == 200 else None
