"""
Common runtime helpers for new agent system.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


BASE_DIR = Path(os.getenv("AMWAY_AGENT_BASE_DIR", r"C:\Users\user\claude AI_Agent"))
LOGS_DIR = BASE_DIR / "logs"


def load_json_config(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def run_codex_cli(prompt: str, timeout: int = 60) -> str:
    response_path = None
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt",
            delete=False, dir=str(LOGS_DIR)
        ) as f:
            response_path = f.name

        result = subprocess.run(
            ["cmd", "/c", "codex", "exec",
             "--skip-git-repo-check", "--sandbox", "read-only",
             "--color", "never", "-C", str(BASE_DIR),
             "-o", response_path, "-"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "codex CLI 回傳非零")

        out = ""
        if response_path and os.path.exists(response_path):
            with open(response_path, "r", encoding="utf-8") as f:
                out = f.read().strip()
        if not out:
            out = result.stdout.strip()
        if out:
            return out
        raise RuntimeError("codex CLI 未回傳內容")
    finally:
        if response_path and os.path.exists(response_path):
            try:
                os.unlink(response_path)
            except Exception:
                pass


def push_line_message(line_token: str, line_user: str, line_push_url: str, message: str) -> int | None:
    if not line_token or not line_user:
        return None
    import requests

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {line_token}"}
    chunks = [message[i:i + 4900] for i in range(0, len(message), 4900)]
    payload = {"to": line_user, "messages": [{"type": "text", "text": c} for c in chunks[:5]]}
    resp = requests.post(line_push_url, headers=headers, json=payload, timeout=10)
    return resp.status_code
