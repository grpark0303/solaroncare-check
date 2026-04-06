import requests
import datetime
import time
import os
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
    # 한국 사용자처럼 보이게 설정 보강
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ko_KR')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20) # 대기 시간을 20초로 더 늘림
    
    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url: return f"❌ {name} : 링크 없음"
        try:
            driver.get(url)
            time.sleep(4) # 랜딩 페이지 로딩 대기 강화
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

        # 2. 네이버 브랜드 검색 정밀 체크
        search_url = "https://search.naver.com/search.naver?where=nexearch&query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4"
        driver.get(search_url)
        time.sleep(5) # 검색 결과 로딩 대기

        try:
            # 네이버 BSA를 찾는 가장 강력한 방법: 'brand_search'나 'ad_section' 키워드 포함 요소 탐색
            # 여러 개의 선택자를 시도합니다.
            selectors = [
                "div.ad_section", 
                "section.sc_new.sp_nbrand", 
                "div.brand_search",
                "div.ns_bsa"
            ]
            
            bsa_container = None
            for selector in selectors:
                try:
                    bsa_container = driver.find_element(By.CSS_SELECTOR, selector)
                    if bsa_container.is_displayed():
                        break
                except:
                    continue

            if bsa_container:
                # 1) 메인 링크 추출
                main_selectors = ["a.ad_thumb", "a.title_link", "a.info_title", "div.ad_info_area a"]
                main_link = None
                for ms in main_selectors:
                    try:
                        main_link = bsa_container.find_element(By.CSS_SELECTOR, ms).get_attribute('href')
                        if main_link: break
                    except: continue
                
                report_details.append(check_landing(main_link, "네이버 BSA 메인"))

                # 2) 썸네일 링크들 추출
                thumb_elements = bsa_container.find_elements(By.CSS_SELECTOR, "div.thumb_area a, ul.list_thumb a, a.lnk_item")
                
                final_thumbs = []
                for t in thumb_elements:
                    href = t.get_attribute('href')
                    if href and "naver.com" not in href and href not in final_thumbs:
                        final_thumbs.append(href)

                for i in range(3):
                    name = f"네이버 BSA 썸네일{i+1}"
                    if i < len(final_thumbs):
                        report_details.append(check_landing(final_thumbs[i], name))
                    else:
                        report_details.append(f"❌ {name} : 영역 미발견")
            else:
                total_status = "오류발생"
                report_details.append("❌ 네이버 BSA 영역 로딩 실패 (미노출)")

        except Exception as e:
            total_status = "오류발생"
            report_details.append(f"❌ 네이버 BSA 체크 중 에러")

    except Exception as e:
        total_status = "시스템에러"
        report_details.append(f"⚠️ 에러: {str(e)[:40]}")
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
