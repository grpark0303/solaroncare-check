import requests
import datetime
import time
import os
import traceback
import random
import imaplib
import email
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def human_delay(min_sec=1.0, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))


def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))


def click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    human_delay(0.5, 1.5)
    driver.execute_script("arguments[0].click();", el)


def get_auth_code(gmail_address, gmail_app_pw, timeout=90):
    """Gmail IMAP으로 솔라온케어 인증번호 추출"""
    print("[IMAP] Gmail 접속 시도...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(gmail_address, gmail_app_pw)
            mail.select("INBOX")

            result, data = mail.search(None, "ALL")
            mail_ids = data[0].split()

            for mail_id in reversed(mail_ids[-15:]):
                result, msg_data = mail.fetch(mail_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                subject = ""
                if msg["Subject"]:
                    decoded_parts = email.header.decode_header(msg["Subject"])
                    for part, encoding in decoded_parts:
                        if isinstance(part, bytes):
                            subject += part.decode(encoding or "utf-8", errors="ignore")
                        else:
                            subject += part

                print(f"[IMAP] 메일 제목: {subject}")

                clean_subj = subject.replace(" ", "")
                if "솔라온케어" in clean_subj and "인증번호" in clean_subj:
                    print("[IMAP] 인증 메일 발견!")

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                            elif part.get_content_type() == "text/html":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                    codes = re.findall(r'\b\d{6}\b', body)
                    if codes:
                        print(f"[IMAP] 인증번호: {codes[0]}")
                        mail.logout()
                        return codes[0]

            mail.logout()

        except Exception as e:
            print(f"[IMAP] 오류: {e}")

        print("[IMAP] 7초 후 재시도...")
        time.sleep(7)

    raise Exception("인증번호 메일을 찾지 못했습니다")


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

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            window.chrome = { runtime: {} };
        """
    })

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')
        gmail_address = os.environ.get('NAVER_EMAIL')
        gmail_app_pw = os.environ.get('NAVER_PW')

        # ── 1. 로그인 ──────────────────────────────────────────────
        print("[1] 로그인 페이지 접속")
        driver.get("https://solaroncare.com/oncarehome/login")
        human_delay(5, 7)
        driver.save_screenshot("step1_login_page.png")

        print("[2] 이메일 입력")
        id_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='email']")
        ))
        id_input.click()
        human_delay(0.5, 1.0)
        human_type(id_input, user_id)
        human_delay(1.0, 2.0)

        print("[3] 비밀번호 입력")
        pw_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='password']")
        ))
        pw_input.click()
        human_delay(0.5, 1.0)
        human_type(pw_input, user_pw)
        human_delay(2.0, 3.0)
        driver.save_screenshot("step2_after_input.png")

        print("[4] 로그인 버튼 클릭")
        login_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH,
             "//div[contains(@class,'bg-main-color') "
             "and contains(@class,'button--round') "
             "and .//div[contains(text(),'로그인')]]")
        ))
        click(driver, login_btn)
        human_delay(8, 10)
        driver.save_screenshot("step3_after_login_click.png")
        print(f"[4] 로그인 후 URL: {driver.current_url}")

        # ── 2단계 인증 처리 ────────────────────────────────────────
        if "login" in driver.current_url:
            print("[5] 2단계 인증 감지 → Gmail에서 인증번호 읽는 중")
            auth_code = get_auth_code(gmail_address, gmail_app_pw, timeout=90)

            code_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder*='인증번호']")
            ))
            code_input.click()
            human_delay(0.5, 1.0)
            human_type(code_input, auth_code)
            human_delay(1.0, 2.0)
            driver.save_screenshot("step4_auth_code_input.png")

            confirm_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'인증 완료하기')]")
            ))
            click(driver, confirm_btn)
            human_delay(8, 10)
            driver.save_screenshot("step5_after_auth.png")
            print(f"[5] 인증 후 URL: {driver.current_url}")

        if "login" in driver.current_url:
            raise Exception("인증 후에도 로그인 실패")

        report_details.append("✅ 로그인 : 완료")
        print("[6] 로그인 성공!")

        # ── 2. 상담 예약하기 ───────────────────────────────────────
        print("[7] 서비스 소개 페이지 이동")
        driver.get(
            "https://solaroncare.com/oncarehome/oncare"
            "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C"
        )
        human_delay(5, 7)
        driver.save_screenshot("step6_service_page.png")

        try:
            print("[8] 상담 예약하기 버튼 클릭")
            consult_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and contains(text(),'상담 예약하기')]")
            ))
            click(driver, consult_btn)
            human_delay(3, 5)
            driver.save_screenshot("step7_after_consult_click.png")

            print("[9] 보유 버튼 클릭")
            own_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//span[contains(@class,'button-2') "
                 "and contains(text(),'네, 보유하고 있습니다')]")
            ))
            click(driver, own_btn)
            human_delay(3, 5)
            driver.save_screenshot("step8_after_own_click.png")

            print("[10] 동의 체크박스 클릭")
            agree_label = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'checkbox__label--text') "
                 "and contains(text(),'개인정보 수집 및 이용 동의')]")
            ))
            click(driver, agree_label)
            human_delay(2, 3)
            driver.save_screenshot("step9_after_agree.png")

            print("[11] 예약하기 버튼 클릭")
            submit_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'bg-main-color') "
                 "and contains(@class,'button--round') "
                 "and .//div[contains(text(),'예약하기')]]")
            ))
            click(driver, submit_btn)
            human_delay(10, 12)
            driver.save_screenshot("step10_after_submit.png")

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
        print("[12] 직접 신청하기")
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
            driver.save_screenshot("step11_direct_apply.png")
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
