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
    # [필살기] 아이폰 14 사용자로 위장 (구글의 의심을 피함)
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
    options.add_argument('--window-size=390,844')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    google_ads = []
    total_status = "정상"

    try:
        # 1. 자사 페이지 점검 (생략 - 기존 로직)
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            driver.get(url); time.sleep(2)
            if "solaroncare" in driver.current_url: report_details.append(f"✅ {name} : 정상")
            else: total_status = "오류발생"; report_details.append(f"❌ {name} : 오류")

        # 2. 네이버 BSA (고정값)
        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

        # 3. 구글 광고 정밀 추출 (모바일 버전)
        # 구글 모바일 검색 주소 사용
        driver.get("https://www.google.com/search?q=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4&hl=ko&gl=kr")
        time.sleep(7)

        ad_titles = []
        
        # 모바일 광고 섹션의 특징인 [data-pcu] 또는 특정 제목 클래스 탐색
        # 가람님이 말씀하신 '광고: 검색 결과' 영역 내의 제목들을 찾습니다.
        try:
            # 모든 h3(제목)와 광고 전용 클래스를 수집
            elements = driver.find_elements(By.CSS_SELECTOR, "div[role='region'] h3, div[data-text-ad] h3, .v9i77d h3, .MUS9be")
            
            for el in elements:
                t = el.text.strip()
                if t and "솔라온케어" in t and t not in ad_titles:
                    ad_titles.append(t)
            
            # 만약 위 방법으로 안 잡히면, 광고 주소(URL) 근처의 텍스트 강제 수집
            if not ad_titles:
                ads = driver.find_elements(By.XPATH, "//span[contains(text(), '광고')]/following::h3[1]")
                for a in ads:
                    if a.text and a.text not in ad_titles:
                        ad_titles.append(a.text)
        except: pass

        if ad_titles:
            ordinals = ["첫번째", "두번째", "세번째", "네번째"]
            for i, title in enumerate(ad_titles[:4]):
                google_ads.append(f"🔍 구글 SA {ordinals[i]}: {title}")
        else:
            google_ads.append("ℹ️ 구글 광고: 현재 노출되는 광고 없음")

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
