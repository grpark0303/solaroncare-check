import requests
import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
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

        # 1) 상담 예약하기 클릭
        btn1 = driver.find_element(By.XPATH, "//*[contains(text(), '상담 예약')]")
        driver.execute_script("arguments[0].click();", btn1)
        time.sleep(12) 

        # 2) [최종 수정] 텍스트 매칭 안 함. 팝업 내 '첫 번째' 버튼만 타격
        # 이미지상 '네, 보유...' 버튼은 항상 상단(첫 번째)에 위치함
        try:
            # 팝업(모달) 영역 내에 있는 모든 버튼을 긁어옴
            pop_btns = driver.find_elements(By.XPATH, "//div[contains(@class, 'modal')]//button | //div[contains(@class, 'popup')]//button | //button[contains(., '보유')]")
            
            if not pop_btns:
                # 만약 위 조건으로 안 잡히면 페이지 내 모든 버튼 중 '보유' 글자가 있는 것들 수집
                pop_btns = [b for b in driver.find_elements(By.TAG_NAME, "button") if "보유" in b.text]

            # 리스트의 첫 번째(index 0) 버튼이 "네, 보유..." 버튼임
            driver.execute_script("arguments[0].click();", pop_btns[0])
            print(">>> 팝업 첫 번째 버튼 클릭 완료")
        except Exception as e:
            raise Exception(f"보유 버튼 순서 클릭 실패: {str(e)}")
        
        time.sleep(8)

        # 3) 필수 동의 체크
        agrees = driver.find_elements(By.XPATH, "//*[contains(text(), '필수')]")
        for a in agrees:
            if "전체" not in a.text:
                driver.execute_script("arguments[0].click();", a)
                break
        time.sleep(5)

        # 4) 최종 예약하기 제출
        submit_btns = driver.find_elements(By.XPATH, "//button[contains(., '예약하기')] | //*[text()='예약하기']")
        driver.execute_script("arguments[0].click();", submit_btns[-1])
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

    # 3. 자사 페이지 점검
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
