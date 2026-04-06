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
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    
    try:
        # 1. 자사 페이지 (생략 - 기존 로직과 동일)
        # ... (상세/이벤트/콘텐츠 페이지 체크 코드) ...

        # 2. 네이버 모바일 버전으로 접속 (차단 회피 확률 높음)
        driver.get("https://m.search.naver.com/search.naver?query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(7) # 충분히 기다림

        # 네이버 브랜드 검색은 보통 'ad_section' 또는 특정 클래스 내에 존재
        # 모든 <a> 태그 중 외부로 나가는 링크만 추출
        all_links = driver.find_elements(By.TAG_NAME, "a")
        valid_urls = []
        for l in all_links:
            href = l.get_attribute('href')
            if href and "adcr.naver.com" in href: # 네이버 광고 클릭 주소만 수집
                if href not in valid_urls:
                    valid_urls.append(href)

        names = ["네이버 BSA 메인", "네이버 BSA 썸네일1", "네이버 BSA 썸네일2", "네이버 BSA 썸네일3"]
        for i, name in enumerate(names):
            if i < len(valid_urls):
                driver.get(valid_urls[i])
                time.sleep(3)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ {name} : 정상")
                else:
                    report_details.append(f"❌ {name} : 연결실패")
            else:
                report_details.append(f"❌ {name} : 영역 미발견")

    # ... (기존 에러 처리 및 전송 코드) ...
