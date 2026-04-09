import requests
import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # 대기 시간을 30초로 넉넉하게 설정
    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        # 0. 계정 정보 가져오기
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        if not user_id or not user_pw:
            raise Exception("Secrets(EMAIL_ID, EMAIL_PW) 설정이 되어있지 않습니다.")

        # 1. 로그인 페이지 접속
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(5)

        # 2. [이메일 로그인] 탭 클릭
        # 텍스트가 정확히 '이메일 로그인'인 버튼을 찾습니다.
        email_tab = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '이메일 로그인')]")))
        driver.execute_script("arguments[0].click();", email_tab)
        time.sleep(3)

        # 3. 아이디/비번 입력
        id_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        id_field.send_keys(user_id)
        
        pw_field = driver.find_element(By.NAME, "password")
        pw_field.send_keys(user_pw)

        # 4. 로그인 버튼 클릭
        login_btn = driver.find_element(By.XPATH, "//button[text()='로그인' or contains(., '로그인')]")
        driver.execute_script("arguments[0].click();", login_btn)
        print(">>> 로그인 시도 중...")
        time.sleep(8) 

        # 5. 상담 예약 신청 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(5)

        try:
            # [상담 예약하기] 클릭
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '상담 예약하기')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(3)

            # [네, 보유하고 있습니다] 클릭
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '네, 보유하고 있습니다')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            # [개인정보 동의] 체크 (체크박스 옆의 텍스트 클릭)
            agree_label = wait.
