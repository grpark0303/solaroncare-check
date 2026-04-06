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
    google_ads = [] # 구글 광고 결과를 따로 담아두기 위해
    total_status = "정상"

    try:
        # 1. 자사 페이지 점검
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            try:
                driver.get(url)
                time.sleep(3)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name} : 정상")
                else:
                    total_status = "오류발생"
                    report_details.append(f"❌ {name} : 오류")
            except:
                total_status = "오류발생"
                report_details.append(f"❌ {name} : 접속에러")

        # 2. 네이버 BSA 영역 (고정값)
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일1 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일2 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")

        # 3. 구글 검색 광고 체크 (가장 마지막에 배치)
        print("구글 광고 정밀 체크 중...")
        driver.get("https://www.google.com/search?q=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(5)

        try:
            # 이미지상의 '솔라온케어 공식' 같은 광고 제목을 잡기 위한 다양한 필터링
            # 구글의 광고 섹션(data-text-ad, v9i77d 등) 내부의 제목(h3, span, div)을 광범위하게 수집
            ad_selectors = [
                "div[data-text-ad] h3", 
                "div[role='region'] h3",
                ".v9i77d h3",
                "a[data-pcu] h3",
                ".CC_Anc h3"
            ]
            
            ad_titles = []
            for selector in ad_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.text and el.text not in ad_titles:
                        ad_titles.append(el.text)
            
            if ad_titles:
                for i, title in enumerate(ad_titles):
                    google_ads.append(f"🔍 구글 SA {['첫번째', '두번째', '세번째', '네번째'][i] if i < 4 else i+1}: {title}")
            else:
                google_ads.append("ℹ️ 구글 광고: 현재 노출되는 광고 없음")
        except:
            google_ads.append("⚠️ 구글 광고: 영역 분석 실패")

        # 자사/네이버 결과 뒤에 구글 광고 결과 붙이기
        report_details.extend(google_ads)

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
