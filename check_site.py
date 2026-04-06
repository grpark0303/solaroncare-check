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
    # 네이버 차단을 피하기 위한 모바일 유저 에이전트 설정
    options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url: return f"❌ {name} : 링크 없음"
        try:
            driver.get(url)
            time.sleep(4)
            if "solaroncare" in driver.current_url:
                return f"✅ {name} : 정상"
            else:
                return f"❌ {name} : 연결실패"
        except:
            return f"❌ {name} : 접속불가"

    try:
        # 1. 자사 페이지 점검
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            report_details.append(check_landing(url, name))

        # 2. 네이버 모바일 검색 점검 (솔라온케어 브랜드검색)
        driver.get("https://m.search.naver.com/search.naver?query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(5)
        
        # 사람처럼 보이게 스크롤 살짝 내림
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)

        # 광고 링크만 추출 (adcr.naver.com 포함된 주소들)
        all_links = driver.find_elements(By.TAG_NAME, "a")
        valid_urls = []
        for l in all_links:
            href = l.get_attribute('href')
            if href and "adcr.naver.com" in href:
                if href not in valid_urls:
                    valid_urls.append(href)

        # 영역별 매칭 (메인 + 썸네일 1, 2, 3)
        bsa_names = ["네이버 BSA 메인", "네이버 BSA 썸네일1", "네이버 BSA 썸네일2", "네이버 BSA 썸네일3"]
        for i, name in enumerate(bsa_names):
            if i < len(valid_urls):
                report_details.append(check_landing(valid_urls[i], name))
            else:
                report_details.append(f"❌ {name} : 영역 미발견")

    except Exception as e:
        total_status = "오류발생"
        report_details.append(f"⚠️ 시스템에러: {str(e)[:30]}")
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
