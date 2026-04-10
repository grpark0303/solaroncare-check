import requests
import datetime
import time
import os
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", el)


def run_automation():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    # 봇 감지 우회
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
            window.chrome = { runtime: {} };
        """
    })

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # ── 1. 로그인 ──────────────────────────────────────────────
        print("[1] 로그인 페이지 접속")
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(5)
        driver.save_screenshot("step1_login_page.png")

        print("[2] 이메일 입력")
        id_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email']")
        ))
        id_input.clear()
        id_input.send_keys(user_id)
        time.sleep(1)

        print("[3] 비밀번호 입력")
        pw_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password']")
        ))
        pw_input.clear()
        pw_input.send_keys(user_pw)
        time.sleep(2)
        driver.save_screenshot("step2_after_input.png")

        print("[4] 로그인 버튼 클릭")
        login_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             "//div[contains(@class,'bg-main-color') "
             "and contains(@class,'button--round') "
             "and .//div[contains(text(),'로그인')]]")
        ))
        click(driver, login_btn)
        time.sleep(10)
        driver.save_screenshot("step3_after_login_click.png")
        print(f"[4] 로그인 후 URL: {driver.current_url}")

        if "login" in driver.current_url:
            raise Exception(f"로그인 실패 — 현재 URL: {driver.current_url}")

        report_details.append("✅ 로그인 : 완료")
        driver.save_screenshot("step4_after_login.png")

        # ── 2. 상담 예약하기 ───────────────────────────────────────
        print("[5] 서비스 소개 페이지 이동")
        driver.get(
            "https://so
