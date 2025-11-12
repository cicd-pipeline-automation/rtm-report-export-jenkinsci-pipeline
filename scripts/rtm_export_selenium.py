#!/usr/bin/env python3
"""
RTM Test Execution Report Export Automation
-------------------------------------------
Logs into Jira Cloud (with RTM plugin), navigates to the Test Execution report,
exports it as PDF, and saves it under /report folder for Jenkins CI/CD pipelines.

Supports:
- Atlassian Cloud login (new unified login pages)
- SSO redirects (captures screenshot and exits gracefully)
- Headless Chrome in Jenkins on Windows or Linux
"""

import os
import sys
import time
import pathlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ------------------------------------------------------------------------------
# Environment Variables (provided by Jenkins)
# ------------------------------------------------------------------------------
JIRA_USER = os.getenv("JIRA_USER")
JIRA_PASS = os.getenv("JIRA_PASS")
JIRA_BASE = os.getenv("JIRA_BASE", "https://yourdomain.atlassian.net")
PROJECT_KEY = os.getenv("RTM_PROJECT")
TEST_EXEC = os.getenv("TEST_EXECUTION")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "report")

# ------------------------------------------------------------------------------
# Directory Setup
# ------------------------------------------------------------------------------
outdir = pathlib.Path(DOWNLOAD_DIR)
outdir.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Configure Chrome (headless mode for Jenkins)
# ------------------------------------------------------------------------------
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--ignore-certificate-errors")

# ✅ Optional: uncomment this if your Jira uses SSO (reuses logged-in Chrome profile)
# options.add_argument(r"user-data-dir=C:\Users\<YOUR_WINDOWS_USERNAME>\AppData\Local\Google\Chrome\User Data")

prefs = {
    "download.default_directory": str(outdir.resolve()),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

try:
    # --------------------------------------------------------------------------
    # Jira Login
    # --------------------------------------------------------------------------
    print(f"[INFO] Logging into Jira: {JIRA_BASE}")
    driver.get(JIRA_BASE)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    if "Atlassian" in driver.title or "Login" in driver.title:
        print("[INFO] Atlassian login page detected.")
        try:
            # Try username input (fallback between ID and NAME)
            try:
                username_box = wait.until(EC.presence_of_element_located((By.ID, "username")))
            except:
                username_box = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_box.clear()
            username_box.send_keys(JIRA_USER)
            print("[INFO] Username entered.")

            # Click Next / Continue
            try:
                driver.find_element(By.ID, "login-submit").click()
            except:
                try:
                    driver.find_element(By.XPATH, "//button[contains(.,'Continue')]").click()
                except:
                    print("[WARN] Continue/Next button not found; proceeding...")

            # Wait for password
            print("[INFO] Waiting for password field...")
            try:
                password_box = wait.until(EC.presence_of_element_located((By.ID, "password")))
            except:
                password_box = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_box.clear()
            password_box.send_keys(JIRA_PASS)
            print("[INFO] Password entered.")

            # Click Login
            try:
                driver.find_element(By.ID, "login-submit").click()
            except:
                try:
                    driver.find_element(By.XPATH, "//button[contains(.,'Log in')]").click()
                except:
                    print("[WARN] Login button not found; continuing...")

            print("[INFO] Login submitted. Waiting for redirect...")
            time.sleep(8)

        except Exception as e:
            print(f"[WARN] Could not locate login fields or redirected to SSO: {e}")
            driver.save_screenshot(str(outdir / "sso_redirect.png"))
            print("[WARN] If using SSO, configure Chrome to reuse profile via user-data-dir.")
            raise

    elif "Dashboard" in driver.title or "Projects" in driver.title:
        print("[INFO] Already logged into Jira (session active).")

    else:
        print(f"[WARN] Unexpected login title: {driver.title}")
        driver.save_screenshot(str(outdir / "unexpected_login.png"))

    # --------------------------------------------------------------------------
    # Navigate to RTM Test Execution Report
    # --------------------------------------------------------------------------
    rtm_url = f"{JIRA_BASE}/jira/apps/rtm/reports/test-execution"
    print(f"[INFO] Navigating to RTM Test Execution Report: {rtm_url}")
    driver.get(rtm_url)
    time.sleep(8)

    # Fill project and execution key
    driver.find_element(By.XPATH, "//input[@placeholder='Project key']").send_keys(PROJECT_KEY)
    driver.find_element(By.XPATH, "//input[@placeholder='Execution key']").send_keys(TEST_EXEC)
    time.sleep(1)

    # Generate report
    print("[INFO] Generating RTM report...")
    driver.find_element(By.XPATH, "//button[contains(.,'Generate')]").click()
    time.sleep(10)

    # --------------------------------------------------------------------------
    # Export to PDF
    # --------------------------------------------------------------------------
    print("[INFO] Exporting report as PDF...")
    driver.find_element(By.XPATH, "//button[contains(.,'Export')]").click()
    time.sleep(2)
    driver.find_element(By.XPATH, "//span[text()='PDF']").click()
    time.sleep(20)

    # --------------------------------------------------------------------------
    # Verify Download
    # --------------------------------------------------------------------------
    print(f"[INFO] Checking for downloaded files in '{DOWNLOAD_DIR}'")
    found = False
    for f in outdir.glob("*.pdf"):
        print(f"[OK] Found downloaded report: {f}")
        found = True
        break

    if not found:
        print("[ERROR] No PDF file detected after export.")
        driver.save_screenshot(str(outdir / "export_failed.png"))
        sys.exit(2)

    print("[SUCCESS] RTM Test Execution Report exported successfully.")
    sys.exit(0)

except Exception as e:
    print(f"[ERROR] Unexpected error occurred: {e}")
    driver.save_screenshot(str(outdir / "fatal_error.png"))
    sys.exit(1)

finally:
    driver.quit()
