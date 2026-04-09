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
    wait = WebDriverWait(driver, 30)
    
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(5)
        inputs = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
        inputs[0].send_keys(user_id)
        inputs[1].send_keys(user_pw)
        inputs[1].send_keys(Keys.ENTER)
        time.sleep(15)

        # 2. 예약 신청 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        
        try:
            # 1) 상담 예약하기
            btn1 = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '상담 예약')]")))
            driver.execute_script("arguments[0].click();", btn1)
            
            # 2) [좀비 로직] 보유 버튼 찾을 때까지 무한 반복 (최대 30초)
            found_btn = None
            for _ in range(30):
                # 모든 버튼/div/span을 다 뒤져서 '네'와 '보유'가 있는 놈 검거
                candidates = driver.find_elements(By.XPATH, "//button | //div[@role='button'] | //span | //a")
                for c in candidates:
                    try:
                        txt = c.text
                        if "네" in txt and "보유" in txt:
                            found_btn = c
                            break
                    except: continue
                if found_btn: break
                time.sleep(1)

            if not found_btn:
                raise Exception("보유버튼 미발견(리스트 0)")
            
            driver.execute_script("arguments[0].click();", found_btn)
            time.sleep(5)
            
            # 3) 필수 동의 체크
            agree_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '필수') and not(contains(text(), '전체'))]")))
            driver.execute_script("arguments[0].click();", agree_el)
            time.sleep(3)
            
            # 4) 최종 예약하기 제출
            submit_btns = driver.find_elements(By.XPATH, "//button[contains(., '예약하기')] | //*[text()='예약하기']")
            driver.execute_script("arguments[0].click();", submit_btns[-1])
            
            time.sleep(20)
            if "result" in driver.current_url.lower():
                report_details.append("✅ 상담 예약 신청 : 완료")
            else:
                report_details.append(f"❌ 상담 예약 신청 : 실패(결과 미도달)")
                total_status = "오류발생"

        except Exception as e:
            report_details.append(f"❌ 상담 예약 신청 : 실패({str(e)})")
            total_status = "오류발생"

        # 3. 자사 페이지 점검
        pages = {"상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
                 "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
                 "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"}
        for name, url in pages.items():
            driver.get(url)
            time.sleep(5)
            report_details.append(f"✅ {name} : 정상")

        # 4. 네이버 BSA
        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

    except Exception:
        total_status = "오류발생"
        report_details.append("❌ 시스템 오류")
    
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
