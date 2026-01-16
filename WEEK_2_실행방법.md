# Week 2: Airflow (데이터 파이프라인)

> 동료가 처음부터 따라할 때 **반드시 실행해야 하는 명령어** 모음  
> 마지막 업데이트: 2026-01-16

---

## Day 1: Airflow 환경 구축
- **뭘 하는 건가?**: 워크플로우 관리 시스템(Airflow) Docker 환경 구축
- **왜 필요한가?**: 크롤링 작업을 스케줄링하고 자동화하기 위해

```
Day 1: Airflow 환경 구축
├── [ ] airflow/docker-compose.yml - Airflow 전용 컴포즈
├── [ ] airflow/.env - 환경변수 설정
├── [ ] airflow/dags/ - DAG 파일 저장소
├── [ ] airflow/logs/ - 로그 저장소
└── [ ] airflow/plugins/ - 플러그인 저장소
```

### 1. Airflow 초기화 (최초 1회)
```bash
cd C:\B2_crawling\airflow
docker-compose up airflow-init
```
> ⏳ DB 초기화 및 admin 계정 생성 (1-2분 소요)

### 2. Airflow 서비스 실행
```bash
docker-compose up -d airflow-webserver airflow-scheduler
```

### 3. 컨테이너 상태 확인
```bash
docker ps
```
- `airflow-postgres` ✅
- `airflow-webserver` ✅
- `airflow-scheduler` ✅

### 4. Airflow 웹 UI 접속
- **URL**: http://localhost:8080
- **로그인**: `admin` / `admin`

### 5. 테스트 DAG 실행
1. `test_dag` 찾기
2. 토글 버튼으로 **Unpause** (활성화)
3. ▶️ **Trigger DAG** 클릭
4. 실행 결과 확인 (초록색 = 성공)

---

## Day 2: 무신사 크롤링 DAG 작성
- **뭘 하는 건가?**: 크롤러를 Airflow DAG로 감싸서 자동 실행 가능하게 만들기
- **왜 필요한가?**: 매일 정해진 시간에 자동 크롤링, 실패 시 재시도

```
Day 2: 무신사 크롤링 DAG
├── [x] musinsa_crawl_dag.py - 3단계 파이프라인
│   ├── crawl_task - 크롤링 실행
│   ├── validate_task - 데이터 검증
│   └── load_task - OpenSearch 저장
├── [x] Dockerfile - Playwright 포함 커스텀 이미지
└── [x] docker-compose.yml 수정 - 커스텀 이미지 빌드
```

### 1. Playwright 에러 발생 시
기본 Airflow 이미지에는 Playwright가 없어서 에러 발생:
```
ModuleNotFoundError: No module named 'playwright'
```

### 2. 해결: 커스텀 이미지 빌드
```bash
cd C:\B2_crawling\airflow

# 기존 컨테이너 중지
docker-compose down

# 새 이미지 빌드 (5~10분 소요)
docker-compose build --no-cache

# 재시작
docker-compose up -d
```

### 3. DAG 활성화 및 실행
1. http://localhost:8080 접속
2. `musinsa_crawl_dag` 찾기
3. 토글 버튼으로 **Unpause** (활성화)
4. ▶️ **Trigger DAG** 클릭

### 4. 실행 확인
- Graph 탭에서 Task 흐름 확인:
  ```
  crawl_task → validate_task → load_task
  ```
- 모든 Task가 **초록색** = 성공 ✅
- OpenSearch Dashboards에서 데이터 확인

### 5. 참고사항
- 현재 DAG의 `seller_info`는 간소화됨 (빈 객체)
- Day 3에서 기존 크롤러 로직을 모듈화하여 개선 예정

---

## Day 3: Task 분리 및 모듈화
- **뭘 하는 건가?**: DAG 안의 로직을 별도 모듈로 분리하여 재사용성 향상
- **왜 필요한가?**: 코드 중복 방지, 테스트 용이, 유지보수 편의

```
Day 3: Task 분리 및 모듈화
├── [x] src/tasks/__init__.py - 패키지 초기화
├── [x] src/tasks/crawl_task.py - 크롤링 모듈 (seller_info 추출 포함!)
├── [x] src/tasks/validate_task.py - 검증 모듈
├── [x] src/tasks/load_task.py - 저장 모듈 (PostgreSQL + OpenSearch)
└── [x] musinsa_crawl_dag.py 업데이트 - 모듈 호출 방식으로 변경
```

