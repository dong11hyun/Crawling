# 🚀 B2_crawling 프로젝트 확장 구현 계획서

> **목표**: 백엔드 + 데이터 엔지니어링 역량을 결합한 실무 수준 시스템 구축  
> **기간**: 4주 (Week 1 ~ Week 4)  
> **기반**: 현재 `src/` 폴더 (crawler.py, api_server.py, init_opensearch.py)

---

## 📋 상세 구현 일정표

| Week | Day | 날짜 | 단계 | 작업 내용 | 핵심 기술 | 산출물 | 상태 |
|:----:|:---:|:----:|:----:|----------|----------|--------|:----:|
| **1** | 1 | 01/13 | 백엔드 | PostgreSQL 환경 구축 | Docker, PostgreSQL 15 | `docker-compose.yml` PostgreSQL 추가, 연결 테스트 | 🟩 |
| **1** | 2 | 01/14 | 백엔드 | SQLAlchemy 모델 정의 | SQLAlchemy 2.0, Alembic | `database/connection.py`, `database/models.py` (Product, Seller) | 🟩 |
| **1** | 3 | 01/15 | 백엔드 | CRUD API 구현 | FastAPI, Pydantic | `database/schemas.py`, `routers/products.py` (POST/GET/PUT/DELETE) | 🟩 |
| **1** | 4 | 01/16 | 백엔드 | 크롤러-DB 연동 | UPSERT, 트랜잭션 | `crawler.py` 수정 (PostgreSQL + OpenSearch 듀얼 저장) | 🟩 |
| **1** | 5 | 01/17 | 캐싱 | Redis 환경 구축 | Docker, Redis 7 | `docker-compose.yml` Redis 추가, 연결 테스트 | 🟩 |
| **1** | 6 | 01/18 | 캐싱 | 캐싱 로직 구현 | Redis, TTL | `src/cache.py`, `routers/search.py` 캐싱 적용 | 🟩 |
| **1** | 7 | 01/19 | 캐싱 | 캐시 관리 기능 | Cache Invalidation | 캐시 무효화 API, 통계 API, 자동 무효화 | 🟩 |
| 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| **2** | 1 | 01/20 | 파이프라인 | Airflow 환경 구축 | Airflow 2.8, LocalExecutor | `airflow/docker-compose.yml`, 웹 UI 접속 | 🟩 |
| **2** | 2 | 01/21 | 파이프라인 | 첫 번째 DAG 작성 | DAG, PythonOperator | `dags/musinsa_crawl_dag.py` (crawl→validate→load) | 🟩|
| **2** | 3 | 01/22 | 파이프라인 | Task 분리 및 모듈화 | 에러 핸들링, 로깅 | `src/tasks/` 폴더 (crawl_task, validate_task, load_task) | 🟩 |
| **2** | 4 | 01/23 | 파이프라인 | XCom 데이터 전달 | XCom, 대용량 데이터 | Task 간 데이터 전달, 파일/S3 경로 전달 | 🟩 |
| **2** | 5 | 01/24 | 파이프라인 | 알림 및 재시도 로직 | Slack, Retry, SLA | 실패 알림, 지수 백오프 재시도, SLA 설정 | 🟩 |
| 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| **3** | 1 | 01/27 | 실시간 | Kafka 환경 구축 | Kafka, Zookeeper | `docker-compose.yml` Kafka 추가, Topic 생성 | 🟩 |
| **3** | 2 | 01/28 | 실시간 | Python 클라이언트 설정 | kafka-python | Kafka 연결 테스트, Kafka UI 확인 | 🟩 |
| **3** | 3 | 01/29 | 실시간 | Producer 구현 | KafkaProducer | `src/kafka/producer.py`, 크롤러 Kafka 발행 연동 | 🟩 |
| **3** | 4 | 01/30 | 실시간 | Consumer 구현 | KafkaConsumer, Consumer Group | `consumer_postgres.py`, `consumer_opensearch.py` | 🟩 |
| **3** | 5 | 01/31 | 실시간 | 크롤러 Kafka 연동 + DLQ 개념 | Producer 연동, DLQ 이해 | Airflow DAG → Kafka 발행, DLQ 개념 정리 | ⬜ |
| 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| **4** | 1 | 02/03 | 인프라 | Dockerfile 작성 | Docker, Playwright | `Dockerfile` (API), `Dockerfile.crawler` (크롤러) | ⬜ |
| **4** | 2 | 02/04 | 인프라 | 이미지 빌드 및 테스트 | Docker Compose, Registry | 로컬 빌드 테스트, Docker Hub 푸시 | ⬜ |
| **4** | 3 | 02/05 | 배포 | K8s 기본 리소스 배포 | Namespace, Deployment, Service | `k8s/namespace.yaml`, `k8s/api/` (deployment, service) | ⬜ |
| **4** | 4 | 02/06 | 배포 | CronJob + StatefulSet | CronJob, StatefulSet | `k8s/crawler/cronjob.yaml`, PostgreSQL/OpenSearch StatefulSet | ⬜ |
| **4** | 5 | 02/07 | 배포 | ConfigMap, Secret, Ingress | K8s 설정 관리 | 환경 설정, 비밀번호 관리, 외부 접속 설정 | ⬜ |
| **4** | 6 | 02/08 | CI/CD | GitHub Actions 설정 | GitHub Actions | `.github/workflows/ci.yaml` (빌드→푸시→배포) | ⬜ |
| **4** | 7 | 02/09 | CI/CD | 배포 전략 + 최종 테스트 | Rolling Update, HPA, Probe | Health Check, 오토스케일링, E2E/부하 테스트 | ⬜ |

