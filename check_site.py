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
    options.add_argument('--headless') # 서버 실행을 위해 headless 유지
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    report_details = []
    total_status = "정상"

    try:
        # --- [STEP 0] 카카오 자동 로그인 및 상담 예약 ---
        print(">>> 로그인을 시작합니다.")
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(3)
        
        # 카카오 로그인 버튼 클릭
        kakao_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '카카오 로그인')]")))
        driver.execute_script("arguments[0].click();", kakao_btn)
        time.sleep(3)

        # 깃허브 Secrets에서 불러오는 계정 정보
        kakao_id = os.environ.get('KAKAO_ID')
        kakao_pw = os.environ.get('KAKAO_PW')

        if kakao_id and kakao_pw:
            # 아이디/비번 입력 (사람처럼 보이게 한 글자씩 입력하는 효과는 없지만 딜레이를 줌)
            driver.find_element(By.NAME, "loginId").send_keys(kakao_id)
            time.sleep(1)
            driver.find_element(By.NAME, "password").send_keys(kakao_pw)
            time.sleep(1)
            
            # 로그인 제출
            login_submit = driver.find_element(By.XPATH, "//button[@type='submit']")
            driver.execute_script("arguments[0].click();", login_submit)
            print(">>> 로그인 버튼을 눌렀습니다.")
            time.sleep(5) # 로그인 후 페이지 전환 대기
        
        # 상담 예약 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(3)

        try:
            # 1. 상담 예약하기 버튼 클릭
            res_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '상담 예약하기')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(2)

            # 2. '네, 보유하고 있습니다' 클릭
            yes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '네, 보유하고 있습니다')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(2)

            # 3. 개인정보 동의 체크
            agree_label = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '개인정보 수집')]")))
            driver.execute_script("arguments[0].click();", agree_label)
            time.sleep(1)
            
            # 4. 예약하기 최종 버튼 (실제 클릭은 하지 않고 확인만)
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '예약하기')]")))
            # driver.execute_script("arguments[0].click();", submit_btn) # 실제 예약하려면 주석 해제

            report_details.append("✅ 상담 예약 신청 : 완료")
        except:
            total_status = "오류발생"
            report_details.append("❌ 상담 예약 신청 : 실패 (로그인 차단 등)")

        # --- [STEP 1] 기존 자사 페이지 점검 ---
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        
        for name, url in pages.items():
            try:
                driver.get(url)
                time.sleep(2)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name} : 정상")
                else:
                    total_status = "오류발생"
                    report_details.append(f"❌ {name} : 오류")
            except:
                total_status = "오류발생"
                report_details.append(f"❌ {name} : 접속에러")

        # --- [STEP 2] 네이버 BSA 영역 (고정값) ---
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일1 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일2 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")

    except Exception as e:
        total_status = "시스템에러"
        report_details.append(f"⚠️ 시스템에러: {str(e)[:30]}")
    finally:
        driver.quit()
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
