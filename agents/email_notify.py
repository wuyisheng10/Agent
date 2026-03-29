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
    if not ENABLED:
        print("[EMAIL] Email notifications are disabled.")
        return False

    if not all([SENDER, PASSWORD, RECEIVER]):
        print("[EMAIL] Missing email credentials in .env")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SENDER
        msg["To"]      = RECEIVER

        # Plain text version
        text_part = MIMEText(body, "plain", "utf-8")

        # HTML version
        html_body = body.replace("\n", "<br>")
        html_part = MIMEText(
            f"""
            <html><body>
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;border:1px solid #ddd;border-radius:8px;">
              <h2 style="color:#2c3e50;">Amway AI Agent Notification</h2>
              <div style="background:#f9f9f9;padding:15px;border-radius:5px;line-height:1.8;">
                {html_body}
              </div>
              <p style="color:#999;font-size:12px;margin-top:20px;">
                Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
              </p>
            </div>
            </body></html>
            """,
            "html",
            "utf-8"
        )

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, PASSWORD)
            server.sendmail(SENDER, RECEIVER, msg.as_string())

        print(f"[EMAIL] Sent successfully to {RECEIVER}")
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

    subject = f"[Amway AI] Daily Pipeline - {status_icon} - {datetime.now().strftime('%Y/%m/%d')}"
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

    subject = f"[Amway AI] Weekly Report Done - {datetime.now().strftime('%Y/%m/%d')}"
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
    subject = f"[Amway AI] ERROR in {agent_name} - {datetime.now().strftime('%Y/%m/%d %H:%M')}"
    return send_email(subject, "\n".join(lines))


# Quick test
if __name__ == "__main__":
    print("Testing email notification...")
    ok = send_email(
        subject="[Amway AI] Test Email",
        body=f"This is a test notification.\nSent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print("Test result:", "SUCCESS" if ok else "FAILED")
