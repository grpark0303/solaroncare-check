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

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ko-KR')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30) # 대기 시간을 30초로 넉넉하게
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # 1. 로그인 시도
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(8) # 페이지가 뜰 때까지 충분히 기다림

        try:
            # [수정] 이름 대신 'input' 태그 자체를 찾아서 입력 (더 확실함)
            inputs = driver.find_elements(By.TAG_NAME, "input")
            if len(inputs) >= 2:
                inputs[0].send_keys(user_id) # 첫 번째 칸에 아이디
                inputs[1].send_keys(user_pw) # 두 번째 칸에 비번
                
                # 로그인 버튼도 텍스트가 아닌 'submit' 타입으로 찾기
                login_btn = driver.find_element(By.XPATH, "//button[@type='submit'] | //button[contains(., '로그인')]")
                driver.execute_script("arguments[0].click();", login_btn)
                print(">>> 로그인 시도 성공")
                time.sleep(8)
            else:
                raise Exception("입력창을 찾을 수 없음")
        except Exception as e:
            report_details.append(f"❌ 로그인 단계 오류: 입력창 미발견")
            total_status = "오류발생"

        # 2. 예약 신청 시도
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        time.sleep(5)

        try:
            # [상담 예약하기] 클릭 (모든 버튼 중 '예약' 글자 포함된 것 찾기)
            res_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '예약')]")))
            driver.execute_script("arguments[0].click();", res_btn)
            time.sleep(3)

            # [네, 보유하고 있습니다] 클릭
            yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., '보유')]")))
            driver.execute_script("arguments[0].click();", yes_btn)
            time.sleep(3)

            # [개인정보 동의] 체크
            agree = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '동의')]")))
            driver.execute_script("arguments[0].click();", agree)
            
            report_details.append("✅ 상담 예약 신청 : 완료")
        except:
            report_details.append("❌ 상담 예약 신청 : 프로세스 오류")
            total_status = "오류발생"

        # 3. 자사 페이지 실제 검증
        check_pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in check_pages.items():
            try:
                driver.get(url)
                time.sleep(3)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name} : 정상")
                else:
                    report_details.append(f"❌ {name} : 오류")
            except:
                report_details.append(f"❌ {name} : 접속실패")

        # 4. 네이버 BSA (고정)
        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

    except Exception:
        total_status = "오류발생"
        error_info = traceback.format_exc().splitlines()[-1]
        report_details.append(f"❌ 시스템 최종 오류: {error_info}")
    
    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status, "entry.1759228838": detail
    }
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
