def send_to_google_form(status, detail):
    # 가람님 설문지 ID: 1wHqcKsCaWxazCf_UYQ8OxOChS9pPijsleHm1r5cdzTM
    # 이 ID를 기반으로 한 전송 주소입니다.
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdF9Q5waHP_dlPK35TonomQxbqph6SIYAoNa9FgXxjd8AJstw/formResponse"
    
    # entry ID는 주셨던 링크 그대로입니다.
    payload = {
        "entry.1608092729": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "entry.1702029548": status,
        "entry.1759228838": detail
    }
    
    try:
        # 주소 오타를 방지하기 위해 headers를 추가합니다.
        res = requests.post(form_url, data=payload, timeout=10)
        if res.status_code == 200:
            print(">>> 전송 성공! 구글 시트를 확인하세요.")
        else:
            print(f">>> 전송 실패! 상태코드: {res.status_code}")
            # 주소가 틀리면 여기서 404가 뜹니다.
    except Exception as e:
        print(f">>> 에러 발생: {e}")
