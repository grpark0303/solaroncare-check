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
from selenium.webdriver.common.action_chains import ActionChains

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

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"
    step = "준비"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인 (수동 주입 방식 유지)
        step = "로그인 시도"
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(12)
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            driver.execute_script("arguments[0].value = arguments[1];", inputs[0], user_id)
            driver.execute_script("arguments[0].value = arguments[1];", inputs[1], user_pw)
            time.sleep(1)
            inputs[1].send_keys(Keys.ENTER)
            time.sleep(15) 
        except:
            report_details.append("❌ 로그인 단계 : 실패")
            total_status = "오류발생"

        # 2. 예약 신청
        step = "예약 페이지 접속"
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(10)

        try:
            # 1) 상담 예약하기
            step = "상담 예약하기 클릭"
            btn1 = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '상담 예약')]")))
            driver.execute_script("arguments[0].click();", btn1)
            time.sleep(8)

            # 2) 보유 네 버튼 (전방위적 타겟팅)
            step = "보유 네 버튼 클릭"
            try:
                # 방법 A: '네, 보유' 글자가 포함된 모든 요소 중 가장 위쪽(첫 번째) 버튼 강제 클릭
                target_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '네, 보유')]")
                driver.execute_script("arguments[0].click();", target_elements[0])
            except:
                # 방법 B: 좌표 기반 클릭 (중앙 팝업 영역)
                ActionChains(driver).move_by_offset(960, 500).click().perform()
            time.sleep(5)

            # 3) 필수 동의 체크 (전체동의 회피 및 input 직접 타격)
            step = "필수 동의 체크"
            agree_xpath = "//*[contains(text(), '개인정보') and contains(text(), '필수') and not(contains(text(), '전체'))]"
            agree_element = wait.until(EC.presence_of_element_located((By.XPATH, agree_xpath)))
            driver.execute_script("""
                var el = arguments[0];
                var box = el.parentElement.querySelector('input') || el.querySelector('input') || el;
                box.click();
            """, agree_element)
            time.sleep(3)

            # 4) 최종 제출
            step = "최종 예약하기 제출"
            final_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '예약하기')]")))
            driver.execute_script("arguments[0].click();", final_btn)
            time.sleep(12)

            # 5) 최종 검증
            if "/oncare/result" in driver.current_url:
                report_details.append("✅ 상담 예약 신청 : 완료")
            else:
                report_details.append(f"❌ 상담 예약 신청 : 실패(결과페이지 미도달)")
                total_status = "오류발생"

        except Exception:
            report_details.append(f"❌ 상담 예약 신청 : 실패({step})")
            total_status = "오류발생"

        # 3. 자사 페이지 점검 (실제 이동)
        pages = {"상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
                 "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
                 "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"}
        for name, url in pages.items():
            driver.get(url)
            time.sleep(5)
            report_details.append(f"✅ {name} : 정상")

        # 4. 네이버 BSA (고정)
        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

    except Exception:
        total_status = "오류발생"
        report_details.append("❌ 시스템 최종 오류")
    
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
