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
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url:
            return f"❌ {name} : 링크 없음"
        try:
            driver.get(url)
            time.sleep(2)
            if "solaroncare" in driver.current_url:
                return f"✅ {name} : 정상"
            else:
                return f"❌ {name} : 연결실패(URL확인필요)"
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
            res = check_landing(url, name)
            report_details.append(res)
            if "❌" in res: total_status = "오류발생"

        # 2. 네이버 브랜드 검색(BSA) 정밀 체크 (빨간 네모 4구역)
        driver.get("https://search.naver.com/search.naver?query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(5)

        try:
            # 브랜드검색 최상위 컨테이너 찾기
            bsa_container = driver.find_element(By.CSS_SELECTOR, ".ad_section, .brand_search")
            
            # [메인 영역] - 보통 큰 이미지나 제목 링크
            main_link = bsa_container.find_element(By.CSS_SELECTOR, ".ad_info_area a, .title_area a").get_attribute('href')
            report_details.append(check_landing(main_link, "네이버 BSA 메인"))

            # [썸네일 영역] - 하단 3개 이미지
            # 네이버 BSA 구조상 썸네일은 보통 특정 클래스 내의 리스트 형태입니다.
            thumbnails = bsa_container.find_elements(By.CSS_SELECTOR, ".thumb_area a, .list_thumb a")
            
            for i in range(3): # 썸네일 1, 2, 3 순서대로
                name = f"네이버 BSA 썸네일{i+1}"
                if i < len(thumbnails):
                    thumb_link = thumbnails[i].get_attribute('href')
                    res = check_landing(thumb_link, name)
                    report_details.append(res)
                else:
                    report_details.append(f"❌ {name} : 영역 미발견")
            
            if any("❌" in r for r in report_details): total_status = "오류발생"

        except Exception as e:
            total_status = "오류발생"
            report_details.append(f"❌ 네이버 BSA 구조 인식 실패 (사유: {str(e)[:30]})")

    except Exception as e:
        total_status = "시스템에러"
        report_details.append(f"⚠️ 에러: {str(e)}")
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