### 📊 주차별 요약

| Week | 주제 | 핵심 기술 | 최종 산출물 |
|:----:|------|----------|------------|
| **1** | 백엔드 기본 + 심화 | PostgreSQL, SQLAlchemy, Redis | CRUD API + 캐싱 시스템 |
| **2** | 데이터 파이프라인 | Airflow | DAG 기반 스케줄링 크롤러 |
| **3** | 실시간 처리 | Kafka | 이벤트 드리븐 파이프라인 |
| **4** | 인프라 & 배포 | Docker, Kubernetes, CI/CD | 프로덕션 배포 환경 |

### 🎯 진행 상태 범례
- ⬜ 미착수
- 🔄 진행 중
- ✅ 완료
- ❌ 보류/취소

---

# Week 1: PostgreSQL + Redis (백엔드)

## 1-1. PostgreSQL + CRUD API (Day 1~4)

### 📌 목표
- 크롤링 원본 데이터를 PostgreSQL에 저장
- FastAPI + SQLAlchemy ORM으로 CRUD API 구현
- OpenSearch는 **검색 전용**, PostgreSQL은 **원본 저장소** (듀얼 저장 구조)

### 🏗️ 아키텍처 변경
```
[크롤러]
    │
    ├──→ [PostgreSQL] ─ 원본 데이터 저장 (Source of Truth)
    │         │
    │         └──→ [CRUD API] ─ 데이터 관리
    │
    └──→ [OpenSearch] ─ 검색용 인덱스 (검색 최적화)
```

### 📁 파일 구조 변경
```
src/
├── crawler.py
├── api_server.py        # 기존 (검색 API)
├── init_opensearch.py
│
├── 📁 database/         # [신규]
│   ├── __init__.py
│   ├── connection.py    # DB 연결 설정
│   ├── models.py        # SQLAlchemy 모델
│   └── schemas.py       # Pydantic 스키마
│
└── 📁 routers/          # [신규]
    ├── __init__.py
    ├── search.py        # 기존 검색 로직 분리
    └── products.py      # CRUD API
```

### ✅ 체크리스트

#### Day 1: PostgreSQL 환경 구축
- [ ] `docker-compose.yml`에 PostgreSQL 추가
  ```yaml
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: crawler
      POSTGRES_PASSWORD: password
      POSTGRES_DB: musinsa_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  ```
- [ ] pgAdmin 컨테이너 추가 (선택)
- [ ] PostgreSQL 컨테이너 실행 및 연결 테스트

#### Day 2: SQLAlchemy 모델 정의
- [ ] `requirements.txt`에 의존성 추가
  ```
  sqlalchemy==2.0.23
  psycopg2-binary==2.9.9
  alembic==1.13.1
  ```
