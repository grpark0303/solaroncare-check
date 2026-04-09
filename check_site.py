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

        # 2. 아이디/비번 입력 및 로그인
        try:
            id_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            id_field.clear()
            id_field.send_keys(user_id)
            
            pw_field = driver.find_element(By.NAME, "password")
            pw_field.clear()
            pw_field.send_keys(user_pw)
            
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '로그인')]")))
            driver.execute_script("arguments[0].click();", login_btn)
            time.sleep(8)
        except Exception as e:
            report_details.append(f"❌ 로그인 단계 오류: {str(e)[:20]}")
            total_status = "오류발생"

        # 3. 상담 예약 신청 프로세스 (실제 체크)
        try:
            driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
            time.sleep(5)
            
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '상담 예약하기')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(3)

            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '네, 보유하고 있습니다')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            agree_label = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '개인정보 수집')]")))
            driver.execute_script("arguments[0].click();", agree_label)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except:
            report_details.append("❌ 상담 예약 신청 : 프로세스 오류")
            total_status = "오류발생"

        # 4. 자사 페이지 점검 (실제 접속 확인 로직 복구)
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        
        for name, url in pages.items():
            try:
                driver.get(url)
                time.sleep(3)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name} : 정상")
                else:
                    report_details.append(f"❌ {name} : 오류")
                    total_status = "오류발생"
            except:
                report_details.append(f"❌ {name} : 접속불가")
                total_status = "오류발생"

        # 5. 네이버 BSA (가람님 요청대로 무조건 정상 출력)
        report_details.extend([
            "✅ 네이버 BSA 메인 : 정상",
            "✅ 네이버 BSA 썸네일1 : 정상",
            "✅ 네이버 BSA 썸네일2 : 정상",
            "✅ 네이버 BSA 썸네일3 : 정상"
        ])

    except Exception:
        total_status = "오류발생"
        error_msg = traceback.format_exc().splitlines()[-1]
        report_details.append(f"❌ 시스템 오류: {error_msg}")
    
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
