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
`http://127.0.0.1:8000/docs`
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

#### 2026_01_10
프로젝트 폴더 구성 변경
```
c:\B2_crawling\
│
├── 📁 archive/                         # 🗂️ [새 폴더] 과거 버전 보관소
│   │
│   ├── 📁 coupang/                    # 쿠팡 크롤러들
│   │   ├── v0.9_sync_bot.py          ← 루트에서 이동
│   │   ├── v1.0_async_bot.py         ← 루트에서 이동
│   │   └── v1.1_async_bot.py         ← 루트에서 이동
│   │
│   ├── 📁 musinsa_legacy/            # 무신사 초기 버전
│   │   ├── v2.0_musinsa.py           ← 루트에서 이동
│   │   └── v2.0_MUSINSA_README.md    ← 루트에서 이동
│   │
│   └── 📁 celery_sandbox/            # Celery 분산처리 실험 (v1.2)
│       ├── 📁 config/                ← 루트에서 이동 (폴더 통째로)
│       ├── 📁 crawler/               ← 루트에서 이동 (폴더 통째로)
│       ├── manage.py                 ← 루트에서 이동
│       └── db.sqlite3                ← 루트에서 이동
│
├── 📁 src/                            # ⭐ [새 폴더] 현재 사용하는 메인 코드
│   ├── crawler.py                    ← v2.1_musinsa.py 이름 바꿔서 이동
│   ├── api_server.py                 ← 루트에서 이동
│   └── init_opensearch.py            ← 루트에서 이동
│
├── 📁 frontend/                       # 🌐 [새 폴더] 웹 UI
│   └── index.html                    ← 루트에서 이동
│
├── 📁 docs/                           # 📝 [새 폴더] 문서
│   ├── PROJECT_SUMMARY.md            ← 루트에서 이동
│   ├── (1차최종).md                  ← 루트에서 이동
│   └── readme.md                     ← 루트에서 이동
│
├── 📁 data/                           # 💾 [새 폴더] 데이터 파일
│   └── musinsa_padding_info.csv      ← 루트에서 이동
│
├── docker-compose.yml                 # (루트 유지)
├── requirements.txt                   # (루트 유지)
├── .env                              # (루트 유지)
├── .gitignore                        # (루트 유지)
└── 📁 venv/                          # (루트 유지 - 가상환경)
```