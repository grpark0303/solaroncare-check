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
from selenium.webdriver.common.keys import Keys

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ko-KR')
    # 봇 탐지 우회 설정
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => false})"
    })

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # --- [STEP 1] 로그인 프로세스 ---
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(10)

        try:
            # 이메일/비번 입력창 (순서대로 타겟팅)
            inputs = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
            driver.execute_script("arguments[0].value = arguments[1];", inputs[0], user_id)
            driver.execute_script("arguments[0].value = arguments[1];", inputs[1], user_pw)
            time.sleep(1)
            inputs[1].send_keys(Keys.ENTER)
            
            # 로그인 후 메인 전환 대기
            time.sleep(15) 
        except:
            report_details.append("❌ 로그인 단계 : 오류 (입력 실패)")
            total_status = "오류발생"

        # --- [STEP 2] 상담 예약 및 결과 페이지 검증 ---
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(10)
