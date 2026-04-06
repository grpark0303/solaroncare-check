import requests
import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # 봇이 요소를 찾을 때까지 기다려주는 '대기조' 설정
    wait = WebDriverWait(driver, 15) 
    
    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url: return f"❌ {name} : 링크 없음"
        try:
            driver.get(url)
            time.sleep(3)
            if "solaroncare" in driver.current_url:
                return f"✅ {name} : 정상"
            else:
                return f"❌ {name} : 연결실패(URL확인필요)"
        except:
            return f"❌ {name} : 접속에러"

    try:
        # 1. 자사 페이지 체크 (이 부분은 잘 되니 그대로 둡니다)
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            res = check_landing(url, name)
            report_details.append(res)
            if "❌" in res: total_status = "오류발생"

        # 2. 네이버 브랜드 검색 정밀 체크
        driver.get("https://search.naver.com/search.naver?query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        
        try:
            # 광고 영역이 나타날 때까지 최대 15초 대기 (가장 확실한 선택자 사용)
            bsa_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ad_section, section.sc_new.sp_nbrand")))
            time.sleep(2) # 로딩 후 안정화를 위해 2초 더 대기

            # [메인 영역] - 링크 찾기
            main_link = bsa_container.find_element(By.CSS_SELECTOR, "a.ad_thumb, a.title_link, a.info_title").get_attribute('href')
            report_details.append(check_landing(main_link, "네이버 BSA 메인"))

            # [썸네일 영역] - 하단 3개 리스트 찾기
            # 네이버 모바일/PC 버전에 따라 클래스가 다를 수 있어 여러 경로 시도
            thumbnails = bsa_container.find_elements(By.CSS_SELECTOR, ".thumb_area a, .list_thumb a, .lnk_item")
            
            # 실제 썸네일 링크만 필터링 (중복 제거)
            final_thumbs = []
            for t in thumbnails:
                href = t.get_attribute('href')
                if href and "naver.com" not in href and href not in final_thumbs:
                    final_thumbs.append(href)

            for i in range(3):
                name = f"네이버 BSA 썸네일{i+1}"
                if i < len(final_thumbs):
                    report_details.append(check_landing(final_thumbs[i], name))
                else:
                    report_details.append(f"❌ {name} : 영역 미발견")

        except Exception as e:
            total_status = "오류발생"
            report_details.append(f"❌ 네이버 BSA 로딩 실패 (시간 초과)")

    except Exception as e:
        total_status = "시스템에러"
        report_details.append(f"⚠️ 에러: {str(e)[:50]}")
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
