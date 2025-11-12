#!/usr/bin/env python3
"""
====================================================================================
📘 Confluence Publisher – RTM Report Automation (Production-Ready)
------------------------------------------------------------------------------------
Uploads generated RTM HTML & PDF reports to a Confluence Cloud page.

✅ Creates page if missing
✅ Updates page content with version bump
✅ Attaches latest HTML/PDF reports (replace if exists)
✅ Safe for Jenkins CI/CD or standalone use
✅ Handles transient network or API errors

Author  : DevOpsUser8413
Version : 1.1.0
====================================================================================
"""

import os
import sys
import json
import time
import requests
import traceback
from pathlib import Path
from datetime import datetime

# ------------------------------------------------------------------------------
# 🌍 Environment Variables (Injected by Jenkins)
# ------------------------------------------------------------------------------
CONFLUENCE_BASE   = os.getenv("CONFLUENCE_BASE")
CONFLUENCE_USER   = os.getenv("CONFLUENCE_USER")
CONFLUENCE_TOKEN  = os.getenv("CONFLUENCE_TOKEN")
CONFLUENCE_SPACE  = os.getenv("CONFLUENCE_SPACE", "DEMO")
CONFLUENCE_TITLE  = os.getenv("CONFLUENCE_TITLE", "RTM Test Execution Report")

HTML_FILE = Path("report/rtm_report.html")
PDF_FILE  = Path("report/rtm_report.pdf")
LOG_FILE  = Path("report/confluence_publish_log.txt")

# ------------------------------------------------------------------------------
# 🧾 Logging Utility
# ------------------------------------------------------------------------------
def log(message: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{level}] {ts} | {message}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp1252", errors="replace").decode("cp1252"))
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ------------------------------------------------------------------------------
# 🧱 Validation
# ------------------------------------------------------------------------------
if not all([CONFLUENCE_BASE, CONFLUENCE_USER, CONFLUENCE_TOKEN]):
    log("Missing Confluence credentials or base URL.", "ERROR")
    sys.exit(1)

if not HTML_FILE.exists() or not PDF_FILE.exists():
    log("Missing report files. Expected rtm_report.html and rtm_report.pdf.", "ERROR")
    sys.exit(2)

# ------------------------------------------------------------------------------
# 🔐 Authentication Setup
# ------------------------------------------------------------------------------
auth = (CONFLUENCE_USER, CONFLUENCE_TOKEN)
common_headers = {"Content-Type": "application/json"}

# ------------------------------------------------------------------------------
# 🧰 HTTP Request Helper with Retry
# ------------------------------------------------------------------------------
def safe_request(method: str, url: str, **kwargs):
    for attempt in range(1, 4):
        try:
            resp = requests.request(method, url, auth=auth, timeout=30, **kwargs)
            if resp.status_code in [200, 201]:
                return resp
            log(f"⚠️ Attempt {attempt} failed ({resp.status_code}): {resp.text[:200]}")
        except requests.RequestException as e:
            log(f"⚠️ Attempt {attempt} request error: {e}", "WARN")
        if attempt < 3:
            time.sleep(3)
    log(f"❌ All attempts failed for {url}", "ERROR")
    sys.exit(99)

# ------------------------------------------------------------------------------
# 🔍 Find Existing Page
# ------------------------------------------------------------------------------
def find_page():
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    params = {"title": CONFLUENCE_TITLE, "spaceKey": CONFLUENCE_SPACE, "expand": "version"}
    resp = safe_request("GET", url, params=params)
    results = resp.json().get("results", [])
    return results[0] if results else None

# ------------------------------------------------------------------------------
# 📝 Create or Update Page
# ------------------------------------------------------------------------------
def create_or_update_page(existing_page: dict):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    payload = {
        "type": "page",
        "title": CONFLUENCE_TITLE,
        "space": {"key": CONFLUENCE_SPACE},
        "body": {"storage": {"value": html_content, "representation": "storage"}},
    }

    if not existing_page:
        log(f"Creating new Confluence page '{CONFLUENCE_TITLE}' in space '{CONFLUENCE_SPACE}'...")
        url = f"{CONFLUENCE_BASE}/rest/api/content"
        resp = safe_request("POST", url, headers=common_headers, json=payload)
        log("✅ Page created successfully.")
        return resp.json()
    else:
        page_id = existing_page["id"]
        version = existing_page.get("version", {}).get("number", 1) + 1
        payload["version"] = {"number": version}
        log(f"Updating Confluence page '{CONFLUENCE_TITLE}' → version {version}...")
        url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}"
        resp = safe_request("PUT", url, headers=common_headers, json=payload)
        log("✅ Page updated successfully.")
        return resp.json()

# ------------------------------------------------------------------------------
# 📎 Upload Attachments
# ------------------------------------------------------------------------------
def upload_attachment(page_id: str, file_path: Path):
    upload_url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}/child/attachment"
    headers = {"X-Atlassian-Token": "no-check"}
    file_name = file_path.name

    log(f"Attaching '{file_name}' to page ID {page_id}...")

    # check if attachment already exists
    resp = safe_request("GET", upload_url)
    attachments = resp.json().get("results", [])
    existing = next((a for a in attachments if a["title"] == file_name), None)

    with open(file_path, "rb") as f:
        files = {"file": (file_name, f, "application/octet-stream")}
        if existing:
            attach_id = existing["id"]
            log(f"Updating existing attachment: {file_name}")
            url = f"{upload_url}/{attach_id}/data"
        else:
            log(f"Uploading new attachment: {file_name}")
            url = upload_url
        resp = safe_request("POST", url, headers=headers, files=files)

    if resp.status_code in [200, 201]:
        log(f"✅ Attachment '{file_name}' uploaded successfully.")
    else:
        log(f"❌ Failed to upload '{file_name}': {resp.status_code}", "ERROR")
        sys.exit(6)

# ------------------------------------------------------------------------------
# 🏁 Main Execution
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("🌐 Starting Confluence Publishing Process")
    print("=" * 70)
    try:
        page = find_page()
        page_data = create_or_update_page(page)
        page_id = page_data["id"]

        upload_attachment(page_id, HTML_FILE)
        upload_attachment(page_id, PDF_FILE)

        confluence_url = f"{CONFLUENCE_BASE}/pages/{page_id}"
        log(f"✅ Confluence publishing completed successfully → {confluence_url}")
        print(f"[SUCCESS] Report published at: {confluence_url}")
        sys.exit(0)
    except Exception as e:
        log(f"❌ Unexpected failure: {e}", "ERROR")
        traceback.print_exc()
        sys.exit(99)
