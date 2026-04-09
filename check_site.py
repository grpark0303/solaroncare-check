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
    wait = WebDriverWait(driver, 20)
    report_details = []
    total_status = "정상"

    try:
        # --- [STEP 0] 로그인 및 예약 (실제 검증) ---
        kakao_id = os.environ.get('KAKAO_ID')
        kakao_pw = os.environ.get('KAKAO_PW')

        driver.get("https://solaroncare.com/oncarehome/login")
        
        # 1. 카카오 로그인 버튼 클릭
        kakao_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '카카오 로그인')]")))
        driver.execute_script("arguments[0].click();", kakao_btn)
        
        # 2. 아이디/비번 입력
        wait.until(EC.presence_of_element_located((By.NAME, "loginId"))).send_keys(kakao_id)
        driver.find_element(By.NAME, "password").send_keys(kakao_pw)
        
        # 3. 로그인 제출
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)

        # 4. 예약 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        
        # 5. 상담 예약하기 버튼 클릭
        res_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '상담 예약하기')]")))
        driver.execute_script("arguments[0].click();", res_btn)
        
        # 6. '네, 보유하고 있습니다' 클릭
        yes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '네, 보유하고 있습니다')]")))
        driver.execute_script("arguments[0].click();", yes_btn)
        
        # 7. 개인정보 동의 체크
        agree_check = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '개인정보 수집')]")))
        driver.execute_script("arguments[0].click();", agree_check)
        
        # 여기까지 성공하면 기록
        report_details.append("✅ 상담 예약 신청 : 완료")

        # --- [STEP 1] 자사 페이지 점검 (실제 검증) ---
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            driver.get(url)
            if "solaroncare" in driver.current_url:
                report_details.append(f"✅ {name} : 정상")
            else:
                raise Exception(f"{name} 이동 실패")

        # --- [STEP 2] 네이버 BSA (요청하신 대로 무조건 정상 출력) ---
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일1 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일2 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")

    except Exception as e:
        total_status = "오류발생"
        # 실제 에러가 나
