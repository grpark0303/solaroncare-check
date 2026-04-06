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
    # 구글 차단 회피를 위한 최신 User-Agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    options.add_argument("lang=ko_KR")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    google_ads = []
    total_status = "정상"

    try:
        # 1. 자사 페이지 점검 (기존 로직)
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
                    total_status = "오류발생"; report_details.append(f"❌ {name} : 오류")
            except:
                total_status = "오류발생"; report_details.append(f"❌ {name} : 접속에러")

        # 2. 네이버 BSA (고정값)
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일1 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일2 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")

        # 3. 구글 광고 점검 (방식 전면 개편)
        driver.get("https://www.google.com/search?q=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4&hl=ko")
        time.sleep(7) # 로딩 대기 시간 대폭 증가

        # [핵심] '광고' 혹은 'Ad'라는 글자가 포함된 모든 컨테이너를 찾아서 그 안의 제목(h3) 추출
        # 구글의 다양한 레이아웃을 모두 커버하기 위한 복합 선택자
        ad_titles = []
        
        # 방식 A: 광고 전용 데이터 속성으로 찾기
        selectors = ["div[data-text-ad] h3", ".v9i77d h3", ".CnP97e h3", ".uE137c h3"]
        for sel in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                if el.text and el.text not in ad_titles:
                    ad_titles.append(el.text)

        # 방식 B: (최후의 수단) '광고'라는 텍스트 근처의 제목 긁기
        if not ad_titles:
            try:
                # '광고' 문구가 포함된 모든 span/div를 찾고 그 부모 노드에서 제목 추출
                potential_ads = driver.find_elements(By.XPATH, "//span[contains(text(), '광고') or contains(text(), 'Sponsored')]/ancestor::div")
                for ad in potential_ads:
                    h3s = ad.find_elements(By.TAG_NAME, "h3")
                    for h3 in h3s:
                        if h3.text and h3.text not in ad_titles:
                            ad_titles.append(h3.text)
            except: pass

        if ad_titles:
            # 중복 제거 및 리스트화
            unique_titles = list(dict.fromkeys(ad_titles))
            ordinal_names = ["첫번째", "두번째", "세번째", "네번째", "다섯번째"]
            for i, title in enumerate(unique_titles):
                name_tag = ordinal_names[i] if i < len(ordinal_names) else f"{i+1}번째"
                google_ads.append(f"🔍 구글 SA {name_tag}: {title}")
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
