import requests
import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    total_status = "정상"

    try:
        # --- 자사 페이지 체크 ---
        check_urls = {
            "상세페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠페이지": "https://solaroncare.com/oncarehome/contents"
        }
        
        for name, url in check_urls.items():
            try:
                driver.get(url)
                time.sleep(3)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name}: OK")
                else:
                    total_status = "오류"
                    report_details.append(f"❌ {name}: 실패")
            except:
                total_status = "오류"
                report_details.append(f"❌ {name}: 에러")

        # --- 네이버 브랜드검색 체크 ---
        driver.get("https://search.naver.com/search.naver?query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(3)
        try:
            brand_section = driver.find_element(By.CSS_SELECTOR, ".ad_section")
            report_details.append("✅ 네이버 검색 노출 확인")
        except:
            total_status = "오류"
            report_details.append("❌ 네이버 검색 미노출")

    except Exception as e:
        total_status = "에러"
        report_details.append(f"⚠️ 시스템에러: {str(e)}")
    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    # [수정] 가람님 설문지 ID와 주소 재검증 완료
    # 공백이나 특수문자 오류 방지를 위해 f-string 대신 직접 입력
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status,
        "entry.1759228838": detail
    }
    
    print(f">>> 전송 시도 주소: {form_url}")
    try:
        res = requests.post(form_url, data=payload, timeout=10)
        if res.status_code == 200:
            print(">>> [성공] 구글 시트 업데이트 완료!")
        else:
            print(f">>> [실패] 상태코드: {res.status_code}")
            # 404가 계속 뜬다면 구글 설문지의 ID(주소 중간값)가 정확하지 않은 것입니다.
    except Exception as e:
        print(f">>> [에러] 네트워크 문제: {e}")

if __name__ == "__main__":
    run_automation()
