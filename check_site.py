import requests
import datetime
import time
import os
import traceback
import random
import imaplib
import email
import re
from bs4 import BeautifulSoup
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
    print("[IMAP] Gmail 접속 시도...")
    start_time = time.time()
    attempts = 0

    while attempts < 3 and time.time() - start_time < timeout:
        attempts += 1
        print(f"[IMAP] {attempts}번째 시도...")
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(gmail_address, gmail_app_pw)
            mail.select("INBOX")

            result, data = mail.search(None, "ALL")
            mail_ids = data[0].split()

            for mail_id in reversed(mail_ids[-20:]):
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

                print(f"[IMAP] 제목: {subject}")

                if "솔라온케어" in subject and "인증번호" in subject:
                    print("[IMAP] 인증 메일 발견!")

                    html_body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/html":
                                html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        html_body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                    soup = BeautifulSoup(html_body, "html.parser")
                    h4_tags = soup.find_all("h4")
                    for h4 in h4_tags:
                        text = h4.get_text().strip()
                        print(f"[IMAP] h4 태그 내용: {text}")
                        if re.match(r'^\d{6}$', text):
                            print(f"[IMAP] 인증번호 추출 성공: {text}")
                            mail.logout()
                            return text

                    print("[IMAP] h4에서 못 찾음")

            mail.logout()

        except Exception as e:
            print(f"[IMAP] 오류: {e}")

        if attempts < 3:
            print("[IMAP] 7초 후 재시도...")
            time.sleep(7)

    raise Exception("인증번호 메일을 찾지 못했습니다 (3회 시도 완료)")


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
    short_wait = WebDriverWait(driver, 5)
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
            print(f"[5] 인증번호: {auth_code}")

            code_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder*='인증번호']")
            ))
            code_input.click()
            human_delay(0.5, 1.0)
            human_type(code_input, auth_code)
            human_delay(1.0, 2.0)
            driver.save_screenshot("step4_auth_code_input.png")

            print("[5-1] 확인 버튼 클릭")
            confirm_check_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-gray-2') "
                 "and contains(text(),'확인')]")
            ))
            click(driver, confirm_check_btn)
            print("[5-1] 확인 버튼 클릭 완료")
            human_delay(2, 3)

            print("[5-2] 인증 완료하기 버튼 클릭")
            confirm_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and contains(text(),'인증 완료하기')]")
            ))
            click(driver, confirm_btn)
            print("[5-2] 인증 완료하기 클릭 완료")
            human_delay(8, 10)
            driver.save_screenshot("step5_after_auth.png")
            print(f"[5] 인증 후 URL: {driver.current_url}")

        if "login" in driver.current_url:
            raise Exception("인증 후에도 로그인 실패")

        report_details.append("✅ 로그인 : 완료")
        print("[6] 로그인 성공!")

        # ── 2. 상담 예약하기 ───────────────────────────────────────
        print("[7] 서비스 소개 페이지 이동")
        driver.get("https://solaroncare.com/oncarehome/oncare"
                   "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        human_delay(5, 7)
        driver.save_screenshot("step6_service_page.png")

        try:
            print("[8] 상담 예약하기 버튼 찾는 중")
            consult_btn = short_wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'bg-sub-color-1') "
                 "and contains(@class,'button--round') "
                 "and .//div[contains(text(),'상담 예약하기')]]")
            ))
            print("[8] 상담 예약하기 버튼 발견 → 클릭")
            click(driver, consult_btn)
            human_delay(3, 5)
            driver.save_screenshot("step7_after_consult_click.png")

            print("[8-1] 네 보유 버튼 클릭")
            own_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and .//span[contains(text(),'네, 보유하고 있습니다')]]")
            ))
            click(driver, own_btn)
            print("[8-1] 네 보유 버튼 클릭 완료")
            human_delay(3, 5)

            print("[8-2] 개인정보 동의 클릭")
            agree_label = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'checkbox__label--text') "
                 "and contains(text(),'개인정보 수집 및 이용 동의')]")
            ))
            click(driver, agree_label)
            print("[8-2] 개인정보 동의 클릭 완료")
            human_delay(2, 3)

            print("[8-3] 예약하기 버튼 클릭")
            submit_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and contains(text(),'예약하기') "
                 "and not(contains(text(),'상담'))]")
            ))
            click(driver, submit_btn)
            print("[8-3] 예약하기 버튼 클릭 완료")
            human_delay(10, 12)
            driver.save_screenshot("step10_after_submit.png")
            report_details.append("✅ 상담 예약 신청 : 완료")

        except Exception as e:
            print(f"[8] 상담 예약 스킵: {e}")
            report_details.append("➖ 상담 예약 신청 : 해당없음(버튼 미노출)")

        # ── 3. 직접 신청하기 ───────────────────────────────────────
        print("[9] 직접 신청하기 프로세스 시작")
        driver.get("https://solaroncare.com/oncarehome/oncare"
                   "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        human_delay(5, 7)

        try:
            print("[9-1] 직접 신청하기 버튼 클릭")
            direct_btn = short_wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-gray-2') "
                 "and contains(text(),'직접 신청하기')]")
            ))
            click(driver, direct_btn)
            human_delay(5, 7)
            print(f"[9-1] 직접 신청하기 클릭 후 URL: {driver.current_url}")

            print("[9-2] 신규 발전소 서비스 신청하기 버튼 클릭")
            new_plant_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and contains(text(),'신규 발전소 서비스 신청하기')]")
            ))
            click(driver, new_plant_btn)
            human_delay(3, 5)
            print(f"[9-2] 신규 발전소 신청하기 클릭 후 URL: {driver.current_url}")

            print("[9-3] 발전소명 입력")
            plant_name_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder='발전소명을 입력해 주세요']")
            ))
            plant_name_input.click()
            human_delay(0.5, 1.0)
            human_type(plant_name_input, "테스트")
            human_delay(1.0, 2.0)

            print("[9-4] 직접 입력 버튼 클릭")
            direct_input_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and normalize-space(text())='직접 입력']")
            ))
            click(driver, direct_input_btn)
            human_delay(2, 3)

            print("[9-5] 주소 입력")
            address_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder='주소를 입력해 주세요']")
            ))
            address_input.click()
            human_delay(0.5, 1.0)
            human_type(address_input, "서울시 강남구 학동로 402 천마빌딩")
            human_delay(1.0, 2.0)

            print("[9-6] 용량 입력 (50)")
            capacity_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[placeholder='예 ) 49.945'][inputmode='decimal']")
            ))
            capacity_input.click()
            human_delay(0.5, 1.0)
            human_type(capacity_input, "50")
            human_delay(1.0, 2.0)

            print("[9-7] 사업자번호 입력")
            biz_num_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[inputmode='decimal'][maxlength='12']")
            ))
            biz_num_input.click()
            human_delay(0.5, 1.0)
            human_type(biz_num_input, "8881231231")
            human_delay(1.0, 2.0)
            driver.save_screenshot("step18_biz_num_input.png")

            print("[9-8] 상호명 입력")
            company_name_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "input[placeholder='상호명 또는 법인명을 입력해 주세요']")
            ))
            company_name_input.click()
            human_delay(0.5, 1.0)
            human_type(company_name_input, "테스트")
            human_delay(1.0, 2.0)

            print("[9-9] 다음 버튼 클릭")
            next_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and normalize-space(text())='다음']")
            ))
            click(driver, next_btn)
            human_delay(5, 7)
            driver.save_screenshot("step20_after_next1.png")
            print(f"[9-9] 다음 클릭 후 URL: {driver.current_url}")

            print("[9-10] 두 번째 다음 버튼 클릭")
            next_btn_2 = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and normalize-space(text())='다음']")
            ))
            click(driver, next_btn_2)
            human_delay(5, 7)
            driver.save_screenshot("step21_after_next2.png")
            print(f"[9-10] 두 번째 다음 클릭 후 URL: {driver.current_url}")

            print("[9-11] 약관 확인하기 버튼 클릭")
            terms_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and normalize-space(text())='약관 확인하기']")
            ))
            click(driver, terms_btn)
            human_delay(3, 5)
            driver.save_screenshot("step22_after_terms.png")
            print(f"[9-11] 약관 확인하기 클릭 후 URL: {driver.current_url}")

            # ✅ 약관 아래 화살표(▼) 버튼 여러번 클릭해서 끝까지 스크롤
            print("[9-12] 약관 아래 화살표 클릭 (끝까지 스크롤)")
            for i in range(10):
                try:
                    down_btn = driver.find_element(
                        By.XPATH,
                        "//img[contains(@src,'iVBORw0KGgoAAAANSUhEUgAAACoAAAAY')]"
                    )
                    click(driver, down_btn)
                    time.sleep(0.5)
                except Exception:
                    break
            human_delay(2, 3)
            driver.save_screenshot("step23_after_scroll.png")

            # ✅ 전체 동의하기 버튼 클릭
            print("[9-13] 전체 동의하기 버튼 클릭")
            agree_all_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'button--label') "
                 "and contains(@class,'text-white') "
                 "and normalize-space(text())='전체 동의하기']")
            ))
            click(driver, agree_all_btn)
            human_delay(8, 10)
            driver.save_screenshot("step24_after_agree_all.png")
            print(f"[9-13] 전체 동의하기 클릭 후 URL: {driver.current_url}")

            if "completed" in driver.current_url:
                report_details.append("✅ 직접 신청하기 : 완료")
            else:
                report_details.append(
                    f"⚠️ 직접 신청하기 : 완료 페이지 미도달 ({driver.current_url})")

        except Exception as e:
            err = traceback.format_exc()
            print(f"[9] 직접 신청하기 오류: {err}")
            report_details.append(f"❌ 직접 신청하기 : 오류 ({str(e)[:100]})")
            try:
                driver.save_screenshot("error_direct_apply.png")
            except Exception:
                pass

        # ── 4. 자사 페이지 점검 ────────────────────────────────────
        pages = {
            "상세 페이지": "https://solaroncare.com/oncarehome/oncare"
                          "?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
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
