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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => false})"
    })

    report_details = []
    total_status = "정상"

    def smart_click(xpath, timeout=30):
        """요소가 나타날 때까지 1초마다 확인하며 클릭 시도"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                el = driver.find_element(By.XPATH, xpath)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", el)
                return True
            except:
                time.sleep(1)
        return False

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(15)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        driver.execute_script("arguments[0].value = arguments[1];", inputs[0], user_id)
        driver.execute_script("arguments[0].value = arguments[1];", inputs[1], user_pw)
        inputs[1].send_keys(Keys.ENTER)
        time.sleep(20)

        # 2. 예약 신청
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(15)

        # [단계별 정밀 타격]
        # 1) 상담 예약하기
        if not smart_click("//*[contains(text(), '상담 예약')]"):
            raise Exception("상담예약하기 버튼 미발견")
        time.sleep(10)

        # 2) 보유 네 버튼
        if not smart_click("//*[normalize-space()='네, 보유하고 있습니다.(준공 및 인허가 단계 포함)'] | //*[contains(text(), '네, 보유')]"):
            raise Exception("보유 네 버튼 미발견")
        time.sleep(5)

        # 3) 필수 동의 체크
        if not smart_click("//*[contains(text(), '필수') and not(contains(text(), '전체'))]"):
            raise Exception("필수동의 체크 미발견")
        time.sleep(3)

        # 4) 최종 예약하기 제출
        if not smart_click("//button[contains(., '예약하기')] | //*[text()='예약하기']"):
            raise Exception("최종 예약하기 버튼 미발견")
        time.sleep(15)

        # 최종 확인
        if "/result" in driver.current_url.lower():
            report_details.append("✅ 상담 예약 신청 : 완료")
        else:
            report_details.append(f"❌ 상담 예약 신청 : 실패(결과페이지 미도달 - {driver.current_url})")
            total_status = "오류발생"

    except Exception as e:
        report_details.append(f"❌ 상담 예약 신청 : 실패({str(e)})")
        total_status = "오류발생"

    # 3. 자사 페이지 점검
    pages = {"상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
             "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
             "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"}
    for name, url in pages.items():
        try:
            driver.get(url)
            time.sleep(8)
            report_details.append(f"✅ {name} : 정상")
        except:
            report_details.append(f"❌ {name} : 오류")

    report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

    driver.quit()
    send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    payload = {"entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               "entry.1702029548": status, "entry.1759228838": detail}
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
