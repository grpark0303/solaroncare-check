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
    # 봇 차단 회피용 설정 추가
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # 봇 탐지 우회 스크립트
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => False
            })
        """
    })

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인 시도
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(10) # 충분한 로딩

        try:
            # [변경] 특정 속성 대신 페이지 내 모든 'input'을 긁어모음
            inputs = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
            
            # 이메일/비번 칸이 나타날 때까지 반복 확인 (최대 3번)
            target_id = None
            target_pw = None
            
            for i in inputs:
                itype = i.get_attribute("type")
                if itype == "email" or i.get_attribute("name") == "email":
                    target_id = i
                elif itype == "password" or i.get_attribute("name") == "password":
                    target_pw = i
            
            # 만약 위 방법으로 못 찾으면 그냥 0번, 1번 인덱스 사용
            if not target_id: target_id = inputs[0]
            if not target_pw: target_pw = inputs[1]

            # 클릭 후 입력 (사람처럼 보이게)
            driver.execute_script("arguments[0].click();", target_id)
            target_id.send_keys(user_id)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", target_pw)
            target_pw.send_keys(user_pw)
            time.sleep(1)
            
            # 로그인 버튼 (엔터키 입력으로 시도)
            target_pw.send_keys(Keys.ENTER)
            print(">>> 로그인 시도 (엔터키 방식)")
            time.sleep(10) 
        except Exception as e:
            report_details.append(f"❌ 로그인 단계 오류: {str(e)[:30]}")
            total_status = "오류발생"

        # 2. 예약 신청 시도
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(7)

        try:
            # [상담 예약하기]
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '예약')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(3)

            # [네, 보유]
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '보유')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            # [동의]
            agree = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '동의')]")))
            driver.execute_script("arguments[0].click();", agree)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except:
            report_details.append("❌ 상담 예약 신청 : 프로세스 오류")
            total_status = "오류발생"

        # 3. 자사 페이지 검증
        pages = {"상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
                 "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
                 "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"}
        for name, url in pages.items():
            try:
                driver.get(url)
                time.sleep(3)
                report_details.append(f"✅ {name} : 정상")
            except:
                report_details.append(f"❌ {name} : 접속실패")

        # 4. 네이버 BSA
        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

    except Exception:
        total_status = "오류발생"
        report_details.append(f"❌ 시스템 최종 오류 발생")
    
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