- [ ] `database/connection.py` 작성
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker, declarative_base
  
  DATABASE_URL = "postgresql://crawler:password@localhost:5432/musinsa_db"
  engine = create_engine(DATABASE_URL)
  SessionLocal = sessionmaker(bind=engine)
  Base = declarative_base()
  ```
- [ ] `database/models.py` 작성
  ```python
  class Product(Base):
      __tablename__ = "products"
      
      id = Column(Integer, primary_key=True)
      url = Column(String, unique=True, index=True)
      title = Column(String)
      brand = Column(String, index=True)
      price = Column(Integer)
      created_at = Column(DateTime, default=datetime.utcnow)
      updated_at = Column(DateTime, onupdate=datetime.utcnow)
  
  class Seller(Base):
      __tablename__ = "sellers"
      
      id = Column(Integer, primary_key=True)
      product_id = Column(Integer, ForeignKey("products.id"))
      company = Column(String)
      contact = Column(String)
      email = Column(String)
  ```

#### Day 3: CRUD API 구현
- [ ] `database/schemas.py` Pydantic 스키마 작성
- [ ] `routers/products.py` CRUD 엔드포인트 구현
  ```
  POST   /products      - 상품 생성
  GET    /products      - 상품 목록 조회 (페이지네이션)
  GET    /products/{id} - 상품 상세 조회
  PUT    /products/{id} - 상품 수정
  DELETE /products/{id} - 상품 삭제
  ```
- [ ] `api_server.py`에 라우터 등록

#### Day 4: 크롤러 연동
- [ ] `crawler.py` 수정: PostgreSQL + OpenSearch 듀얼 저장
  ```python
  # 1. PostgreSQL에 원본 저장
  db_product = Product(url=url, title=title, ...)
  session.add(db_product)
  session.commit()
  
  # 2. OpenSearch에 검색용 인덱싱
  helpers.bulk(client, docs)
  ```
- [ ] 중복 데이터 처리 로직 (UPSERT)
- [ ] 트랜잭션 롤백 처리

### 🧪 검증 항목
- [ ] PostgreSQL 데이터 저장 확인 (pgAdmin)
- [ ] CRUD API Swagger 테스트 (`/docs`)
- [ ] OpenSearch 동기화 확인

---

## 1-2. Redis 캐싱 (Day 5~7)

### 📌 목표
- 검색 결과 캐싱으로 응답 속도 개선
- TTL(Time To Live) 기반 캐시 만료 관리
- 캐시 히트율 모니터링

### 🏗️ 아키텍처 변경
```
[클라이언트 요청]
        │
        ▼
    [FastAPI]
        │
        ├──→ [Redis] ─ 캐시 히트? → 즉시 반환 (빠름!)
        │         │
        │         └─ 캐시 미스? ─┐
        │                       │
        └──────────────────────→ [OpenSearch] ─ 검색 실행
                                      │
                                      └──→ [Redis 저장] ─ 다음 요청 대비
