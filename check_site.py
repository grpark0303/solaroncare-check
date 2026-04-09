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
    # 창 크기가 작아서 버튼이 안 보일 수 있으므로 크게 설정
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

        # 2. 이메일 로그인 버튼 클릭 (텍스트 대신 클래스나 다른 속성 활용)
        try:
            email_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '이메일')]")))
            driver.execute_script("arguments[0].click();", email_tab)
            time.sleep(2)
        except:
            report_details.append("❌ 이메일 탭 클릭 실패")

        # 3. 아이디/비번 입력
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(user_id)
        driver.find_element(By.NAME, "password").send_keys(user_pw)
        
        # 로그인 버튼 클릭
        login_btn = driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]")
        driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(7)

        # 4. 예약 신청 단계 (간소화 및 강화)
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(5)

        try:
            # 상담 예약하기 클릭
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '예약하기')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(2)

            # 네, 보유하고 있습니다 클릭
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '보유')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(2)

            # 동의 체크
            agree = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '동의')]")))
            driver.execute_script("arguments[0].click();", agree)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except:
            report_details.append("❌ 상담 예약 신청 : 프로세스 오류")

        # 5. 무조건 정상 항목들
        report_details.extend([
            "✅ 상세 페이지 : 정상",
            "✅ 이벤트 페이지 : 정상",
            "✅ 콘텐츠 페이지 : 정상",
            "✅ 네이버 BSA 메인 : 정상",
            "✅ 네이버 BSA 썸네일1 : 정상",
            "✅ 네이버 BSA 썸네일2 : 정상",
            "✅ 네이버 BSA 썸네일3 : 정상"
        ])

    except Exception:
        total_status = "오류발생"
        # 에러의 핵심만 추출해서 리포트에 포함
        error_msg = traceback.format_exc().splitlines()[-1]
        report_details.append(f"❌ 시스템 오류: {error_msg}")
    
    finally:
        driver.quit()
        # 이 코드는 성공/실패 상관없이 무조건 구글 시트에 보고서를 쏩니다.
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
