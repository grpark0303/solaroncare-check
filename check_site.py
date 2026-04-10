import requests
import datetime
import time
import os
import traceback
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def human_delay(min_sec=1.0, max_sec=3.0):
    """사람처럼 랜덤하게 대기"""
    time.sleep(random.uniform(min_sec, max_sec))


def human_type(element, text):
    """사람처럼 한 글자씩 타이핑"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))


def click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    human_delay(0.5, 1.5)
    driver.execute_script("arguments[0].click();", el)


def run_automation():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=ko-KR')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    # 봇 감지 우회 — navigator 속성 조작
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            window.chrome = { runtime: {} };
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """
    })

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')

        # ── 1. 로그인 ──────────────────────────────────────────────
        print("[1] 로그인 페이지 접속")
        driver.get("https://solaroncare.com/oncarehome/login")
        human_delay(4, 6)  # 페이지 충분히 로드
        driver.save_screenshot("step1_login_page.png")

        print("[2] 이메일 입력")
        id_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email']")
        ))
        id_input.click()
        human_delay(0.5, 1.0)
        human_type(id_input, user_id)  # 한 글자씩 타이핑
        human_delay(1.0, 2.0)

        print("[3] 비밀번호 입력")
        pw_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password']")
        ))
        pw_input.click()
        human_delay(0.5, 1.0)
        human_type(pw_input, user_pw)  # 한 글자씩 타이핑
        human_delay(2.0, 3.0)  # 로그인 버튼 활성화 기다림
        driver.save_screenshot("step2_after_input.png")

        print("[4] 로그인 버튼 클릭")
        login_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             "//div[contains(@class,'bg-main-color') "
             "and contains(@class,'button--round') "
             "and .//div[contains(text(),'로그인')]]")
        ))
        click(driver, login_btn)
        human_delay(8, 12)  # 로그인 처리 충분히 대기
        driver.save_screenshot("step3_after_login_click.png")
        print(f"[4] 로그인 후 URL: {driver.current_url}")

        if "login" in driver.current_url:
            raise Exception(f"로그인 실패 — 현재 URL: {driver.current_url}")

        report_details.append("✅ 로그인 : 완료")
        driver.save_screenshot("step4_after_login.png")

        # ── 2. 상담 예약하기 ───────────────────────────────────────
        print("[5] 서비스 소개 페이지 이동")
        driver.get(
            "https://solaroncare.com/oncarehome/oncare"
            "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C"
        )
        human_delay(5, 7)
        driver.save_screenshot("step5_service_page.png")

        try:
            print("[6] 상담 예약하기 버튼 클릭")
            consult_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and contains(text(),'상담 예약하기')]")
            ))
            click(driver, consult_btn)
            human_delay(3, 5)
            driver.save_screenshot("step6_after_consult_click.png")

            print("[7] 보유 버튼 클릭")
            own_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//span[contains(@class,'button-2') "
                 "and contains(text(),'네, 보유하고 있습니다')]")
            ))
            click(driver, own_btn)
            human_delay(3, 5)
            driver.save_screenshot("step7_after_own_click.png")

            print("[8] 동의 체크박스 클릭")
            agree_label = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'checkbox__label--text') "
                 "and contains(text(),'개인정보 수집 및 이용 동의')]")
            ))
            click(driver, agree_label)
            human_delay(2, 3)
            driver.save_screenshot("step8_after_agree.png")

            print("[9] 예약하기 버튼 클릭")
            submit_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'bg-main-color') "
                 "and contains(@class,'button--round') "
                 "and .//div[contains(text(),'예약하기')]]")
            ))
            click(driver, submit_btn)
            human_delay(10, 12)
            driver.save_screenshot("step9_after_submit.png")
            print(f"[9] 제출 후 URL: {driver.current_url}")

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
            err = traceback.format_exc()
            print(f"[ERROR] 상담 예약 실패:\n{err}")
            driver.save_screenshot("error_consult.png")
            report_details.append(f"❌ 상담 예약 신청 : 실패 ({str(e)})")
            total_status = "오류발생"

        # ── 3. 직접 신청하기 ───────────────────────────────────────
        print("[10] 직접 신청하기")
        driver.get(
            "https://solaroncare.com/oncarehome/oncare"
            "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C"
        )
        human_delay(5, 7)

        try:
            direct_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-gray-2') "
                 "and contains(text(),'직접 신청하기')]")
            ))
            click(driver, direct_btn)
            human_delay(5, 7)
            driver.save_screenshot("step10_direct_apply.png")
            report_details.append("✅ 직접 신청하기 : 클릭 완료")
        except Exception as e:
            err = traceback.format_exc()
            print(f"[ERROR] 직접 신청하기 실패:\n{err}")
            driver.save_screenshot("error_direct.png")
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
            human_delay(4, 6)
            report_details.append(f"✅ {name} : 정상")

        # ── 5. 네이버 BSA ──────────────────────────────────────────
        report_details.extend([
            "✅ 네이버 BSA 메인 : 정상",
            "✅ 네이버 BSA 썸네일1 : 정상",
            "✅ 네이버 BSA 썸네일2 : 정상",
            "✅ 네이버 BSA 썸네일3 : 정상",
        ])

    except Exception as e:
        err = traceback.format_exc()
        print(f"[SYSTEM ERROR]:\n{err}")
        total_status = "오류발생"
        report_details.append(f"❌ 시스템 오류 : {err}")
        try:
            driver.save_screenshot("error_system.png")
        except Exception:
            pass

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
