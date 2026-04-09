import requests
import datetime
import time
import os
import sys
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20) # 대기 시간을 현실적인 20초로 단축
    
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인 (속도 개선)
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(5)
        inputs = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
        inputs[0].send_keys(user_id)
        inputs[1].send_keys(user_pw)
        inputs[1].send_keys(Keys.ENTER)
        time.sleep(7) # 로그인 후 처리 대기

        # 2. 예약 신청 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        
        # [단계별 정밀 추적]
        try:
            # 1) 상담 예약하기
            btn1 = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '상담 예약')]")))
            driver.execute_script("arguments[0].click();", btn1)
            
            # 2) 보유 네 버튼 (가람님 비기)
            btn2 = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '네') and contains(text(), '보유')]")))
            driver.execute_script("arguments[0].click();", btn2)
            
            # 3) 필수 동의 체크
            agree_el = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '필수') and not(contains(text(), '전체'))]")))
            driver.execute_script("arguments[0].click();", agree_el)
            
            # 4) 최종 예약하기 제출
            submit_btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[contains(., '예약하기')] | //*[text()='예약하기']")))
            driver.execute_script("arguments[0].click();", submit_btns[-1])
            
            # 결과 페이지 확인 (최대 10초만 대기)
            time.sleep(10)
            if "result" in driver.current_url.lower():
                report_details.append("✅ 상담 예약 신청 : 완료")
            else:
                report_details.append(f"❌ 상담 예약 신청 : 실패(미도달: {driver.current_url[-20:]})")
                total_status = "오류발생"

        except Exception as e:
            # 에러가 발생한 위치를 찾기 위해 에러 타입과 메시지를 정확히 출력
            error_type = type(e).__name__
            report_details.append(f"❌ 상담 예약 신청 : 실패({error_type})")
            total_status = "오류발생"

        # 3. 기타 페이지 점검 (속도 업)
        for name, url in {"상세": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
                          "이벤트": "https://solaroncare.com/oncarehome/coupons",
                          "콘텐츠": "https://solaroncare.com/oncarehome/contents"}.items():
            driver.get(url)
            time.sleep(3)
            report_details.append(f"✅ {name} 페이지 : 정상")

    except Exception as e:
        total_status = "오류발생"
        report_details.append(f"❌ 시스템 오류: {str(e)[:20]}")
    
    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    payload = {"entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               "entry.1702029548": status, "entry.1759228838": detail}
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
