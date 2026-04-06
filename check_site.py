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

    try:
        # --- [3,4,5번] 자사 페이지 노출 체크 ---
        check_urls = {
            "상세페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠페이지": "https://solaroncare.com/oncarehome/contents"
        }
        
        for name, url in check_urls.items():
            try:
                driver.get(url)
                time.sleep(3)
                if "solaroncare" in driver.current_url and len(driver.title) > 0:
                    report_details.append(f"✅ {name}: 접속 정상")
                else:
                    total_status = "오류발생"
                    report_details.append(f"❌ {name}: 접속 실패 또는 빈 페이지")
            except:
                total_status = "오류발생"
                report_details.append(f"❌ {name}: 접속 중 에러")

        # --- [6,7번] 네이버 브랜드검색 체크 ---
        naver_url = "https://search.naver.com/search.naver?query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4"
        driver.get(naver_url)
        time.sleep(3)

        try:
            brand_section = driver.find_element(By.CSS_SELECTOR, ".ad_section")
            report_details.append("✅ 네이버 브랜드검색 영역 노출 확인")
            
            ad_links = brand_section.find_elements(By.TAG_NAME, "a")
            target_urls = []
            for link in ad_links:
                href = link.get_attribute('href')
                if href and "naver.com" not in href and href not in target_urls:
                    target_urls.append(href)
            
            for i, link_url in enumerate(target_urls[:4]):
                driver.get(link_url)
                time.sleep(2)
                if "solaroncare" in driver.current_url:
                    report_details.append(f"✅ 브랜드검색 링크 {i+1} 랜딩 확인")
                else:
                    total_status = "오류발생"
                    report_details.append(f"❌ 브랜드검색 링크 {i+1} 랜딩 실패")
        except:
            total_status = "오류발생"
            report_details.append("❌ 네이버 브랜드검색 영역 찾기 실패")

    except Exception as e:
        total_status = "시스템에러"
        report_details.append(f"⚠️ 실행 중 에러: {str(e)}")
    
    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    # 가람님 설문지 기반 최종 주소 및 ID 수정 완료
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status,
        "entry.1759228838": detail
    }
    
    res = requests.post(form_url, data=payload)
    if res.status_code == 200:
        print("구글 시트 업데이트 완료!")
    else:
        print(f"전송 실패: {res.status_code}")

if __name__ == "__main__":
    run_automation()