```

### ✅ 체크리스트

#### Day 5: Redis 환경 구축
- [ ] `docker-compose.yml`에 Redis 추가
  ```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
  ```
- [ ] `requirements.txt`에 추가
  ```
  redis==5.0.1
  ```
- [ ] Redis 연결 테스트

#### Day 6: 캐싱 로직 구현
- [ ] `src/cache.py` 작성
  ```python
  import redis
  import json
  
  redis_client = redis.Redis(host='localhost', port=6379, db=0)
  
  def get_cache(key: str):
      data = redis_client.get(key)
      return json.loads(data) if data else None
  
  def set_cache(key: str, value: dict, ttl: int = 300):
      redis_client.setex(key, ttl, json.dumps(value))
  
  def generate_cache_key(keyword: str, min_price: int, max_price: int):
      return f"search:{keyword}:{min_price}:{max_price}"
  ```
- [ ] `routers/search.py` 캐싱 적용
  ```python
  @app.get("/search")
  def search_products(keyword: str, ...):
      cache_key = generate_cache_key(keyword, min_price, max_price)
      
      # 1. 캐시 확인
      cached = get_cache(cache_key)
      if cached:
          return cached  # 캐시 히트!
      
      # 2. 캐시 미스 → OpenSearch 검색
      results = opensearch_search(keyword, ...)
      
      # 3. 결과 캐싱
      set_cache(cache_key, results, ttl=300)  # 5분
      
      return results
  ```

#### Day 7: 캐시 관리 기능
- [ ] 캐시 무효화 API 추가
  ```
  DELETE /cache/{keyword}  - 특정 키워드 캐시 삭제
  DELETE /cache/all        - 전체 캐시 삭제
  ```
- [ ] 캐시 통계 API (히트율 등)
- [ ] 상품 업데이트 시 관련 캐시 자동 무효화

### 🧪 검증 항목
- [ ] 첫 번째 요청 vs 두 번째 요청 응답 시간 비교
- [ ] Redis CLI로 캐시 데이터 확인 (`redis-cli GET search:패딩:0:0`)
- [ ] TTL 만료 후 캐시 갱신 확인

---

# Week 2: Airflow (데이터 엔지니어링)

## 2-1. Airflow 기본 설정 (Day 1~2)

### 📌 목표
- Airflow 환경 구축 (Docker)
- 크롤링 작업을 DAG로 스케줄링
- 성공/실패 알림 설정

### 🏗️ 아키텍처 변경
```
┌─────────────────────────────────────────────────┐
│                  [Airflow]                       │
│  ┌─────────────────────────────────────────────┐ │
│  │            musinsa_crawl_dag                │ │
│  │                                             │ │
│  │  [start] → [crawl] → [validate] → [load]   │ │
│  │              │            │          │      │ │
│  │              ▼            ▼          ▼      │ │
│  │          무신사       품질검증    PostgreSQL │ │
│  │          크롤링                  OpenSearch │ │
│  └─────────────────────────────────────────────┘ │
│                      │                           │
│                 [Scheduler]                      │
│              매일 오전 6시 실행                   │
└─────────────────────────────────────────────────┘
```

### 📁 폴더 구조
```
B2_crawling/
├── 📁 airflow/              # [신규]
│   ├── docker-compose.yml   # Airflow 전용
│   ├── 📁 dags/
│   │   └── musinsa_crawl_dag.py
│   ├── 📁 plugins/
│   └── 📁 logs/
│
├── 📁 src/
│   ├── crawler.py           # Airflow에서 호출
│   └── ...
```

### ✅ 체크리스트

#### Day 1: Airflow 환경 구축
- [ ] `airflow/docker-compose.yml` 작성
  ```yaml
  version: '3'
  services:
    airflow-webserver:
      image: apache/airflow:2.8.0
      environment:
        - AIRFLOW__CORE__EXECUTOR=LocalExecutor
        - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      volumes:
        - ./dags:/opt/airflow/dags
        - ./logs:/opt/airflow/logs
        - ../src:/opt/airflow/src  # 크롤러 마운트
      ports:
        - "8080:8080"
      command: webserver
    
    airflow-scheduler:
      image: apache/airflow:2.8.0
      volumes:
        - ./dags:/opt/airflow/dags
        - ./logs:/opt/airflow/logs
        - ../src:/opt/airflow/src
      command: scheduler
    
    postgres:
      image: postgres:13
      environment:
        - POSTGRES_USER=airflow
        - POSTGRES_PASSWORD=airflow
        - POSTGRES_DB=airflow
  ```
- [ ] Airflow 초기화 (`airflow db init`)
- [ ] 웹 UI 접속 확인 (`http://localhost:8080`)

#### Day 2: 첫 번째 DAG 작성
- [ ] `dags/musinsa_crawl_dag.py` 작성
  ```python
  from airflow import DAG
  from airflow.operators.python import PythonOperator
  from datetime import datetime, timedelta
  
  default_args = {
      'owner': 'data-engineer',
      'depends_on_past': False,
      'start_date': datetime(2026, 1, 1),
      'retries': 3,
      'retry_delay': timedelta(minutes=5),
  }
  
  dag = DAG(
      'musinsa_crawl_dag',
      default_args=default_args,
      description='무신사 상품 데이터 수집',
      schedule_interval='0 6 * * *',  # 매일 오전 6시
      catchup=False,
  )
  
  def run_crawler():
      # src/crawler.py 실행 로직
      pass
  
  def validate_data():
      # 데이터 품질 검증
      pass
  
  def load_to_db():
      # PostgreSQL + OpenSearch 적재
      pass
  
  t1 = PythonOperator(task_id='crawl', python_callable=run_crawler, dag=dag)
  t2 = PythonOperator(task_id='validate', python_callable=validate_data, dag=dag)
  t3 = PythonOperator(task_id='load', python_callable=load_to_db, dag=dag)
  
  t1 >> t2 >> t3
  ```

---

## 2-2. DAG 고도화 (Day 3~5)

### ✅ 체크리스트

#### Day 3: Task 분리 및 모듈화
- [ ] `src/tasks/` 폴더 생성
  ```
  src/tasks/
  ├── __init__.py
  ├── crawl_task.py      # 크롤링 로직
  ├── validate_task.py   # 검증 로직
  └── load_task.py       # 적재 로직
  ```
