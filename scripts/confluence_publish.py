#!/usr/bin/env python3
# ==========================================================
# 📰 confluence_publish.py
# Purpose: Publish RTM HTML report to Confluence (create or update page)
# ==========================================================

import json
import os
import sys
from urllib.parse import quote

import requests


def env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        print(f"[ERROR] Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(2)
    return value


def load_html(path):
    if not os.path.exists(path):
        print(f"[ERROR] HTML report not found: {path}", file=sys.stderr)
        sys.exit(4)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_existing_page_id(base_url, space_key, title, auth, verify_ssl):
    url = f"{base_url}/rest/api/content?spaceKey={quote(space_key)}&title={quote(title)}&expand=version"
    resp = requests.get(url, auth=auth, verify=verify_ssl)
    if resp.status_code != 200:
        print(f"[WARN] Failed to search for existing Confluence page (HTTP {resp.status_code})")
        return None, None

    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None, None

    page = results[0]
    return page.get("id"), page.get("version", {}).get("number")


def create_page(base_url, space_key, title, parent_id, html, auth, verify_ssl):
    url = f"{base_url}/rest/api/content"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": html,
                "representation": "storage",
            }
        },
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]

    resp = requests.post(
        url,
        auth=auth,
        json=payload,
        headers={"Content-Type": "application/json"},
        verify=verify_ssl,
    )
    if not (200 <= resp.status_code < 300):
        print(f"[ERROR] Failed to create Confluence page (HTTP {resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(5)

    data = resp.json()
    print(f"[INFO] Created Confluence page: {data.get('id')}")
    return data.get("id")


def update_page(base_url, page_id, current_version, title, html, auth, verify_ssl):
    url = f"{base_url}/rest/api/content/{page_id}"
    new_version = (current_version or 0) + 1
    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": new_version},
        "body": {
            "storage": {
                "value": html,
                "representation": "storage",
            }
        },
    }
    resp = requests.put(
        url,
        auth=auth,
        json=payload,
        headers={"Content-Type": "application/json"},
        verify=verify_ssl,
    )
    if not (200 <= resp.status_code < 300):
        print(f"[ERROR] Failed to update Confluence page (HTTP {resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(5)

    data = resp.json()
    print(f"[INFO] Updated Confluence page: {data.get('id')} (version {new_version})")
    return data.get("id")


def main():
    base_url = env("CONFLUENCE_BASE_URL", required=True).rstrip("/")
    user = env("CONFLUENCE_USER", required=True)
    token = env("CONFLUENCE_TOKEN", required=True)
    space = env("CONFLUENCE_SPACE", required=True)
    title = env("CONFLUENCE_TITLE", "RTM Test Execution Report")
    parent_id = env("CONFLUENCE_PARENT_ID", "")
    html_path = env("RTM_REPORT_HTML") or "report/rtm_execution.html"
    verify_ssl = os.getenv("CONFLUENCE_VERIFY_SSL", "true").lower() not in ("false", "0", "no")

    auth = (user, token)
    html = load_html(html_path)

    print("=======================================================")
    print("[INFO] Publishing report to Confluence")
    print(f"[INFO]  Base URL : {base_url}")
    print(f"[INFO]  Space    : {space}")
    print(f"[INFO]  Title    : {title}")
    print("=======================================================")

    page_id, current_version = get_existing_page_id(base_url, space, title, auth, verify_ssl)

    if page_id:
        print(f"[INFO] Existing page found: {page_id} (version={current_version}) – updating.")
        update_page(base_url, page_id, current_version, title, html, auth, verify_ssl)
    else:
        print("[INFO] No existing page found – creating new page.")
        create_page(base_url, space, title, parent_id, html, auth, verify_ssl)

    print("[INFO] Confluence publish completed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
