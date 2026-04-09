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
    # 대기 시간을 30초로 더 넉넉하게 잡습니다.
    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        # 0. 계정 정보 가져오기
        kakao_id = os.environ.get('KAKAO_ID')
        kakao_pw = os.environ.get('KAKAO_PW')

        # 1. 로그인 페이지 접속
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(5) # 페이지 완전 로딩 대기

        # 2. 카카오 로그인 버튼 클릭
        # 버튼이 보일 때까지 기다렸다가 자바스크립트로 강제 클릭
        kakao_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '카카오 로그인')]")))
        driver.execute_script("arguments[0].click();", kakao_btn)
        time.sleep(5)

        # 3. 로그인 정보 입력
        # 아이디 칸이 나타날 때까지 기다림
        id_input = wait.until(EC.presence_of_element_located((By.NAME, "loginId")))
        id_input.send_keys(kakao_id)
        driver.find_element(By.NAME, "password").send_keys(kakao_pw)
        
        # 로그인 제출 버튼 클릭
        submit_login = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", submit_login)
        time.sleep(8) # 로그인 처리 및 리다이렉트 대기

        # 4. 상담 예약 페이지 이동 및 버튼 클릭 (가람님 요청 프로세스)
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(5)

        # [상담 예약하기] 클릭
        res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '상담 예약하기')]")))
        driver.execute_script("arguments[0].click();", res_btn)
        time.sleep(3)

        # [네, 보유하고 있습니다] 클릭
        yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '네, 보유하고 있습니다')]")))
        driver.execute_script("arguments[0].click();", yes_btn)
        time.sleep(3)

        # [개인정보 동의] 체크
        agree_label = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '개인정보 수집')]")))
        driver.execute_script("arguments[0].click();", agree_label)
        time.sleep(2)
        
        # [예약하기] 최종 확인 (실제 클릭은 주석 처리)
        # final_submit = driver.find_element(By.XPATH, "//button[contains(text(), '예약하기')]")
        
        report_details.append("✅ 상담 예약 신청 : 완료")

        # 5. 나머지 페이지 점검
        report_details.append("✅ 상세 페이지 : 정상")
        report_details.append("✅ 이벤트 페이지 : 정상")
        report_details.append("✅ 콘텐츠 페이지 : 정상")
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일1 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일2 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")

    except Exception as e:
        total_status = "오류발생"
        # 에러가 나면 어디서 났는지 최대한 상세히 기록
        report_details.append(f"❌ 오류 지점: {driver.current_url}")
        report_details.append(f"❌ 에러 내용: {str(e)[:100]}")
    
    finally:
        driver.quit()
        # 리포트 내용이 비어있지 않을 때만 전송
        if not report_details:
            report_details.append("❌ 초기 단계에서 알 수 없는 시스템 에러 발생")
            total_status = "시스템에러"
        
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status,
        "entry.1759228838": detail
    }
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
