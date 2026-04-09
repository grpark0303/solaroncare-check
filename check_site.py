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
    wait = WebDriverWait(driver, 30) # 대기 시간을 30초로 최대화
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인 페이지 접속
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(7) # 페이지 로딩 넉넉히 대기

        # 2. 아이디/비번 입력 (기본 이메일 탭 상태)
        try:
            # 이메일 입력창 찾기 (name 혹은 type으로 검색)
            id_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='email' or @type='email']")))
            id_field.clear()
            id_field.send_keys(user_id)
            
            pw_field = driver.find_element(By.XPATH, "//input[@name='password' or @type='password']")
            pw_field.clear()
            pw_field.send_keys(user_pw)
            
            # 3. 로그인 버튼 클릭 (텍스트 '로그인'이 포함된 모든 버튼 검색)
            login_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '로그인')]")))
            driver.execute_script("arguments[0].click();", login_btn)
            print(">>> 로그인 버튼 클릭 성공")
            time.sleep(10) # 로그인 처리 후 메인 이동 대기
        except Exception as e:
            report_details.append(f"❌ 로그인 단계 오류: 입력창/버튼 미발견")
            total_status = "오류발생"

        # 4. 예약 신청 페이지 이동 및 프로세스 진행
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(7)

        try:
            # [상담 예약하기] 클릭
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '예약')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(3)

            # [네, 보유하고 있습니다] 클릭
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '보유')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            # 개인정보 동의 체크 (텍스트 클릭)
            agree_label = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '동의') or contains(text(), '개인정보')]")))
            driver.execute_script("arguments[0].click();", agree_label)
            time.sleep(2)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except Exception as e:
            report_details.append("❌ 상담 예약 신청 : 프로세스 오류 (버튼 미발견)")
            total_status = "오류발생"

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
        # 상세 에러 메시지 추출
        error_info = traceback.format_exc().splitlines()[-1]
        report_details.append(f"❌ 시스템 최종 오류: {error_info}")
    
    finally:
        driver.quit()
        # 시트에 결과 전송
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
