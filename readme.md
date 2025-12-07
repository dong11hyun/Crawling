## 2025_11_22 
- project with z

## 크롬 디버깅 모드 실행 
- win + r
- chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_temp"

## 실행후 가상환경에서 
- python bot.py

## 크롤링 중 차단이 발생했을 때, 시크릿 모드나 사용 기록 삭제 후 접속이 된다면 이는 IP 차단이 아닙니다.
- 쿠키 , 캐시 삭제
- 세션 초기화


**Windows:**
```bash
python -m venv venv
가상환경
.\venv\Scripts\activate

가상환경이 켜진 상태(괄호로 (venv)가 보이는 상태)에서 패키지를 설치합니다.
Bash

pip install -r requirements.txt

+ env  # 암호 있을시에만
+ python manage.py migrate
+ python manage.py createsuperuser
# 서버 admin 에서 접속 가능

25_11_27
