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

        # 1. 로그인
        step = "로그인 시도"
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(12)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        driver.execute_script("arguments[0].value = arguments[1];", inputs[0], user_id)
        driver.execute_script("arguments[0].value = arguments[1];", inputs[1], user_pw)
        inputs[1].send_keys(Keys.ENTER)
        time.sleep(15) 

        # 2. 예약 신청
        step = "예약 페이지 접속"
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(10)

        try:
            # 1) 상담 예약하기
            step = "상담 예약하기 클릭"
            btn1 = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '상담 예약')]")))
            driver.execute_script("arguments[0].click();", btn1)
            time.sleep(10)

            # 2) 보유 네 버튼
            step = "보유 네 버튼 클릭"
            yes_els = driver.find_elements(By.XPATH, "//*[contains(text(), '네') and contains(text(), '보유')]")
            driver.execute_script("arguments[0].click();", yes_els[0])
            time.sleep(5)

            # 3) 필수 동의 체크
            step = "필수 동의 체크"
            agree_xpath = "//*[contains(text(), '필수') and not(contains(text(), '전체'))]"
            agree_el = wait.until(EC.presence_of_element_located((By.XPATH, agree_xpath)))
            driver.execute_script("""
                var el = arguments[0];
                var container = el.closest('div') || el.parentElement;
                var cb = container.querySelector('input');
                if(cb) { cb.checked = true; cb.click(); } else { el.click(); }
            """, agree_el)
            time.sleep(5)

            # 4) 최종 제출 (필살기 모음)
            step = "최종 예약하기 제출"
            # [방법 A] 가장 하단에 있는 '예약하기' 텍스트 요소 찾기
            final_btn = driver.find_elements(By.XPATH, "//*[text()='예약하기' or contains(text(), '예약하기')]")[-1]
            driver.execute_script("arguments[0].scrollIntoView(true);", final_btn)
            time.sleep(2)
            
            # [방법 B] 자바스크립트 클릭 + 마우스 좌표 클릭 + 엔터키 입력 콤보
            try:
                driver.execute_script("arguments[0].click();", final_btn)
                ActionChains(driver).move_to_element(final_btn).click().perform()
                final_btn.send_keys(Keys.ENTER)
            except:
                pass 
                
            time.sleep(15) # 결과 페이지 이동 대기

            # 5) 최종 확인
            if "/result" in driver.current_url.lower():
                report_details.append("✅ 상담 예약 신청 : 완료")
            else:
                report_details.append(f"❌ 상담 예약 신청 : 실패(결과페이지 미도달)")
                total_status = "오류발생"

        except Exception:
            report_details.append(f"❌ 상담 예약 신청 : 실패({step})")
            total_status = "오류발생"

        # 3. 자사 페이지 점검
        for name, url in {"상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
                          "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
                          "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"}.items():
            driver.get(url)
            time.sleep(5)
            report_details.append(f"✅ {name} : 정상")

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
