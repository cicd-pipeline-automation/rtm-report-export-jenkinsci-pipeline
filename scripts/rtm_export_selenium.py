#!/usr/bin/env python3
"""
RTM Test Execution Report Export Automation (Stable Jenkins Edition)
--------------------------------------------------------------------
This script logs into Jira Cloud (with RTM plugin), navigates to the Test
Execution report, exports it as PDF, and saves it under /report folder.

Compatible with:
  - Jenkins running on Windows using 'java -jar jenkins.war'
  - Chrome installed system-wide (Program Files or Program Files (x86))
  - Headless Chrome execution

Author: DevOps Automation (RTM Report Export)
"""

import os
import sys
import time
import pathlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
# Detect Chrome installation path
# ------------------------------------------------------------------------------
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    rf"C:\Users\{os.getenv('USERNAME')}\AppData\Local\Google\Chrome\Application\chrome.exe",
]

chrome_binary = None
for path in CHROME_PATHS:
    if os.path.exists(path):
        chrome_binary = path
        break

if not chrome_binary:
    print("[ERROR] Google Chrome not found. Please install Chrome or update path.")
    sys.exit(1)

print(f"[INFO] Chrome detected at: {chrome_binary}")

# ------------------------------------------------------------------------------
# Configure Chrome Options (Headless mode for Jenkins)
# ------------------------------------------------------------------------------
options = Options()
options.binary_location = chrome_binary
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-extensions")
options.add_argument("--disable-notifications")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--window-size=1920,1080")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--ignore-certificate-errors")

# Optional profile (safe sandbox)
profile_dir = r"C:\Users\I17270834\AppData\Local\Google\Chrome\User Data"

os.makedirs(profile_dir, exist_ok=True)
options.add_argument(f"--user-data-dir={profile_dir}")

prefs = {
    "download.default_directory": str(outdir.resolve()),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# ------------------------------------------------------------------------------
# Initialize ChromeDriver
# ------------------------------------------------------------------------------
try:
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    print("[INFO] Chrome started successfully.")
except Exception as e:
    print(f"[ERROR] Chrome startup failed: {e}")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Jira Login and RTM Export
# ------------------------------------------------------------------------------
try:
    print(f"[INFO] Logging into Jira: {JIRA_BASE}")
    driver.get(JIRA_BASE)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Detect login page
    if "Atlassian" in driver.title or "Login" in driver.title:
        print("[INFO] Atlassian login page detected.")
        try:
            username_box = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='username' or @name='username']"))
            )
            username_box.clear()
            username_box.send_keys(JIRA_USER)
            print("[INFO] Username entered.")

            # Next/Continue
            try:
                driver.find_element(By.ID, "login-submit").click()
            except:
                driver.find_element(By.XPATH, "//button[contains(.,'Continue')]").click()

            # Password
            print("[INFO] Waiting for password field...")
            password_box = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='password' or @name='password']"))
            )
            password_box.clear()
            password_box.send_keys(JIRA_PASS)
            print("[INFO] Password entered.")

            # Log in
            try:
                driver.find_element(By.ID, "login-submit").click()
            except:
                driver.find_element(By.XPATH, "//button[contains(.,'Log in')]").click()

            print("[INFO] Login submitted. Waiting for redirect...")
            time.sleep(10)

        except Exception as e:
            print(f"[WARN] Login elements not found or redirected to SSO: {e}")
            driver.save_screenshot(str(outdir / "sso_redirect.png"))
            print("[WARN] If using SSO, configure Chrome profile reuse via user-data-dir.")
            sys.exit(2)

    else:
        print(f"[INFO] Jira page title: {driver.title}")

    # --------------------------------------------------------------------------
    # Navigate to RTM Test Execution Report
    # --------------------------------------------------------------------------
    rtm_url = f"{JIRA_BASE}/jira/apps/rtm/reports/test-execution"
    print(f"[INFO] Navigating to RTM Test Execution Report: {rtm_url}")
    driver.get(rtm_url)
    time.sleep(8)

    # Fill fields
    driver.find_element(By.XPATH, "//input[@placeholder='Project key']").send_keys(PROJECT_KEY)
    driver.find_element(By.XPATH, "//input[@placeholder='Execution key']").send_keys(TEST_EXEC)
    time.sleep(1)

    print("[INFO] Generating RTM report...")
    driver.find_element(By.XPATH, "//button[contains(.,'Generate')]").click()
    time.sleep(10)

    # --------------------------------------------------------------------------
    # Export Report as PDF
    # --------------------------------------------------------------------------
    print("[INFO] Exporting report as PDF...")
    driver.find_element(By.XPATH, "//button[contains(.,'Export')]").click()
    time.sleep(2)
    driver.find_element(By.XPATH, "//span[text()='PDF']").click()
    time.sleep(20)

    # --------------------------------------------------------------------------
    # Verify Download
    # --------------------------------------------------------------------------
    print(f"[INFO] Checking for downloaded PDF in '{DOWNLOAD_DIR}' ...")
    for f in outdir.glob("*.pdf"):
        print(f"[SUCCESS] Report downloaded: {f}")
        sys.exit(0)

    print("[ERROR] PDF not found after export.")
    driver.save_screenshot(str(outdir / "export_failed.png"))
    sys.exit(3)

except Exception as e:
    print(f"[ERROR] Unexpected failure: {e}")
    driver.save_screenshot(str(outdir / "fatal_error.png"))
    sys.exit(4)

finally:
    driver.quit()