### 1. 파일 구조
```
src/
└── tasks/
    ├── __init__.py       # 패키지 초기화
    ├── crawl_task.py     # 크롤링 (v2.2 로직 재사용)
    ├── validate_task.py  # 데이터 검증
    └── load_task.py      # 듀얼 저장
```

### 2. 개선된 점
- `seller_info` 완전 수집 (Day 2 문제 해결!)
- 로깅 추가
- 에러 핸들링 강화
- 함수 단위 테스트 가능

### 3. DAG 재실행
```bash
# Airflow가 자동으로 DAG 파일 변경 감지 (1분 내)
# 또는 수동 새로고침: http://localhost:8080 → DAGs → 새로고침
```

### 4. 확인
- Trigger DAG 후 실행
- OpenSearch에서 `seller_info` 필드 확인

---

## Day 4: XCom 데이터 전달
- **뭘 하는 건가?**: Task 간 데이터 전달 최적화 (크기에 따라 XCom / 파일 자동 선택)
- **왜 필요한가?**: XCom은 소량 데이터에 적합, 대용량은 파일 기반이 효율적

```
Day 4: XCom 데이터 전달
├── [x] xcom_utils.py - XCom 유틸리티 (파일 저장/로드, 크기 판단)
├── [x] musinsa_crawl_dag.py v3 업데이트
│   ├── 소량: XCom 직접 전달
│   ├── 대용량: 파일로 저장 → 경로 XCom 전달
│   └── cleanup_task 추가 (7일 이상 파일 삭제)
```

### 1. XCom vs 파일 전달

| 방식 | 조건 | 장점 |
|------|------|------|
| XCom | < 48KB | 간단, 별도 저장소 불필요 |
| 파일 | >= 48KB | 메모리 절약, 대용량 처리 |

### 2. 새 파이프라인 구조
```
crawl_task → validate_task → load_task → cleanup_task
                                          (임시 파일 정리)
```

### 3. 확인
- http://localhost:8080 → DAG 자동 감지 (1분 내)
- Trigger 후 4개 Task 모두 성공 확인

---

## Day 5: 알림 및 재시도 로직 (개념만, 구현 안함)
- **뭘 하는 건가?**: 실패 시 Slack 알림, SLA 설정
- **왜 필요한가?**: 운영 환경에서 장애 빠른 대응

```
Day 5: 알림 및 재시도 (개념 정리)
├── [x] 재시도 전략 - DAG에 이미 구현됨 (retries: 3)
├── [x] 지수 백오프 - retry_exponential_backoff: True
└── [ ] Slack 알림 - (선택사항, Webhook 필요)
```

### 1. 이미 구현된 재시도 설정
```python
default_args = {
    'retries': 3,                          # 최대 3번 재시도
    'retry_delay': timedelta(minutes=5),   # 5분 간격
    'retry_exponential_backoff': True,     # 지수 백오프
    'max_retry_delay': timedelta(minutes=30),
}
```

### 2. Slack 알림 (선택사항)
```python
# 구현하려면 필요한 것:
# 1. Slack 워크스페이스
# 2. Incoming Webhook URL
# 3. on_failure_callback 설정

from airflow.hooks.base import BaseHook
import requests

def slack_alert(context):
    webhook_url = "https://hooks.slack.com/..."
    message = f"❌ 실패: {context['task_instance'].task_id}"
    requests.post(webhook_url, json={"text": message})

default_args['on_failure_callback'] = slack_alert
```

### 3. SLA 설정 (선택사항)
```python
task = PythonOperator(
    task_id='crawl_task',
    python_callable=run_crawl,
    sla=timedelta(hours=1),  # 1시간 내 완료 필요
)
```

---

## 접속 주소 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| Airflow UI | http://localhost:8080 | admin / admin |
| Airflow PostgreSQL | localhost:5432 | airflow DB (내부용) |
| OpenSearch Dashboards | http://localhost:5601 | 검색 데이터 |
| pgAdmin | http://localhost:5050 | PostgreSQL 관리 |
| FastAPI Swagger | http://localhost:8000/docs | API 테스트 |

---

## ✅ Week 2 완료!

```
Week 2: Airflow 데이터 파이프라인
├── [x] Day 1: Airflow 환경 구축
├── [x] Day 2: 무신사 크롤링 DAG
├── [x] Day 3: Task 분리 및 모듈화
├── [x] Day 4: XCom 데이터 전달
└── [x] Day 5: 알림 및 재시도 (개념)
```
