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
from selenium.webdriver.common.keys import Keys

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ko-KR')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 기다리는 시간을 60초로 넉넉하게 설정
    wait = WebDriverWait(driver, 60)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(15)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        driver.execute_script("arguments[0].value = arguments[1];", inputs[0], user_id)
        driver.execute_script("arguments[0].value = arguments[1];", inputs[1], user_pw)
        inputs[1].send_keys(Keys.ENTER)
        time.sleep(20)

        # 2. 예약 신청 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        
        # 1) 상담 예약하기 클릭 (나타날 때까지 기다림)
        btn1 = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '상담 예약')]")))
        driver.execute_script("arguments[0].click();", btn1)
        
        # 2) 보유 네 버튼 (아까 성공했던 그 로직 + 대기 강화)
        # 팝업이 뜰 때까지 최대 60초간 기다린 후 클릭
        btn2 = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '네') and contains(text(), '보유')]")))
        driver.execute_script("arguments[0].click();", btn2)
        time.sleep(5)

        # 3) 필수 동의 체크
        agree_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '필수') and not(contains(text(), '전체'))]")))
        driver.execute_script("arguments[0].click();", agree_el)
        time.sleep(3)

        # 4) 최종 예약하기 제출
        submit_btn = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[contains(., '예약하기')] | //*[text()='예약하기']")))
        driver.execute_script("arguments[0].click();", submit_btn[-1])
        time.sleep(15)

        # 최종 확인
        if "/result" in driver.current_url.lower():
            report_details.append("✅ 상담 예약 신청 : 완료")
        else:
            report_details.append(f"❌ 상담 예약 신청 : 실패(최종 페이지 미도달)")
            total_status = "오류발생"

    except Exception as e:
        # 에러 메시지를 좀 더 자세히 남겨서 원인 파악
        report_details.append(f"❌ 상담 예약 신청 : 실패({str(e)[:50]})")
        total_status = "오류발생"

    # 3. 자사 페이지 점검 (생략 방지)
    for name, url in {"상세 페이지": "
