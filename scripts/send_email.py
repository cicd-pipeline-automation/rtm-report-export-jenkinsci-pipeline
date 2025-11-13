#!/usr/bin/env python3
# ==========================================================
# ✉ send_email.py
# Purpose: Send RTM report by SMTP to multiple recipients
#          (HTML body + HTML/PDF attachments)
# ==========================================================

import json
import os
import smtplib
import sys
import traceback
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List


def env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        print(f"[ERROR] Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(2)
    return value


def parse_recipients(raw: str) -> List[str]:
    if not raw:
        return []
    parts = [p.strip() for p in raw.replace(";", ",").split(",")]
    return [p for p in parts if p]


def load_execution_summary(json_path: str):
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def build_message(subject: str, sender: str, to_addrs: List[str], html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = sender
    msg["To"] = ", ".join(to_addrs)

    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def attach_file(msg: MIMEMultipart, path: str, filename: str = None):
    if not path or not os.path.exists(path):
        print(f"[WARN] Attachment missing or path not found: {path}")
        return
    filename = filename or os.path.basename(path)
    with open(path, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
    part["Content-Disposition"] = f'attachment; filename="{filename}"'
    msg.attach(part)
    print(f"[INFO] Attached file: {filename}")


def build_html_body(data: dict) -> str:
    project = data.get("projectKey", "")
    execution = data.get("executionKey", "")
    status = data.get("status", "UNKNOWN")
    summary = data.get("summary", "")
    fetched_at = data.get("fetchedAt", "")
    total_tc = len(data.get("testCases", []) or data.get("issues", []))

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; font-size: 13px;">
        <h2>RTM Test Execution Report</h2>
        <table cellpadding="4" cellspacing="0" border="0">
          <tr><td><b>Project:</b></td><td>{project}</td></tr>
          <tr><td><b>Execution:</b></td><td>{execution}</td></tr>
          <tr><td><b>Status:</b></td><td>{status}</td></tr>
          <tr><td><b>Summary:</b></td><td>{summary}</td></tr>
          <tr><td><b>Generated at:</b></td><td>{fetched_at}</td></tr>
          <tr><td><b>Total Test Cases:</b></td><td>{total_tc}</td></tr>
        </table>

        <p>
          Please find the attached HTML/PDF report for detailed test case results.
        </p>
        <p>
          Regards,<br/>
          RTM Automation Pipeline
        </p>
      </body>
    </html>
    """


def main():
    smtp_host = env("SMTP_HOST", required=True)
    smtp_port = int(env("SMTP_PORT", "587"))
    smtp_user = env("SMTP_USER", required=True)
    smtp_password = env("SMTP_PASSWORD", required=True)
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() not in ("false", "0", "no")

    sender = env("EMAIL_FROM", required=True)
    to_raw = env("EMAIL_TO", required=True)
    cc_raw = os.getenv("EMAIL_CC", "")
    bcc_raw = os.getenv("EMAIL_BCC", "")

    to_list = parse_recipients(to_raw)
    cc_list = parse_recipients(cc_raw)
    bcc_list = parse_recipients(bcc_raw)

    if not to_list:
        print("[ERROR] No valid recipients specified in EMAIL_TO.", file=sys.stderr)
        sys.exit(2)

    # Load execution summary for subject/body
    json_path = os.getenv("RTM_OUTPUT_JSON", "data/rtm_execution.json")
    data = load_execution_summary(json_path)

    project = data.get("projectKey", "")
    execution = data.get("executionKey", "")
    status = data.get("status", "UNKNOWN")

    subject = os.getenv(
        "EMAIL_SUBJECT",
        f"RTM Test Execution Report - {project}/{execution} [{status}]",
    )

    html_body = build_html_body(data)
    msg = build_message(subject, sender, to_list + cc_list, html_body)

    # Attach HTML + PDF
    html_report = os.getenv("RTM_REPORT_HTML", "report/rtm_execution.html")
    pdf_report = os.getenv("RTM_REPORT_PDF", "report/rtm_execution.pdf")

    attach_file(msg, html_report)
    attach_file(msg, pdf_report)

    all_recipients = list(dict.fromkeys(to_list + cc_list + bcc_list))  # dedupe

    print("=======================================================")
    print("[INFO] Sending email notification")
    print(f"[INFO]  SMTP Host : {smtp_host}:{smtp_port}")
    print(f"[INFO]  From      : {sender}")
    print(f"[INFO]  To        : {', '.join(to_list)}")
    if cc_list:
        print(f"[INFO]  Cc        : {', '.join(cc_list)}")
    if bcc_list:
        print(f"[INFO]  Bcc       : {', '.join(bcc_list)}")
    print("=======================================================")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            if smtp_use_tls:
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender, all_recipients, msg.as_string())
            print("[INFO] Email sent successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(6)

    sys.exit(0)


if __name__ == "__main__":
    main()
