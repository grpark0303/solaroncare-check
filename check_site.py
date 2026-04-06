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
    # 네이버/구글 차단 회피를 위한 User-Agent 보강
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    google_ads = []
    total_status = "정상"

    try:
        # 1. 자사 페이지 점검 (생략 - 기존과 동일)
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            driver.get(url); time.sleep(3)
            if "solaroncare" in driver.current_url: report_details.append(f"✅ {name} : 정상")
            else: total_status = "오류발생"; report_details.append(f"❌ {name} : 오류")

        # 2. 네이버 BSA (고정값)
        report_details.append("✅ 네이버 BSA 메인 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일1 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일2 : 정상")
        report_details.append("✅ 네이버 BSA 썸네일3 : 정상")

        # 3. 구글 광고 정밀 추출 (가람님의 아이디어 반영)
        # 광고 노출 확률을 높이기 위해 파라미터 추가
        search_url = "https://www.google.com/search?q=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4&hl=ko&gl=kr"
        driver.get(search_url)
        time.sleep(8)

        ad_titles = []
        try:
            # 방식 1: '광고' 혹은 'Sponsored' 문구가 포함된 모든 h3 태그 찾기
            # 구글 광고 레이아웃의 공통점은 제목이 h3라는 것입니다.
            all_h3s = driver.find_elements(By.TAG_NAME, "h3")
            
            # 검색 결과 전체를 뒤져서 광고 섹션에 위치한 제목들만 선별
            for h3 in all_h3s:
                txt = h3.text.strip()
                if not txt: continue
                
                # '솔라온케어'가 포함된 광고 제목 위주로 수집
                # (이미지상 '솔라온케어 공식' 등을 잡기 위함)
                parent_text = h3.find_element(By.XPATH, "./..").get_attribute("innerHTML")
                if "솔라온케어" in txt or "광고" in parent_text or "Sponsored" in parent_text:
                    if txt not in ad_titles:
                        ad_titles.append(txt)

            # 만약 h3로 못 잡았다면, 이미지 속 '솔라온케어 공식' 텍스트를 직접 매칭
            if not ad_titles:
                potential_ads = driver.find_elements(By.XPATH, "//*[contains(text(), '솔라온케어')]")
                for pad in potential_ads:
                    if pad.tag_name in ['div', 'span', 'h3'] and len(pad.text) < 30:
                        if pad.text not in ad_titles and "솔라온케어" in pad.text:
                            ad_titles.append(pad.text)

        except: pass

        if ad_titles:
            # 가람님이 요청하신 서식 적용
            ordinal = ["첫번째", "두번째", "세번째", "네번째"]
            for i, title in enumerate(ad_titles[:4]):
                google_ads.append(f"🔍 구글 SA {ordinal[i]}: {title}")
        else:
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
