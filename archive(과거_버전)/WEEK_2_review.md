# Week 2 Review: Airflow 데이터 파이프라인

> Week 2에서 배운 개념, 기술 스택, 코드 리뷰를 정리한 문서  
> 마지막 업데이트: 2026-01-16

---

# 📚 Part 1: 핵심 개념 정리

## 1. Airflow 기본 개념

### DAG (Directed Acyclic Graph)
- **작업 흐름을 코드로 정의**하는 방식
- Task들의 **의존성과 실행 순서**를 표현
- "비순환" = 작업이 순환하지 않음 (A→B→C, C→A는 불가)

### 왜 Airflow인가?
```
기존 방식 (cron):
- 단일 스크립트 실행만 가능
- 실패 시 재시도 어려움
- 모니터링 불가

Airflow 방식:
- 복잡한 워크플로우 정의
- 자동 재시도, 알림
- 웹 UI로 모니터링
```

---

## 2. Airflow 구성 요소

### 핵심 컴포넌트
| 컴포넌트 | 역할 |
|----------|------|
| **Scheduler** | DAG 파싱, Task 스케줄링 |
| **Webserver** | 웹 UI 제공 |
| **Executor** | Task 실행 방식 결정 |
| **Metadata DB** | DAG/Task 상태 저장 |

### Executor 종류
| Executor | 설명 | 사용 환경 |
|----------|------|----------|
| SequentialExecutor | 순차 실행 | 테스트용 |
| **LocalExecutor** | 병렬 실행 (단일 머신) | **우리 프로젝트** |
| CeleryExecutor | 분산 실행 (다중 머신) | 대규모 운영 |
| KubernetesExecutor | K8s Pod으로 실행 | 클라우드 환경 |

---

## 3. XCom (Cross-Communication)

### 개념
- Task 간 **소량 데이터 전달** 메커니즘
- 메타데이터 DB에 저장됨

### 사용 예시
```python
# Task A: 데이터 전달
context['ti'].xcom_push(key='data', value=[1, 2, 3])

# Task B: 데이터 받기
data = context['ti'].xcom_pull(key='data', task_ids='task_a')
```

### 주의점
- **크기 제한** 있음 (기본 48KB)
- 대용량 데이터는 **파일 경로**만 전달

---

## 4. 재시도 (Retry) 전략

### 기본 설정
```python
default_args = {
    'retries': 3,                    # 최대 3번 재시도
    'retry_delay': timedelta(minutes=5),  # 5분 간격
    'retry_exponential_backoff': True,    # 지수 백오프
    'max_retry_delay': timedelta(minutes=30),
}
```

### 지수 백오프 (Exponential Backoff)
```
1차 실패 → 5분 후 재시도
2차 실패 → 10분 후 재시도
3차 실패 → 20분 후 재시도 (최대 30분)
```
- **서버 과부하 방지**에 효과적

---

## 5. SLA (Service Level Agreement)

### 개념
- Task가 **일정 시간 내 완료되지 않으면** 알림 발생

### 설정 예시
```python
task = PythonOperator(
    task_id='crawl_task',
    python_callable=run_crawl,
    sla=timedelta(hours=1),  # 1시간 내 완료 필요
)
```

---

# 🛠️ Part 2: 기술 스택별 역할 및 튜닝

## 1. Airflow

### 역할
- **워크플로우 오케스트레이션**
- 스케줄링, 모니터링, 재시도
- 웹 UI 대시보드

### 튜닝 포인트
```yaml
# docker-compose.yml
environment:
  AIRFLOW__CORE__PARALLELISM: 32        # 전체 동시 Task 수
  AIRFLOW__CORE__DAG_CONCURRENCY: 16    # DAG당 동시 Task 수
  AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG: 1  # DAG 동시 실행 수
  AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL: 30  # DAG 파일 파싱 주기
```

### 타임존 설정
```yaml
AIRFLOW__CORE__DEFAULT_TIMEZONE: Asia/Seoul
AIRFLOW__WEBSERVER__DEFAULT_UI_TIMEZONE: Asia/Seoul
TZ: Asia/Seoul
```

---

## 2. PythonOperator

### 역할
- Python 함수를 Airflow Task로 실행

### 사용 패턴
```python
def my_task(**context):
    # context에서 실행 정보 접근
    execution_date = context['execution_date']
    ti = context['ti']  # TaskInstance
    
    # XCom으로 데이터 전달
    ti.xcom_push(key='result', value=result)
    
    return result  # return 값도 XCom에 저장됨

task = PythonOperator(
    task_id='my_task',
    python_callable=my_task,
    dag=dag,
)
```

