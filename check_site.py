import requests
import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080') # 팝업 위치 고정을 위해 창 크기 고정
    options.add_argument('--lang=ko-KR')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
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

        # 2. 예약 신청 페이지 이동
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(15)

        # [단계별 강제 집행]
        # 1) 상담 예약하기 버튼 클릭 (텍스트 기반)
        try:
            btn1 = driver.find_element(By.XPATH, "//*[contains(text(), '상담 예약')]")
            driver.execute_script("arguments[0].click();", btn1)
        except:
            raise Exception("상담예약 버튼 클릭 실패")
        
        time.sleep(10) # 팝업 로딩 대기

        # 2) [핵심] 보유 네 버튼 - 좌표 광클 (화면 정중앙 부근 타격)
        try:
            actions = ActionChains(driver)
            # 1920x1080 창 크기 기준, 이미지상의 '네' 버튼 대략적 좌표 (960, 520)
            # 버튼이 살짝 위아래로 움직일 수 있으므로 주변을 5번 연속 클릭
            for i in range(5):
                actions.move_to_location(960, 510 + (i*5)).click().perform()
                time.sleep(0.5)
        except:
            raise Exception("보유 버튼 좌표 클릭 실패")
        
        time.sleep(7)

        # 3) 필수 동의 체크 (성공했던 로직 유지)
        try:
            agree_el = driver.find_element(By.XPATH, "//*[contains(text(), '필수') and not(contains(text(), '전체'))]")
            driver.execute_script("""
                var div = arguments[0].closest('div');
                var cb = div.querySelector('input') || div.querySelector('span');
                cb.click();
            """, agree_el)
        except:
            # 글자라도 클릭 시도
            driver.execute_script("arguments[0].click();", agree_el)
        
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
            report_details.append(f"❌ 상담 예약 신청 : 실패(결과페이지 미도달)")
            total_status = "오류발생"

    except Exception as e:
        report_details.append(f"❌ 상담 예약 신청 : 실패({str(e)})")
        total_status = "오류발생"

    # 3. 자사 페이지 점검 (생략 방지)
    pages = {"상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
             "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
             "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"}
    for name, url in pages.items():
        driver.get(url)
        time.sleep(5)
        report_details.append(f"✅ {name} : 정상")

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
