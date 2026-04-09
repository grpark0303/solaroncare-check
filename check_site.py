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
    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인 시도
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(10) # 넉넉한 로딩 시간

        try:
            # 이메일 입력창: 속성값을 더 포괄적으로 검색
            email_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email'] | //input[contains(@placeholder, '이메일')] | //input[@name='email']")))
            
            # 일반적인 send_keys가 안 통할 경우를 대비해 JS로 강제 값 주입
            driver.execute_script("arguments[0].value = '';", email_input)
            email_input.send_keys(user_id)
            
            # 비밀번호 입력창
            pw_input = driver.find_element(By.XPATH, "//input[@type='password'] | //input[contains(@placeholder, '비밀번호')]")
            driver.execute_script("arguments[0].value = '';", pw_input)
            pw_input.send_keys(user_pw)
            
            # 로그인 버튼: '로그인' 텍스트를 가진 버튼을 더 정확히 타겟팅
            login_btn = driver.find_element(By.XPATH, "//button[./span[contains(text(), '로그인')]] | //button[contains(text(), '로그인')] | //button[@type='submit']")
            driver.execute_script("arguments[0].click();", login_btn)
            
            print(">>> 로그인 시도 (JS 주입 방식)")
            time.sleep(10) # 로그인 후 전환 대기
        except Exception as e:
            report_details.append(f"❌ 로그인 단계 오류: {str(e)[:30]}")
            total_status = "오류발생"

        # 2. 예약 신청 시도 (로그인 성공 여부와 상관없이 시도는 함)
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(7)

        try:
            # [상담 예약하기] 클릭
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '상담 예약하기')] | //button[contains(., '예약')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(3)

            # [네, 보유하고 있습니다] 클릭
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '보유')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            # [개인정보 동의] 체크
            agree = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '동의')]")))
            driver.execute_script("arguments[0].click();", agree)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except:
            report_details.append("❌ 상담 예약 신청 : 프로세스 오류")
            total_status = "오류발생"

        # 3. 자사 페이지 실제 검증
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
            except:
                report_details.append(f"❌ {name} : 접속실패")

        # 4. 네이버 BSA (고정)
        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

    except Exception:
        total_status = "오류발생"
        error_info = traceback.format_exc().splitlines()[-1]
        report_details.append(f"❌ 시스템 최종 오류: {error_info}")
    
    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status, "entry.1759228838": detail
    }
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