- [ ] 각 Task를 독립적으로 테스트 가능하게 분리
- [ ] 에러 핸들링 및 로깅 추가

#### Day 4: XCom을 활용한 Task 간 데이터 전달
- [ ] 크롤링 결과를 XCom으로 다음 Task에 전달
  ```python
  def run_crawler(**context):
      data = crawl_musinsa()
      context['ti'].xcom_push(key='crawled_data', value=data)
  
  def validate_data(**context):
      data = context['ti'].xcom_pull(key='crawled_data', task_ids='crawl')
      # 검증 로직
  ```
- [ ] 대용량 데이터는 파일/S3로 저장 후 경로만 전달

#### Day 5: 알림 및 재시도 로직
- [ ] Slack 알림 연동 (선택)
  ```python
  from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
  
  def on_failure_callback(context):
      slack_msg = f"❌ Task 실패: {context['task_instance'].task_id}"
      # Slack 전송
  ```
- [ ] 재시도 전략 설정
  ```python
  default_args = {
      'retries': 3,
      'retry_delay': timedelta(minutes=5),
      'retry_exponential_backoff': True,
      'max_retry_delay': timedelta(minutes=30),
  }
  ```
- [ ] SLA 설정 (Task 지연 알림)

### 🧪 검증 항목
- [ ] DAG 수동 실행 테스트
- [ ] Task 실패 시 재시도 동작 확인
- [ ] 스케줄 실행 확인 (오전 6시)
- [ ] 알림 수신 확인

---

# Week 3: Kafka (실시간 파이프라인)

## 3-1. Kafka 환경 구축 (Day 1~2)

### 📌 목표
- Kafka 클러스터 구축
- Producer: 크롤러에서 데이터 발행
- Consumer: OpenSearch/PostgreSQL에 적재

### 🏗️ 아키텍처 변경
```
[크롤러 (Producer)]
        │
        │ publish
        ▼
┌─────────────────────────────────────────┐
│          [Kafka Cluster]                 │
│  ┌─────────────────────────────────────┐ │
│  │     Topic: musinsa.products         │ │
│  │     Partitions: 3                   │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
        │
        │ consume
        ▼
┌───────────────────────────────────────┐
│           [Consumers]                  │
│  ┌──────────────┐  ┌────────────────┐ │
│  │ PostgreSQL   │  │  OpenSearch    │ │
│  │  Consumer    │  │   Consumer     │ │
│  └──────────────┘  └────────────────┘ │
└───────────────────────────────────────┘
```

### ✅ 체크리스트

#### Day 1: Kafka 환경 구축
- [ ] `docker-compose.yml`에 Kafka 추가
  ```yaml
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
  
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8090:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
  ```
- [ ] Topic 생성
  ```bash
  kafka-topics --create --topic musinsa.products --partitions 3 --replication-factor 1
  ```
- [ ] Kafka UI 접속 확인 (`http://localhost:8090`)

#### Day 2: Python 클라이언트 설정
- [ ] `requirements.txt`에 추가
  ```
  kafka-python==2.0.2
  # 또는
  confluent-kafka==2.3.0
  ```
- [ ] 연결 테스트

---

## 3-2. Producer/Consumer 구현 (Day 3~5)

### ✅ 체크리스트

#### Day 3: Producer 구현 (크롤러 수정)
- [ ] `src/kafka/producer.py` 작성
  ```python
  from kafka import KafkaProducer
  import json
  
  producer = KafkaProducer(
      bootstrap_servers=['localhost:9092'],
      value_serializer=lambda v: json.dumps(v).encode('utf-8')
  )
  
  def send_product(product_data: dict):
      producer.send('musinsa.products', value=product_data)
      producer.flush()
  ```
- [ ] `crawler.py` 수정: 직접 저장 → Kafka 발행
  ```python
  # 기존: DB 직접 저장
  # 변경: Kafka로 발행
  for product in crawled_products:
      send_product(product)
  ```

#### Day 4: Consumer 구현
- [ ] `src/kafka/consumer_postgres.py`
  ```python
  from kafka import KafkaConsumer
  import json
  
  consumer = KafkaConsumer(
      'musinsa.products',
      bootstrap_servers=['localhost:9092'],
      group_id='postgres-consumer',
      value_deserializer=lambda m: json.loads(m.decode('utf-8'))
  )
  
  for message in consumer:
      product = message.value
      save_to_postgres(product)
  ```
