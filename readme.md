## 2025_11_22 
- project with z
#### 크롬 디버깅 모드 실행 
- win + r
- chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_temp"

#### 실행후 가상환경에서 
- python bot.py

#### 크롤링 중 차단이 발생했을 때, 시크릿 모드나 사용 기록 삭제 후 접속이 된다면 이는 IP 차단 아님
- 쿠키 , 캐시 삭제
- 세션 초기화


#### 2025_12_19
- python v1.2_safe_crawler.py
[무신사 사이트]
      │
      │ (1. 수집: Python Playwright)
      ▼
[ 데이터 전처리 (ETL) ] ── (2. 가공: 형태소 분석, 정제)
      │
      │ (3. 적재: Bulk Insert)
      ▼
[ OpenSearch (검색 엔진) ] ◀── [ Synonym / Analysis (검색 품질 튜닝) ]
      ▲
      │ (4. 검색/집계 쿼리)
      │
[ FastAPI (백엔드 API) ] ◀── [ Redis (캐싱 - 선택사항) ]
      ▲
      │ (5. REST API 요청)
      │
[ 사용자 / 클라이언트 (Swagger UI) ]