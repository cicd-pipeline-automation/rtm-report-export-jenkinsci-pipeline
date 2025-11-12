#!/usr/bin/env python3
"""
====================================================================================
📧 Email Notification – RTM Report Automation (Production-Ready)
------------------------------------------------------------------------------------
Sends RTM HTML & PDF reports via SMTP to stakeholders.

✅ Secure SMTP authentication (App Passwords / Jenkins credentials)
✅ MIME multipart email (HTML + PDF attachments)
✅ Includes Confluence page link
✅ Works seamlessly on Jenkins Windows/Linux agents
✅ Retries transient SMTP errors and logs all activity

Author  : DevOpsUser8413
Version : 1.1.0
====================================================================================
"""

import os
import sys
import smtplib
import traceback
from time import sleep
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# 🌍 Environment Variables (Injected by Jenkins)
# ---------------------------------------------------------------------------
SMTP_HOST       = os.getenv("SMTP_HOST")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER       = os.getenv("SMTP_USER")
SMTP_PASS       = os.getenv("SMTP_PASS")
REPORT_FROM     = os.getenv("REPORT_FROM", SMTP_USER)
REPORT_TO       = os.getenv("REPORT_TO", "")       # Comma-separated list
REPORT_CC       = os.getenv("REPORT_CC", "")       # Optional CC list
REPORT_BCC      = os.getenv("REPORT_BCC", "")      # Optional BCC list
CONFLUENCE_LINK = os.getenv("CONFLUENCE_LINK", "https://confluence.yourorg.com/display/RTM/RTM+Test+Execution+Report")

HTML_REPORT = Path("report/rtm_report.html")
PDF_REPORT  = Path("report/rtm_report.pdf")
LOG_FILE    = Path("report/email_notification_log.txt")

# ---------------------------------------------------------------------------
# 🧾 Logging Utility
# ---------------------------------------------------------------------------
def log(message: str, level: str = "INFO") -> None:
    """Prints and writes log messages with timestamps."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{level}] {ts} | {message}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp1252", errors="replace").decode("cp1252"))
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ---------------------------------------------------------------------------
# 🧩 Validation
# ---------------------------------------------------------------------------
if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, REPORT_TO]):
    log("Missing SMTP configuration or recipient list.", "ERROR")
    sys.exit(1)

if not HTML_REPORT.exists() or not PDF_REPORT.exists():
    log("Missing report files. Expected rtm_report.html and rtm_report.pdf.", "ERROR")
    sys.exit(2)

def parse_recipients(value: str):
    return [r.strip() for r in value.split(",") if r.strip()]

to_list  = parse_recipients(REPORT_TO)
cc_list  = parse_recipients(REPORT_CC)
bcc_list = parse_recipients(REPORT_BCC)
all_recipients = list({*to_list, *cc_list, *bcc_list})

if not to_list:
    log("Recipient TO list is empty.", "ERROR")
    sys.exit(3)

# ---------------------------------------------------------------------------
# 📨 Compose Email
# ---------------------------------------------------------------------------
def build_email() -> MIMEMultipart:
    """Builds a MIME multipart email with HTML + PDF attachments."""
    log("Composing RTM report email...")

    subject = f"RTM Test Execution Report – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    msg = MIMEMultipart("mixed")
    msg["From"] = REPORT_FROM
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = subject

    # HTML Body
    html_body = f"""
    <html>
    <body style="font-family:Arial, sans-serif; font-size:14px; color:#333;">
        <p>Dear Team,</p>
        <p>Please find attached the latest <b>RTM Test Execution Report</b>.</p>
        <p>You can also view it on Confluence:<br>
           🔗 <a href="{CONFLUENCE_LINK}" target="_blank">{CONFLUENCE_LINK}</a></p>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Regards,<br><b>DevOps CI/CD Automation</b></p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach HTML Report
    with open(HTML_REPORT, "rb") as f:
        html_part = MIMEApplication(f.read(), _subtype="html")
        html_part.add_header("Content-Disposition", "attachment", filename=HTML_REPORT.name)
        msg.attach(html_part)

    # Attach PDF Report
    with open(PDF_REPORT, "rb") as f:
        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
        pdf_part.add_header("Content-Disposition", "attachment", filename=PDF_REPORT.name)
        msg.attach(pdf_part)

    log(f"Email composed successfully → Subject: {subject}")
    return msg

# ---------------------------------------------------------------------------
# 📬 Send Email with retry
# ---------------------------------------------------------------------------
def send_email(msg: MIMEMultipart, retries: int = 3, delay_sec: int = 5) -> None:
    """Send email via SMTP with retry for transient errors."""
    for attempt in range(1, retries + 1):
        try:
            log(f"Attempt {attempt}: Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT} as {SMTP_USER}...")
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(REPORT_FROM, all_recipients, msg.as_string())
            log(f"✅ Email sent successfully to {len(all_recipients)} recipients.")
            return
        except smtplib.SMTPException as e:
            log(f"⚠️  SMTP error on attempt {attempt}: {e}", "WARN")
            if attempt < retries:
                sleep(delay_sec)
                continue
            else:
                log("❌ All retry attempts failed. Aborting email send.", "ERROR")
                traceback.print_exc()
                sys.exit(4)
        except Exception as e:
            log(f"❌ Unexpected error on attempt {attempt}: {e}", "ERROR")
            traceback.print_exc()
            if attempt < retries:
                sleep(delay_sec)
            else:
                sys.exit(5)

# ---------------------------------------------------------------------------
# 🏁 Main Entry
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("📧 Starting RTM Email Notification Process")
    print("=" * 70)

    try:
        message = build_email()
        send_email(message)
        log("Email notification process completed successfully.")
        sys.exit(0)
    except Exception as e:
        log(f"Unhandled exception: {e}", "ERROR")
        traceback.print_exc()
        sys.exit(99)
