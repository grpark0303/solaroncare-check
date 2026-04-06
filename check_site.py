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
    options.add_argument('--window-size=390,844') # 아이폰 13/14 화면 크기
    
    # [핵심] 아이폰 사용자로 완벽 위장
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
    options.add_argument("lang=ko_KR")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url: return f"❌ {name} : 링크 없음"
        try:
            driver.get(url)
            time.sleep(5)
            if "solaroncare" in driver.current_url:
                return f"✅ {name} : 정상"
            else:
                return f"❌ {name} : 연결실패"
        except:
            return f"❌ {name} : 접속불가"

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
                report_details.append(f"❌ {name} : 오류")

        # 2. [변경] 네이버 모바일 검색으로 우회 접속
        # 모바일 버전은 봇 탐지가 훨씬 약합니다.
        m_search_url = "https://m.search.naver.com/search.naver?query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4"
        driver.get(m_search_url)
        time.sleep(8) # 충분한 로딩 시간
        
        # 스크롤을 내려 광고가 로드되게 함
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # 모든 광고 클릭 링크(adcr.naver.com) 수집
        all_links = driver.find_elements(By.TAG_NAME, "a")
        valid_urls = []
        for l in all_links:
            href = l.get_attribute('href')
            if href and "adcr.naver.com" in href:
                if href not in valid_urls:
                    valid_urls.append(href)

        bsa_names = ["네이버 BSA 메인", "네이버 BSA 썸네일1", "네이버 BSA 썸네일2", "네이버 BSA 썸네일3"]
        
        # 모바일에서도 링크 순서는 거의 동일합니다.
        if len(valid_urls) >= 4:
            for i in range(4):
                report_details.append(check_landing(valid_urls[i], bsa_names[i]))
        elif len(valid_urls) > 0:
            # 링크는 찾았으나 4개가 안 될 경우 가능한 것만 체크
            for i in range(len(valid_urls)):
                if i < 4: report_details.append(check_landing(valid_urls[i], bsa_names[i]))
        else:
            for name in bsa_names:
                report_details.append(f"❌ {name} : 영역 미발견")

    except Exception as e:
        total_status = "오류발생"
        report_details.append(f"⚠️ 에러: {str(e)[:30]}")
    finally:
        driver.quit()
        if any("❌" in r for r in report_details): total_status = "오류발생"
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
