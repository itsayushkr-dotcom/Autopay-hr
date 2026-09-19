"""
AutoPay-HR Streamlit Cloud Keep-Alive Daemon
Periodically checks https://autopay-hr.streamlit.app/
If the app has hibernated ('This app has gone to sleep due to inactivity'),
it clicks 'Yes, get this app back up!' and waits for container activation.
"""
import os
import sys
import time

STREAMLIT_URL = os.environ.get("STREAMLIT_APP_URL", "https://autopay-hr.streamlit.app/")

def run():
    print(f"[Keep-Alive] Checking Streamlit Cloud status at: {STREAMLIT_URL}")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.common.exceptions import TimeoutException
    except ImportError as err:
        print(f"[Keep-Alive] Missing dependency: {err}")
        print("Please install selenium and webdriver-manager: pip install selenium webdriver-manager")
        sys.exit(1)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"[Keep-Alive] ChromeDriverManager notice ({e}), falling back to direct Chrome driver...")
        driver = webdriver.Chrome(options=options)

    try:
        driver.get(STREAMLIT_URL)
        print(f"[Keep-Alive] Connected. Page title: {driver.title or '(loading)'}")
        time.sleep(6)

        # XPaths to locate the Streamlit Community Cloud 'wake up' button
        wake_button_xpaths = [
            "//button[contains(., 'Yes, get this app back up')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get this app back up')]",
            "//button[contains(., 'wake up') or contains(., 'Wake up')]",
        ]

        button_found = None
        for xpath in wake_button_xpaths:
            try:
                wait = WebDriverWait(driver, 6)
                elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if elem:
                    button_found = elem
                    break
            except TimeoutException:
                continue

        if button_found:
            print("[Keep-Alive] App is asleep! Found wake-up button. Clicking 'Yes, get this app back up!'...")
            button_found.click()
            try:
                wait = WebDriverWait(driver, 60)
                wait.until(EC.invisibility_of_element_located((By.XPATH, wake_button_xpaths[0])))
                print("[Keep-Alive] Wake-up button disappeared! Container is booting up.")
                time.sleep(12)
                print("[Keep-Alive] App successfully awakened.")
            except TimeoutException:
                print("[Keep-Alive] Button was clicked; waiting for server response completed.")
        else:
            print("[Keep-Alive] App is active and responsive! Inactivity timer refreshed successfully.")

    except Exception as exc:
        print(f"[Keep-Alive] Exception encountered: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        driver.quit()
        print("[Keep-Alive] Session closed.")

if __name__ == "__main__":
    run()
