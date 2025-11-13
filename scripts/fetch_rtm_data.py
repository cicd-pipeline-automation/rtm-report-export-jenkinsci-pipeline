#!/usr/bin/env python3
# ==========================================================
# 📘 fetch_rtm_data.py  (RTM Cloud V2 API)
# Purpose: Fetch Test Execution results from RTM Cloud REST API
# Endpoint: GET /api/v2/test-execution/{testKey}
# ==========================================================

import json
import os
import sys
from datetime import datetime

import requests


def env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        print(f"[ERROR] Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(2)
    return value


def normalize_status(raw_status):
    """Support dict or plain string status."""
    if isinstance(raw_status, dict):
        return raw_status.get("name") or raw_status.get("status") or str(raw_status)
    if raw_status is None:
        return "UNKNOWN"
    return str(raw_status)


def extract_test_cases(raw: dict):
    """
    Try to find test case executions array in various fields commonly used by RTM-like APIs.
    Returns a list of normalized test case dictionaries.
    """
    candidate_keys = [
        "testCaseExecutions",
        "testCaseExecutionList",
        "tces",
        "testCases",
        "issues",
        "results",
    ]

    tces = []
    for key in candidate_keys:
        value = raw.get(key)
        if isinstance(value, list):
            tces = value
            print(f"[INFO] Using test case executions from '{key}' (count={len(tces)})")
            break

    normalized = []
    for item in tces:
        status = item.get("status")
        status_name = normalize_status(status)

        normalized.append(
            {
                "key": item.get("key")
                or item.get("testCaseKey")
                or item.get("testCaseId")
                or item.get("id"),
                "name": item.get("summary")
                or item.get("name")
                or item.get("title")
                or "",
                "status": status_name,
                "executedBy": item.get("executedBy")
                or item.get("assignee")
                or item.get("tester"),
                "executedOn": item.get("executedOn")
                or item.get("executionDate")
                or item.get("updated"),
                "defects": item.get("defects") or item.get("bugs") or [],
                "comment": item.get("comment") or item.get("comments") or "",
                "raw": item,
            }
        )

    return normalized


def main():
    base_url = env("RTM_BASE_URL", required=True).rstrip("/")
    project_key = env("RTM_PROJECT_KEY", required=True)
    execution_key = (
        env("RTM_EXECUTION_KEY")
        or env("JIRA_EXECUTION_ID")
        or env("TEST_EXECUTION_KEY")
    )
    if not execution_key:
        print("[ERROR] Missing RTM_EXECUTION_KEY / JIRA_EXECUTION_ID / TEST_EXECUTION_KEY", file=sys.stderr)
        sys.exit(2)

    user = env("RTM_USER") or env("JIRA_USER", required=True)
    token = env("RTM_TOKEN") or env("JIRA_TOKEN", required=True)

    output_file = env("RTM_OUTPUT_JSON", "data/rtm_execution.json")
    verify_ssl = env("RTM_VERIFY_SSL", "true").lower() not in ("false", "0", "no")

    url = f"{base_url}/api/v2/test-execution/{execution_key}"

    print("==========================================================")
    print(f"[INFO] RTM V2 API – Fetching Test Execution")
    print(f"[INFO]  Base URL     : {base_url}")
    print(f"[INFO]  Project Key  : {project_key}")
    print(f"[INFO]  Execution Key: {execution_key}")
    print(f"[INFO]  Endpoint     : {url}")
    print("==========================================================")

    try:
        resp = requests.get(
            url,
            headers={"Accept": "application/json"},
            auth=(user, token),
            timeout=30,
            verify=verify_ssl,
        )
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network/connection error while calling RTM API: {e}", file=sys.stderr)
        sys.exit(3)

    if not (200 <= resp.status_code < 300):
        print(
            f"[ERROR] RTM API responded with HTTP {resp.status_code}:\n{resp.text}",
            file=sys.stderr,
        )
        sys.exit(3)

    try:
        raw = resp.json()
    except ValueError as e:
        print(f"[ERROR] Failed to decode RTM API JSON: {e}", file=sys.stderr)
        sys.exit(3)

    test_cases = extract_test_cases(raw)
    overall_status = normalize_status(raw.get("status"))
    summary = raw.get("summary") or raw.get("name") or raw.get("description") or ""

    data_to_save = {
        "fetchedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "projectKey": project_key,
        "executionKey": execution_key,
        "summary": summary,
        "status": overall_status,
        "testCases": test_cases,
        "raw": raw,
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Data saved successfully to {output_file}")
    print(f"[INFO] Test cases fetched: {len(test_cases)}")
    print("[INFO] fetch_rtm_data.py completed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
