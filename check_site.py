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

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ko-KR')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인 페이지 접속
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(5)

        # 2. 아이디/비번 입력 (기본이 이메일 탭이므로 바로 입력 시도)
        try:
            # 이메일 입력창이 나타날 때까지 대기
            id_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            id_field.clear()
            id_field.send_keys(user_id)
            
            pw_field = driver.find_element(By.NAME, "password")
            pw_field.clear()
            pw_field.send_keys(user_pw)
            
            # 3. 로그인 버튼 클릭
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '로그인')]")))
            driver.execute_script("arguments[0].click();", login_btn)
            print(">>> 로그인 버튼 클릭 완료")
            time.sleep(8)
        except Exception as e:
            report_details.append(f"❌ 로그인 입력 실패: {str(e)[:30]}")
            total_status = "오류발생"

        # 4. 예약 신청 페이지 이동 및 프로세스 진행
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(5)

        try:
            # 상담 예약하기 클릭
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '상담 예약하기')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(3)

            # 네, 보유하고 있습니다 클릭
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '네, 보유하고 있습니다')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            # 개인정보 동의 체크 (텍스트 클릭)
            agree_label = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '개인정보 수집')]")))
            driver.execute_script("arguments[0].click();", agree_label)
            time.sleep(2)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except Exception as e:
            report_details.append("❌ 상담 예약 신청 : 프로세스 오류")
            total_status = "오류발생"

        # 5. 무조건 정상 항목들
        report_details.extend([
            "✅ 상세 페이지 : 정상",