- [ ] `src/kafka/consumer_opensearch.py`
  ```python
  consumer = KafkaConsumer(
      'musinsa.products',
      group_id='opensearch-consumer',
      ...
  )
  
  for message in consumer:
      product = message.value
      index_to_opensearch(product)
  ```

#### Day 5: Consumer Group 및 에러 처리
- [ ] Consumer Group 설정 (병렬 처리)
- [ ] Dead Letter Queue (DLQ) 구현
  ```python
  try:
      process_message(message)
  except Exception as e:
      # 처리 실패 시 DLQ로 전송
      producer.send('musinsa.products.dlq', value=message.value)
  ```
- [ ] Offset 관리 (at-least-once / exactly-once)

### 🧪 검증 항목
- [ ] Producer → Kafka UI에서 메시지 확인
- [ ] Consumer 실행 후 DB/OpenSearch 데이터 확인
- [ ] Consumer 중지 후 재시작 시 Offset 복구 확인

---

# Week 4: Kubernetes 배포 (인프라)

## 4-1. Docker 이미지 빌드 (Day 1~2)

### 📌 목표
- 각 컴포넌트를 컨테이너화
- Docker Hub 또는 Private Registry에 푸시

### ✅ 체크리스트

#### Day 1: Dockerfile 작성
- [ ] `src/Dockerfile` (API 서버)
  ```dockerfile
  FROM python:3.11-slim
  
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  
  COPY . .
  
  EXPOSE 8000
  CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- [ ] `src/Dockerfile.crawler` (크롤러)
  ```dockerfile
  FROM python:3.11-slim
  
  # Playwright 의존성
  RUN apt-get update && apt-get install -y \
      libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1
  
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  RUN playwright install chromium
  
  COPY . .
  
  CMD ["python", "crawler.py"]
  ```

#### Day 2: 이미지 빌드 및 테스트
- [ ] 로컬 빌드 테스트
  ```bash
  docker build -t musinsa-api:v1 -f Dockerfile .
  docker build -t musinsa-crawler:v1 -f Dockerfile.crawler .
  ```
- [ ] Docker Compose로 통합 테스트
- [ ] Registry 푸시 (Docker Hub / ghcr.io)

---

## 4-2. Kubernetes 매니페스트 작성 (Day 3~5)

### 📁 폴더 구조
```
k8s/
├── namespace.yaml
├── 📁 api/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── 📁 crawler/
│   └── cronjob.yaml
├── 📁 kafka/
│   ├── zookeeper.yaml
│   └── kafka.yaml
├── 📁 database/
│   ├── postgres.yaml
│   ├── redis.yaml
│   └── opensearch.yaml
└── 📁 monitoring/
    └── prometheus.yaml
```

### ✅ 체크리스트

#### Day 3: 기본 리소스 배포
- [ ] Namespace 생성
  ```yaml
  apiVersion: v1
  kind: Namespace
  metadata:
    name: musinsa
  ```
- [ ] API Server Deployment + Service
  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: musinsa-api
    namespace: musinsa
  spec:
    replicas: 3
    selector:
      matchLabels:
        app: musinsa-api
    template:
      metadata:
        labels:
          app: musinsa-api
      spec:
        containers:
        - name: api
          image: musinsa-api:v1
          ports:
          - containerPort: 8000
          env:
          - name: DATABASE_URL
            valueFrom:
              secretKeyRef:
                name: db-secret
                key: url
  ```

#### Day 4: CronJob + StatefulSet
- [ ] Crawler CronJob (매일 오전 6시)
  ```yaml
  apiVersion: batch/v1
  kind: CronJob
  metadata:
    name: musinsa-crawler
  spec:
    schedule: "0 6 * * *"
    jobTemplate:
      spec:
        template:
          spec:
            containers:
            - name: crawler
              image: musinsa-crawler:v1
            restartPolicy: OnFailure
  ```
- [ ] PostgreSQL StatefulSet
- [ ] OpenSearch StatefulSet

