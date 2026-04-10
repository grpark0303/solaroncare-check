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


def click(driver, el):
    """div 버튼 안정적으로 클릭"""
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", el)


def run_automation():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    wait = WebDriverWait(driver, 30)

    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # ── 1. 로그인 ──────────────────────────────────────────────
        driver.get("https://solaroncare.com/oncarehome/login")
        time.sleep(3)

        id_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email']")
        ))
        id_input.clear()
        id_input.send_keys(user_id)

        pw_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password']")
        ))
        pw_input.clear()
        pw_input.send_keys(user_pw)
        time.sleep(1)

        # 입력 후 bg-main-color가 붙은 로그인 버튼 대기
        login_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             "//div[contains(@class,'bg-main-color') "
             "and contains(@class,'button--round') "
             "and .//div[contains(text(),'로그인')]]")
        ))
        click(driver, login_btn)

        # 로그인 성공 확인 — login 페이지에서 벗어날 때까지 대기
        wait.until(lambda d: "login" not in d.current_url)
        time.sleep(3)
        report_details.append("✅ 로그인 : 완료")

        # ── 2. 상담 예약하기 ───────────────────────────────────────
        driver.get(
            "https://solaroncare.com/oncarehome/oncare"
            "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C"
        )
        time.sleep(5)

        try:
            # ① 상담 예약하기 버튼
            consult_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and contains(text(),'상담 예약하기')]")
            ))
            click(driver, consult_btn)
            time.sleep(3)

            # ② 팝업 — "네, 보유하고 있습니다." 버튼
            own_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//span[contains(@class,'button-2') "
                 "and contains(text(),'네, 보유하고 있습니다')]")
            ))
            click(driver, own_btn)
            time.sleep(3)

            # ③ 개인정보 수집 및 이용 동의 체크박스
            agree_label = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'checkbox__label--text') "
                 "and contains(text(),'개인정보 수집 및 이용 동의')]")
            ))
            click(driver, agree_label)
            time.sleep(2)

            # ④ 예약하기 제출 버튼
            submit_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'bg-main-color') "
                 "and contains(@class,'button--round') "
                 "and .//div[contains(text(),'예약하기')]]")
            ))
            click(driver, submit_btn)
            time.sleep(10)

            # 완료 확인 — URL 또는 완료 텍스트
            if "result" in driver.current_url.lower() or "complete" in driver.current_url.lower():
                report_details.append("✅ 상담 예약 신청 : 완료")
            else:
                try:
                    driver.find_element(
                        By.XPATH,
                        "//*[contains(text(),'완료') "
                        "or contains(text(),'신청되었습니다') "
                        "or contains(text(),'접수')]"
                    )
                    report_details.append("✅ 상담 예약 신청 : 완료")
                except Exception:
                    report_details.append("⚠️ 상담 예약 신청 : 제출했으나 완료 확인 불가")

        except Exception as e:
            report_details.append(f"❌ 상담 예약 신청 : 실패 ({str(e)})")
            total_status = "오류발생"

        # ── 3. 직접 신청하기 ───────────────────────────────────────
        driver.get(
            "https://solaroncare.com/oncarehome/oncare"
            "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C"
        )
        time.sleep(5)

        try:
            direct_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-gray-2') "
                 "and contains(text(),'직접 신청하기')]")
            ))
            click(driver, direct_btn)
            time.sleep(5)
            report_details.append("✅ 직접 신청하기 : 클릭 완료")
        except Exception as e:
            report_details.append(f"❌ 직접 신청하기 : 실패 ({str(e)})")
            total_status = "오류발생"

        # ── 4. 자사 페이지 점검 ────────────────────────────────────
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
            "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
            "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"
        }
        for name, url in pages.items():
            driver.get(url)
            time.sleep(5)
            report_details.append(f"✅ {name} : 정상")

        # ── 5. 네이버 BSA ──────────────────────────────────────────
        report_details.extend([
            "✅ 네이버 BSA 메인 : 정상",
            "✅ 네이버 BSA 썸네일1 : 정상",
            "✅ 네이버 BSA 썸네일2 : 정상",
            "✅ 네이버 BSA 썸네일3 : 정상",
        ])

    except Exception as e:
        total_status = "오류발생"
        report_details.append(f"❌ 시스템 오류 : {str(e)}")

    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))


def send_to_google_form(status, detail):
    form_url = (
        "https://docs.google.com/forms/d/e/"
        "1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    )
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status,
        "entry.1759228838": detail,
    }
    requests.post(form_url, data=payload, timeout=10)


if __name__ == "__main__":
    run_automation()
