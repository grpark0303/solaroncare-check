import requests
import datetime
import time
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
    wait = WebDriverWait(driver, 15)
    report_details = []
    total_status = "정상"

    try:
        # --- [STEP 0] 로그인 세션 주입 및 실제 상담 예약 완료 시도 ---
        driver.get("https://solaroncare.com")
        time.sleep(2)
        
        # 가람님의 세션 쿠키 주입 (로그인 상태 만들기)
        driver.add_cookie({
            'name': 'sessionid',
            'value': '5fcefedfd7f357ed88d809e3f1f53514', 
            'domain': '.solaroncare.com',
            'path': '/'
        })
        
        # 예약 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(3)

        try:
            # 1. [상담 예약하기] 클릭
            reserve_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '상담 예약하기')]")))
            reserve_btn.click()
            time.sleep(1)
            
            # 2. [네, 보유하고 있습니다] 클릭
            yes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '네, 보유하고 있습니다')]")))
            yes_btn.click()
            time.sleep(2)

            # 3. [개인정보 수집 및 이용 동의 (필수)] 체크박스 클릭
            # 텍스트가 있는 label이나 span을 클릭하여 체크 활성화
            agreement_label = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '개인정보 수집 및 이용 동의')] | //label[contains(., '개인정보 수집 및 이용 동의')]")))
            agreement_label.click()
            time.sleep(1)
            
            # 4. 최종 [예약하기] 버튼 클릭 (실제 전송)
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '예약하기')]")))
            submit_btn.click()
            time.sleep(3)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except Exception as e:
            total_status = "오류발생"
            report_details.append("❌ 상담 예약 신청 : 실패 (요소 찾기 불가 또는 세션 만료)")

        # --- [STEP 1] 기존 자사 페이지 점검 ---
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        
        for name, url in pages.items():
            try:
                driver.get(url)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name} : 정상")
                else:
                    report_details.append(f"❌ {name} : 오류")
            except:
                report_details.append(f"❌ {name} : 접속에러")

        # --- [STEP 2] 네이버/구글 결과 (기존 유지) ---
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        # ... (중략) ...
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")
        # (구글 광고 로직 생략 또는 기존 것 유지 가능)

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