#### Day 5: ConfigMap, Secret, Ingress
- [ ] ConfigMap (설정 값)
- [ ] Secret (비밀번호, API 키)
- [ ] Ingress (외부 접속)
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: Ingress
  metadata:
    name: musinsa-ingress
  spec:
    rules:
    - host: api.musinsa.local
      http:
        paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: musinsa-api
              port:
                number: 8000
  ```

---

## 4-3. CI/CD 파이프라인 (Day 6~7)

### ✅ 체크리스트

#### Day 6: GitHub Actions 설정
- [ ] `.github/workflows/ci.yaml`
  ```yaml
  name: CI/CD Pipeline
  
  on:
    push:
      branches: [main]
  
  jobs:
    build:
      runs-on: ubuntu-latest
      steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker Image
        run: docker build -t musinsa-api:${{ github.sha }} .
      
      - name: Push to Registry
        run: docker push ...
      
      - name: Deploy to K8s
        run: kubectl set image deployment/musinsa-api api=musinsa-api:${{ github.sha }}
  ```

#### Day 7: 배포 전략 설정
- [ ] Rolling Update 설정
- [ ] Health Check (Liveness/Readiness Probe)
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 5
  ```
- [ ] HPA (Horizontal Pod Autoscaler)
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  spec:
    minReplicas: 2
    maxReplicas: 10
    metrics:
    - type: Resource
      resource:
        name: cpu
        targetAverageUtilization: 70
  ```

### 🧪 최종 검증
- [ ] 전체 시스템 E2E 테스트
- [ ] 부하 테스트 (k6, locust)
- [ ] 장애 시나리오 테스트 (Pod 강제 종료)
- [ ] 모니터링 대시보드 확인

---

# 📊 최종 아키텍처

```
                                    ┌─────────────────────────────────────────────────────────┐
                                    │                    Kubernetes Cluster                    │
                                    │                                                         │
[User] ──→ [Ingress] ──→ [API Service] ──→ [API Pods x3]                                    │
                                    │           │                                             │
                                    │           ├──→ [Redis] ──→ 캐시                         │
                                    │           ├──→ [OpenSearch] ──→ 검색                    │
                                    │           └──→ [PostgreSQL] ──→ 원본 저장               │
                                    │                                                         │
[Airflow Scheduler] ──→ [Crawler CronJob] ──→ [Kafka] ──→ [Consumers]                       │
                                    │                          │                              │
                                    │                          ├──→ PostgreSQL Consumer      │
                                    │                          └──→ OpenSearch Consumer      │
                                    │                                                         │
                                    │ [Prometheus] ──→ [Grafana] ──→ 모니터링                 │
                                    └─────────────────────────────────────────────────────────┘
```

---

# ✅ 전체 마일스톤 체크리스트

| Week | Day | Task | Status |
|------|-----|------|--------|
| 1 | 1 | PostgreSQL 환경 구축 | ⬜ |
| 1 | 2 | SQLAlchemy 모델 정의 | ⬜ |
| 1 | 3 | CRUD API 구현 | ⬜ |
| 1 | 4 | 크롤러 연동 (듀얼 저장) | ⬜ |
| 1 | 5 | Redis 환경 구축 | ⬜ |
| 1 | 6 | 캐싱 로직 구현 | ⬜ |
| 1 | 7 | 캐시 관리 기능 | ⬜ |
| 2 | 1 | Airflow 환경 구축 | ⬜ |
| 2 | 2 | 첫 번째 DAG 작성 | ⬜ |
| 2 | 3 | Task 분리 및 모듈화 | ⬜ |
| 2 | 4 | XCom 데이터 전달 | ⬜ |
| 2 | 5 | 알림 및 재시도 로직 | ⬜ |
| 3 | 1 | Kafka 환경 구축 | ⬜ |
| 3 | 2 | Python 클라이언트 설정 | ⬜ |
| 3 | 3 | Producer 구현 | ⬜ |
| 3 | 4 | Consumer 구현 | ⬜ |
| 3 | 5 | 에러 처리 및 DLQ | ⬜ |
| 4 | 1 | Dockerfile 작성 | ⬜ |
| 4 | 2 | 이미지 빌드 및 테스트 | ⬜ |
| 4 | 3 | K8s 기본 리소스 배포 | ⬜ |
| 4 | 4 | CronJob + StatefulSet | ⬜ |
| 4 | 5 | ConfigMap, Secret, Ingress | ⬜ |
| 4 | 6 | GitHub Actions CI/CD | ⬜ |
| 4 | 7 | 배포 전략 + 최종 테스트 | ⬜ |

---

> **작성일**: 2026-01-10  
> **예상 완료일**: 2026-02-07 (4주 후)
