#!/usr/bin/env python3
"""
RTM Test Execution Report Export Automation
-------------------------------------------
Logs into Jira Cloud (with RTM plugin), navigates to the Test Execution report,
exports it as PDF, and saves it under /report folder for Jenkins CI/CD pipelines.

Supports:
- Atlassian Cloud login (new unified login pages)
- SSO redirects (captures screenshot and exits gracefully)
- Headless Chrome stability for Jenkins Windows/Linux
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
# Configure Chrome (robust Jenkins headless mode)
# ------------------------------------------------------------------------------
options = Options()

# ✅ Classic headless mode is more stable in Windows Jenkins services
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-extensions")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-notifications")
options.add_argument("--ignore-certificate-errors")

# ✅ Optional: reuse Chrome profile if Jira uses SSO
# Make sure Jenkins runs under your Windows account or that this path is accessible
options.add_argument(
    r"user-data-dir=C:\Users\I17270834\AppData\Local\Google\Chrome\User Data"
)

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
            # --- Username field (fallbacks for old/new pages) ---
            try:
                username_box = wait.until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
            except:
                username_box = wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
            username_box.clear()
            username_box.send_keys(JIRA_USER)
            print("[INFO] Username entered.")

            # --- Click Continue ---
            try:
                driver.find_element(By.ID, "login-submit").click()
            except:
                try:
                    driver.find_element(By.XPATH, "//button[contains(.,'Continue')]").click()
                except:
                    print("[WARN] Continue button not found; proceeding...")

            print("[INFO] Waiting for password field...")
            time.sleep(3)

            # --- Password field ---
            try:
                password_box = wait.until(
                    EC.element_to_be_clickable((By.ID, "password"))
                )
            except:
                password_box = wait.until(
                    EC.element_to_be_clickable((By.NAME, "password"))
                )
            password_box.clear()
            password_box.send_keys(JIRA_PASS)
            print("[INFO] Password entered.")

            # --- Click Login ---
            try:
                driver.find_element(By.ID, "login-submit").click()
            except:
                try:
                    driver.find_element(By.XPATH, "//button[contains(.,'Log in')]").click()
                except:
                    print("[WARN] Login button not found; continuing...")

            print("[INFO] Login submitted. Waiting for redirect...")
            time.sleep(10)

        except Exception as e:
            print(f"[WARN] Could not locate login fields or redirected to SSO: {e}")
            driver.save_screenshot(str(outdir / "sso_redirect.png"))
            print("[WARN] If using SSO, Chrome profile reuse via user-data-dir is required.")
            raise

    elif "Dashboard" in driver.title or "Projects" in driver.title:
        print("[INFO] Already logged into Jira (session active).")
    else:
        print(f"[WARN] Unexpected login page: {driver.title}")
        driver.save_screenshot(str(outdir / "unexpected_login.png"))

    # --------------------------------------------------------------------------
    # Navigate to RTM Test Execution Report
    # --------------------------------------------------------------------------
    rtm_url = f"{JIRA_BASE}/jira/apps/rtm/reports/test-execution"
    print(f"[INFO] Navigating to RTM Test Execution Report: {rtm_url}")
    driver.get(rtm_url)
    time.sleep(10)

    # --- Fill project and execution key ---
    driver.find_element(By.XPATH, "//input[@placeholder='Project key']").send_keys(PROJECT_KEY)
    driver.find_element(By.XPATH, "//input[@placeholder='Execution key']").send_keys(TEST_EXEC)
    time.sleep(2)

    # --- Generate report ---
    print("[INFO] Generating RTM report...")
    driver.find_element(By.XPATH, "//button[contains(.,'Generate')]").click()
    time.sleep(10)

    # --------------------------------------------------------------------------
    # Export to PDF
    # --------------------------------------------------------------------------
    print("[INFO] Exporting report as PDF...")
    driver.find_element(By.XPATH, "//button[contains(.,'Export')]").click()
    time.sleep(3)
    driver.find_element(By.XPATH, "//span[text()='PDF']").click()
    print("[INFO] Waiting for download to complete...")
    time.sleep(25)

    # --------------------------------------------------------------------------
    # Verify Download
    # --------------------------------------------------------------------------
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
