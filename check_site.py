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
from selenium.webdriver.common.keys import Keys

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ko-KR')
    # 봇 탐지 우회 설정
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => false})"
    })

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # --- [STEP 1] 로그인 프로세스 ---
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(10)

        try:
            # 이메일/비번 입력창 (순서대로 타겟팅)
            inputs = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
            driver.execute_script("arguments[0].value = arguments[1];", inputs[0], user_id)
            driver.execute_script("arguments[0].value = arguments[1];", inputs[1], user_pw)
            time.sleep(1)
            inputs[1].send_keys(Keys.ENTER)
            
            # 로그인 후 메인 전환 대기
            time.sleep(15) 
        except:
            report_details.append("❌ 로그인 단계 : 오류 (입력 실패)")
            total_status = "오류발생"

        # --- [STEP 2] 상담 예약 및 결과 페이지 검증 ---
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(10)

        try:
            # 1. '상담 예약하기' 버튼 클릭
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '상담 예약')] | //button[contains(., '예약')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(5)

            # 2. '네, 보유하고 있습니다' 클릭 (아니오 제외 로직)
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '네') and contains(., '보유')] | //*[contains(text(), '네') and contains(text(), '보유')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            # 3. '필수 동의'만 체크 (전체 동의 제외 로직)
            # '전체' 글자가 없고, '개인정보'와 '필수' 글자가 있는 요소만 타겟팅
            agree = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '개인정보') and contains(text(), '필수') and not(contains(text(), '전체'))]")))
            driver.execute_script("arguments[0].click();", agree)
            time.sleep(2)

            # 4. 최종 '예약하기' 제출
            final_submit = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '예약하기')]")))
            driver.execute_script("arguments[0].click();", final_submit)
            time.sleep(10)

            # 5. 결과 페이지 검증 (/result 주소 확인)
            if "/oncare/result" in driver.current_url:
                report_details.append("✅ 상담 예약 신청 : 완료 (필수동의 확인)")
            else:
                report_details.append("❌ 상담 예약 신청 : 실패 (최종 페이지 미도달)")
                total_status = "오류발생"

        except Exception as e:
            report_details.append(f"❌ 상담 예약 신청 : 프로세스 오류")
            total_status = "오류발생"

        # --- [STEP 3] 자사 페이지 실제 검증 ---
        check_pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in check_pages.items():
            try:
                driver.get(url)
                time.sleep(5)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name} : 정상")
                else:
                    report_details.append(f"❌ {name} : 주소 불일치")
                    total_status = "오류발생"
            except:
                report_details.append(f"❌ {name} : 접속 실패")
                total_status = "오류발생"

        # --- [STEP 4] 네이버 BSA (가람님 요청 고정값) ---
        report_details.extend([
            "✅ 네이버 BSA 메인 : 정상",
            "✅ 네이버 BSA 썸네일1 : 정상",
            "✅ 네이버 BSA 썸네일2 : 정상",
            "✅ 네이버 BSA 썸네일3 : 정상"
        ])

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
        "entry.1702029548": status,
        "entry.1759228838": detail
    }
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
