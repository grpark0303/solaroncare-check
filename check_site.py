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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url or "naver.com" in url: return f"❌ {name} : 링크 오류"
        try:
            driver.get(url)
            time.sleep(3)
            if "solaroncare" in driver.current_url:
                return f"✅ {name} : 정상"
            else:
                return f"❌ {name} : 연결실패"
        except:
            return f"❌ {name} : 접속에러"

    try:
        # 1. 자사 페이지 체크
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            report_details.append(check_landing(url, name))

        # 2. 네이버 브랜드 검색 체크 (유연한 추출 방식)
        driver.get("https://search.naver.com/search.naver?where=nexearch&query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(5)

        try:
            # 광고 컨테이너 찾기 (여러 후보군)
            bsa = None
            for selector in [".ad_section", ".brand_search", ".sc_new.sp_nbrand", ".ns_bsa"]:
                try:
                    target = driver.find_element(By.CSS_SELECTOR, selector)
                    if target.is_displayed():
                        bsa = target
                        break
                except: continue

            if bsa:
                # [핵심] 해당 영역 내의 모든 '외부 연결 링크'를 추출
                all_links = bsa.find_elements(By.TAG_NAME, "a")
                valid_urls = []
                for l in all_links:
                    href = l.get_attribute('href')
                    # 네이버 내부 링크나 빈 링크 제외하고 '솔라온케어' 관련 외부 링크만 수집
                    if href and "naver.com" not in href and href not in valid_urls:
                        valid_urls.append(href)

                # 매칭: 0번은 메인, 1/2/3번은 썸네일
                names = ["네이버 BSA 메인", "네이버 BSA 썸네일1", "네이버 BSA 썸네일2", "네이버 BSA 썸네일3"]
                for i, name in enumerate(names):
                    if i < len(valid_urls):
                        report_details.append(check_landing(valid_urls[i], name))
                    else:
                        report_details.append(f"❌ {name} : 영역 미발견")
            else:
                report_details.append("❌ 네이버 BSA : 영역 로딩 실패")

        except Exception as e:
            report_details.append(f"❌ 네이버 BSA : 체크 중 오류")

    except Exception as e:
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
