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
    # 유저 에이전트를 최신 버전으로 업데이트하여 일반 브라우저처럼 보이게 함
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    report_details = []
    total_status = "정상"

    def check_landing(url, name):
        if not url: return f"❌ {name} : 링크 없음"
        # 네이버 광고 추적 링크는 requests로 체크하면 차단될 수 있어 직접 접속 시도
        try:
            driver.get(url)
            time.sleep(5) # 페이지가 완전히 뜰 때까지 충분히 대기
            current_url = driver.current_url
            if "solaroncare" in current_url or "naver.com" not in current_url:
                return f"✅ {name} : 정상"
            else:
                return f"❌ {name} : 연결실패"
        except:
            return f"❌ {name} : 접속불가"

    try:
        # 1. 자사 페이지 체크 (이미 잘 되는 부분)
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

        # 2. 네이버 브랜드 검색 체크
        driver.get("https://search.naver.com/search.naver?where=nexearch&query=%EC%86%94%EB%9D%BC%EC%98%A8%EC%BC%80%EC%96%B4")
        time.sleep(5)
        
        # 사람처럼 보이게 스크롤을 살짝 내림
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(3)

        try:
            # 모든 광고 후보 영역 탐색
            bsa = None
            for sel in [".ad_section", ".brand_search", "section.sp_nbrand", ".ns_bsa"]:
                try:
                    targets = driver.find_elements(By.CSS_SELECTOR, sel)
                    for t in targets:
                        if t.is_displayed():
                            bsa = t
                            break
                    if bsa: break
                except: continue

            if bsa:
                # 해당 영역 내 모든 링크 추출
                all_links = bsa.find_elements(By.TAG_NAME, "a")
                valid_urls = []
                for l in all_links:
                    href = l.get_attribute('href')
                    # 광고 신고나 네이버 내부 도움말 링크 등은 필터링
                    if href and "javascript" not in href and "help.naver.com" not in href and "policy.naver.com" not in href:
                        if href not in valid_urls:
                            valid_urls.append(href)

                # 보통 브랜드 검색은 [메인제목, 메인이미지, 썸네일1, 2, 3] 순서로 링크가 잡힙니다.
                # 중복되는 메인 링크를 고려하여 필터링 후 4개 영역 매칭
                names = ["네이버 BSA 메인", "네이버 BSA 썸네일1", "네이버 BSA 썸네일2", "네이버 BSA 썸네일3"]
                
                # 실제 유효한 외부 랜딩 링크만 추출 (네이버 광고 추적 URL 포함)
                final_targets = []
                for url in valid_urls:
                    if "adcr.naver.com" in url: # 네이버 광고 클릭 추적 주소
                        final_targets.append(url)
                
                # 중복 제거 (순서 유지)
                seen = set()
                dedup_targets = [x for x in final_targets if not (x in seen or seen.add(x))]

                for i, name in enumerate(names):
                    if i < len(dedup_targets):
                        report_details.append(check_landing(dedup_targets[i], name))
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
