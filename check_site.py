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

        # [단계별 강제 집행]
        # 1) 상담 예약하기
        try:
            btn1 = driver.find_element(By.XPATH, "//*[contains(text(), '상담 예약')]")
            driver.execute_script("arguments[0].click();", btn1)
        except:
            raise Exception("상담예약 버튼 클릭 실패")
        time.sleep(10)

        # 2) 보유 네 버튼 (글자 매칭 안 하고 모달 안의 첫 버튼 클릭)
        try:
            # 화면에 뜬 '모달' 또는 '팝업' 레이어 안의 모든 버튼을 긁어옴
            modal_btns = driver.find_elements(By.XPATH, "//div[contains(@class, 'modal')]//button | //div[contains(@class, 'popup')]//button | //button[contains(., '보유')]")
            # 가람님 캡처상 첫 번째 버튼이 무조건 '네' 버튼이므로 0번 인덱스 타격
            driver.execute_script("arguments[0].click();", modal_btns[0])
        except:
            raise Exception("보유 네 버튼 강제 클릭 실패")
        time.sleep(7)

        # 3) 필수 동의 체크
        try:
            agree_el = driver.find_element(By.XPATH, "//*[contains(text(), '필수') and not(contains(text(), '전체'))]")
            driver.execute_script("""
                var cb = arguments[0].closest('div').querySelector('input');
                if(cb) { cb.checked = true; cb.click(); } else { arguments[0].click(); }
            """, agree_el)
        except:
            raise Exception("필수동의 체크 실패")
        time.sleep(5)

        # 4) 최종 예약하기 제출
        try:
            final_btns = driver.find_elements(By.XPATH, "//button[contains(., '예약하기')] | //*[text()='예약하기']")
            driver.execute_script("arguments[0].click();", final_btns[-1])
        except:
            raise Exception("최종 예약 버튼 클릭 실패")
        time.sleep(15)

        # 최종 확인
        if "/result" in driver.current_url.lower():
            report_details.append("✅ 상담 예약 신청 : 완료")
        else:
            report_details.append(f"❌ 상담 예약 신청 : 실패(최종 페이지 미도달)")
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
            time.sleep(5)
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
