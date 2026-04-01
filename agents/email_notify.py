"""
Email Notification Module
File: C:/Users/user/claude AI_Agent/agents/email_notify.py
Description: Send Gmail notifications after each agent run
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

SENDER   = os.getenv("EMAIL_SENDER", "")
PASSWORD = os.getenv("EMAIL_PASSWORD", "")
RECEIVER = os.getenv("EMAIL_RECEIVER", "")
ENABLED  = os.getenv("EMAIL_ENABLED", "false").lower() == "true"


def send_email(subject: str, body: str) -> bool:
    """
    Send an email notification via Gmail SMTP.
    Returns True on success, False on failure.
    """
    return send_email_to(subject, body, [RECEIVER])


def send_email_to(subject: str, body: str, receivers: list) -> bool:
    """
    Send an email to one or more recipients.
    body may be plain text or a full HTML string.
    Returns True on success, False on failure.
    """
    if not ENABLED:
        print("[EMAIL] Email notifications are disabled.")
        return False

    if not all([SENDER, PASSWORD]):
        print("[EMAIL] Missing email credentials in .env")
        return False

    targets = [r for r in receivers if r]
    if not targets:
        print("[EMAIL] No recipients specified.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SENDER
        msg["To"]      = ", ".join(targets)

        # Plain text version (strip tags for fallback)
        import re as _re
        plain = _re.sub(r"<[^>]+>", "", body)
        text_part = MIMEText(plain, "plain", "utf-8")

        # HTML version — if body already contains <html>, use as-is; else wrap
        if body.lstrip().lower().startswith("<html"):
            html_content = body
        else:
            html_body = body.replace("\n", "<br>")
            html_content = f"""
            <html><body>
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;border:1px solid #ddd;border-radius:8px;">
              <h2 style="color:#2c3e50;">Yisheng AI Notification</h2>
              <div style="background:#f9f9f9;padding:15px;border-radius:5px;line-height:1.8;">
                {html_body}
              </div>
              <p style="color:#999;font-size:12px;margin-top:20px;">
                Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
              </p>
            </div>
            </body></html>
            """
        html_part = MIMEText(html_content, "html", "utf-8")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, PASSWORD)
            server.sendmail(SENDER, targets, msg.as_string())

        print(f"[EMAIL] Sent successfully to {', '.join(targets)}")
        return True

    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False


def notify_pipeline_done(results: list, summary_path: str = "") -> bool:
    """Send notification after daily pipeline completes."""
    lines = []
    all_ok = all(r.get("status") == "success" for r in results)
    status_icon = "SUCCESS" if all_ok else "PARTIAL FAILURE"

    lines.append(f"[{status_icon}] Daily Pipeline Report")
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("Step Results:")
    for r in results:
        icon = "OK" if r.get("status") == "success" else "FAIL"
        lines.append(f"  [{icon}] {r.get('step', '')} - {r.get('status', '')}")
    if summary_path:
        lines.append("")
        lines.append(f"Summary saved to: {summary_path}")

    subject = f"[Yisheng AI] Daily Pipeline - {status_icon} - {datetime.now().strftime('%Y/%m/%d')}"
    return send_email(subject, "\n".join(lines))


def notify_crew_done(result_path: str = "") -> bool:
    """Send notification after weekly CrewAI report completes."""
    lines = [
        "[SUCCESS] Weekly CrewAI Report Completed",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "The multi-agent weekly analysis has finished.",
    ]
    if result_path:
        lines.append(f"Report saved to: {result_path}")

    subject = f"[Yisheng AI] Weekly Report Done - {datetime.now().strftime('%Y/%m/%d')}"
    return send_email(subject, "\n".join(lines))


def notify_error(agent_name: str, error_msg: str) -> bool:
    """Send error notification when an agent fails."""
    lines = [
        f"[ERROR] Agent Failed: {agent_name}",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Error Details:",
        error_msg[:500],
    ]
    subject = f"[Yisheng AI] ERROR in {agent_name} - {datetime.now().strftime('%Y/%m/%d %H:%M')}"
    return send_email(subject, "\n".join(lines))


# Quick test
if __name__ == "__main__":
    print("Testing email notification...")
    ok = send_email(
        subject="[Yisheng AI] Test Email",
        body=f"This is a test notification.\nSent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print("Test result:", "SUCCESS" if ok else "FAILED")
