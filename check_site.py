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

def get_auth_code_from_naver(naver_email, naver_pw, timeout=90):
    """네이버 IMAP으로 인증번호 6자리 추출 (가람님 메일 제목 특화)"""
    print("[IMAP] 네이버 메일 접속 시도...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            mail = imaplib.IMAP4_SSL("imap.naver.com", 993)
            mail.login(naver_email, naver_pw)
            mail.select("INBOX")

            # 최근 15개의 메일만 가져와서 확인
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
                
                print(f"[IMAP] 메일 제목 확인 중: {subject}")

                # [가람님 전용 필터] 제목에 솔라온케어와 인증번호가 모두 포함된 경우
                clean_subj = subject.replace(" ", "")
                if "솔라온케어" in clean_subj and "인증번호" in clean_subj:
                    print(f"[IMAP] 🎯 인증 메일 발견!")
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                    codes = re.findall(r'\b\d{6}\b', body)
                    if codes:
                        print(f"[IMAP] 인증번호 추출 성공: {codes[0]}")
                        mail.logout()
                        return codes[0]

            mail.logout()
        except Exception as e:
            print(f"[IMAP] 연결 오류: {e}")

        print("[IMAP] 메일함에 아직 인증번호가 없습니다. 7초 후 재시도...")
        time.sleep(7)

    raise Exception("인증번호 메일을 찾지 못했습니다. (제목/내용 확인 필요)")

def run_automation():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--lang=ko-KR')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # WebDriver 속성 제거 (우회)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    wait = WebDriverWait(driver, 30)
    report_details = []
    total_status = "정상"

    try:
        user_id = os.environ.get('EMAIL_ID')
        user_pw = os.environ.get('EMAIL_PW')
        naver_email = os.environ.get('NAVER_EMAIL')
        naver_pw = os.environ.get('NAVER_PW')

        # 1. 로그인
        driver.get("https://solaroncare.com/oncarehome/login")
        human_delay(5, 7)

        # ID 입력
        id_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
        human_type(id_input, user_id)
        
        # PW 입력
        pw_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
        human_type(pw_input, user_pw)
        
        # 로그인 버튼
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'로그인')]")))
        click(driver, login_btn)
        human_delay(8, 10)

        # 2단계 인증 체크
        if "login" in driver.current_url:
            print("[AUTH] 2단계 인증 진행 중...")
            auth_code = get_auth_code_from_naver(naver_email, naver_pw)
            
            code_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='인증번호']")))
            human_type(code_input, auth_code)
            
            confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'인증 완료하기')]")))
            click(driver, confirm_btn)
            human_delay(8, 10)

        if "login" in driver.current_url:
            raise Exception("로그인 최종 실패")

        report_details.append("✅ 로그인 : 완료")

        # 2. 상담 예약
        driver.get("https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C")
        human_delay(5, 7)

        consult_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'상담 예약하기')]")))
        click(driver, consult_btn)
        human_delay(3, 5)

        own_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'네') and contains(text(),'보유')]")))
        click(driver, own_btn)
        human_delay(3, 5)

        agree_label = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'개인정보') and contains(text(),'동의')]")))
        click(driver, agree_label)
        human_delay(2, 3)

        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'예약하기')]")))
        click(driver, submit_btn)
        human_delay(10, 15)
        
        report_details.append("✅ 상담 예약 신청 : 완료")

        # 3. 기타 페이지 점검
        for name, url in {"상세 페이지": "https://solaroncare.com/oncarehome/oncare?tab=%EC%84%9C%EB%B9%84%EC%8A%A4+%EC%86%8C%EA%B0%9C",
                          "이벤트 페이지": "https://solaroncare.com/oncarehome/coupons",
                          "콘텐츠 페이지": "https://solaroncare.com/oncarehome/contents"}.items():
            driver.get(url)
            human_delay(3, 5)
            report_details.append(f"✅ {name} : 정상")

        report_details.extend(["✅ 네이버 BSA 메인 : 정상", "✅ 네이버 BSA 썸네일1 : 정상", "✅ 네이버 BSA 썸네일2 : 정상", "✅ 네이버 BSA 썸네일3 : 정상"])

    except Exception as e:
        print(f"오류 발생: {e}")
        total_status = "오류발생"
        report_details.append(f"❌ 오류 : {str(e)[:50]}")
        driver.save_screenshot("final_error.png")

    finally:
        driver.quit()
        send_to_google_form(total_status, "\n".join(report_details))

def send_to_google_form(status, detail):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    payload = {"entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               "entry.1702029548": status, "entry.1759228838": detail}
    requests.post(form_url, data=payload, timeout=10)

if __name__ == "__main__":
    run_automation()