---

## 3. 커스텀 Docker 이미지

### 왜 필요한가?
- 기본 Airflow 이미지에 **Playwright 등 추가 라이브러리 없음**
- 필요한 의존성을 포함한 **커스텀 이미지** 빌드 필요

### Dockerfile 구조
```dockerfile
FROM apache/airflow:2.8.0-python3.11

# 시스템 패키지 (root 권한)
USER root
RUN apt-get update && apt-get install -y ...

# Python 패키지 (airflow 권한)
USER airflow
RUN pip install playwright opensearch-py sqlalchemy
RUN playwright install chromium
```

---

# 💻 Part 3: 코드 리뷰

## 1. musinsa_crawl_dag.py

```python
dag = DAG(
    'musinsa_crawl_dag',
    default_args=default_args,
    schedule_interval='0 6 * * *',  # 매일 오전 6시
    catchup=False,                  # 과거 실행 건너뛰기
    max_active_runs=1,              # 동시 실행 방지
)
```

### 리뷰 포인트
- ✅ `catchup=False`로 과거 실행 방지
- ✅ `max_active_runs=1`로 중복 실행 방지
- ✅ cron 표현식으로 스케줄 정의

---

## 2. crawl_task.py (모듈화)

```python
def crawl_musinsa(keyword: str, scroll_count: int, max_products: int):
    """재사용 가능한 크롤링 함수"""
    data = asyncio.run(_crawl_async(...))
    return data
```

### 리뷰 포인트
- ✅ DAG에서 분리된 **독립 모듈**
- ✅ 파라미터로 유연한 설정 가능
- ✅ 단위 테스트 가능

---

## 3. xcom_utils.py

```python
def should_use_file(data: Any) -> bool:
    """데이터 크기에 따라 파일 사용 여부 결정"""
    json_str = json.dumps(data, ensure_ascii=False)
    return len(json_str.encode('utf-8')) > 48000  # 48KB

def save_to_file(data: Any, prefix: str) -> str:
    """대용량 데이터를 파일로 저장"""
    filepath = os.path.join(DATA_DIR, f"{prefix}_{timestamp}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath
```

### 리뷰 포인트
- ✅ XCom 크기 제한 자동 처리
- ✅ 파일 기반 전달로 대용량 지원
- ✅ 자동 정리 기능 (`cleanup_old_files`)

---

# 🎯 Part 4: 면접 대비 Q&A

### Q1. Airflow DAG란?
- **Directed Acyclic Graph**의 약자
- Task들의 **의존성과 실행 순서**를 정의하는 Python 코드
- 스케줄 설정, 재시도 로직 등 포함

### Q2. XCom의 한계와 해결책은?
- **한계**: 크기 제한 (기본 48KB), 메타DB 부담
- **해결책**: 
  - 파일/S3 경로만 전달
  - 외부 저장소 (Redis, S3) 활용

### Q3. Executor 종류와 선택 기준은?
- **LocalExecutor**: 단일 서버, 중소규모
- **CeleryExecutor**: 다중 서버, 대규모
- **KubernetesExecutor**: K8s 환경, 탄력적 확장

### Q4. 재시도 전략에서 지수 백오프란?
- 재시도 간격을 **점점 늘리는** 방식
- 예: 5분 → 10분 → 20분
- **서버 부하 분산** 및 **일시적 장애 복구**에 효과적

### Q5. catchup=False의 의미는?
- DAG 생성 이후 **과거 실행을 건너뜀**
- True면 start_date부터 현재까지 **모든 스케줄 실행**

---

# ✅ Week 2 핵심 역량 체크리스트

| 역량 | 세부 내용 | 습득 |
|------|----------|:----:|
| DAG 작성 | Airflow DAG 정의, 스케줄 설정 | ✅ |
| Task 정의 | PythonOperator, 의존성 설정 | ✅ |
| XCom | Task 간 데이터 전달, 크기 제한 대응 | ✅ |
| 재시도 | retries, 지수 백오프 | ✅ |
| 모듈화 | src/tasks/ 분리, 재사용성 | ✅ |
| 커스텀 이미지 | Dockerfile, Playwright 설치 | ✅ |
| 모니터링 | Airflow UI, 로그 확인 | ✅ |
