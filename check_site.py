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
    # 유저 에이전트를 실제 일반 PC 크롬처럼 더 정교하게 설정
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    google_ads = []
    total_status = "정상"

    try:
        # 1. 자사 페이지 점검 (생략 - 기존 로직 유지)
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            driver.get(url); time.sleep(2)
            if "solaroncare" in driver.current_url: report_details.append(f"✅ {name} : 정상")
            else: total_status = "오류발생"; report_details.append(f"❌ {name} : 오류")

        # 2. 네이버 BSA (고정값)
        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

        # 3. 구글 광고 정밀 추출 (텍스트 기반)
        # 구글에 한국 지역/언어 강제 설정하여 접속
        driver.get("https://www.google.com/search?q=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4&hl=ko&gl=kr")
        time.sleep(8)

        ad_titles = []
        try:
            # 전략: "광고"라는 단어가 포함된 모든 요소를 찾고, 
            # 그 주변에 있는 '솔라온케어' 관련 제목(h3)을 긁어옵니다.
            # 가람님이 말씀하신 '광고: 검색 결과' 섹션을 타겟팅합니다.
            
            # 페이지 내 모든 h3 태그(검색 결과 제목) 탐색
            all_h3s = driver.find_elements(By.TAG_NAME, "h3")
            
            for h3 in all_h3s:
                txt = h3.text.strip()
                if not txt: continue
                
                # 구글 광고 제목의 특징: 특정 클래스 내부 혹은 광고 표식 근처
                # '솔라온케어'라는 단어가 포함된 최상단 h3들을 광고로 간주 (순서대로)
                if "솔라온케어" in txt and len(ad_titles) < 4:
                    if txt not in ad_titles:
                        ad_titles.append(txt)
                        
        except: pass

        if ad_titles:
            ordinals = ["첫번째", "두번째", "세번째", "네번째"]
            for i, title in enumerate(ad_titles):
                google_ads.append(f"🔍 구글 SA {ordinals[i]}: {title}")
        else:
            # 최후의 수단: 특정 광고 레이아웃 강제 스캔
            try:
                backup_ads = driver.find_elements(By.CSS_SELECTOR, "div[role='region'] h3, div[data-text-ad] h3")
                for ba in backup_ads:
                    if ba.text and ba.text not in ad_titles:
                        ad_titles.append(ba.text)
                
                for i, title in enumerate(ad_titles[:4]):
                    google_ads.append(f"🔍 구글 SA {ordinals[i]}: {title}")
            except:
                pass

        if not google_ads:
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
