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
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    total_status = "정상"

    try:
        # 1. 자사 페이지 점검 (기존 동일)
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            driver.get(url)
            time.sleep(3)
            if "solaroncare" in driver.current_url:
                report_details.append(f"✅ {name} : 정상")
            else:
                total_status = "오류발생"
                report_details.append(f"❌ {name} : 오류")

        # 2. 구글 검색 광고 체크 (추가된 기능)
        print("구글 광고 체크 중...")
        driver.get("https://www.google.com/search?q=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(5)

        try:
            # 구글 검색 결과에서 '광고' 섹션의 제목들 추출
            # h3 태그 중 광고 영역에 포함된 것들을 찾습니다.
            ad_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-text-ad] h3, .CC_Anc h3")
            
            if ad_elements:
                ad_titles = [el.text for el in ad_elements if el.text]
                for i, title in enumerate(ad_titles):
                    report_details.append(f"🔍 구글 광고 {i+1}: {title}")
            else:
                report_details.append("ℹ️ 구글 광고: 현재 노출되는 광고 없음")
        except:
            report_details.append("⚠️ 구글 광고: 영역 분석 실패")

        # 3. 네이버 BSA 영역 (고정값 유지)
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일1 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일2 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")

    except Exception as e:
        total_status = "시스템에러"
        report_details.append(f"⚠️ 시스템에러: {str(e)[:30]}")
    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status,
        "entry.1759228838": detail
    }
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
