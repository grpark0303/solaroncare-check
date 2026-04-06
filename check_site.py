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
    
    # [핵심] 네이버 차단을 피하기 위한 위장 설정
    options.add_argument("lang=ko_KR")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 봇 감지 우회 스크립트 실행
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })

    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url: return f"❌ {name} : 링크 없음"
        try:
            driver.get(url)
            time.sleep(5) # 랜딩 페이지 로딩 대기
            if "solaroncare" in driver.current_url:
                return f"✅ {name} : 정상"
            else:
                return f"❌ {name} : 연결실패"
        except:
            return f"❌ {name} : 접속불가"

    try:
        # 1. 자사 페이지 점검 (기존 로직 유지)
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

        # 2. 네이버 검색 점검 (가람님이 주신 경로 기반)
        search_url = "https://search.naver.com/search.naver?where=nexearch&query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4"
        driver.get(search_url)
        time.sleep(7) # 검색 결과 로딩 대기
        
        # 화면 스크롤 (실제 사용자처럼 행동)
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(2)

        # 네이버 브랜드 검색 광고 링크(adcr.naver.com) 모두 수집
        all_links = driver.find_elements(By.TAG_NAME, "a")
        valid_urls = []
        for l in all_links:
            href = l.get_attribute('href')
            if href and "adcr.naver.com" in href:
                if href not in valid_urls:
                    valid_urls.append(href)

        # 수집된 링크 매칭 (보통 제목/이미지 중복이 있어 유니크한 링크만 사용)
        bsa_names = ["네이버 BSA 메인", "네이버 BSA 썸네일1", "네이버 BSA 썸네일2", "네이버 BSA 썸네일3"]
        
        # 실제 광고 영역의 링크만 정교하게 필터링
        if len(valid_urls) >= 4:
            for i in range(4):
                report_details.append(check_landing(valid_urls[i], bsa_names[i]))
        else:
            # 링크를 못 찾았다면 화면 캡처 로그 남기기 (디버깅용)
            print(f"발견된 광고 링크 수: {len(valid_urls)}")
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
