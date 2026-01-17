# Week 3: Kafka 실시간 파이프라인

> 동료가 처음부터 따라할 때 **반드시 실행해야 하는 명령어** 모음  
> 마지막 업데이트: 2026-01-17

---

## Day 1: Kafka 환경 구축
- **뭘 하는 건가?**: Kafka, Zookeeper, Kafka UI를 Docker로 설치
- **왜 필요한가?**: 실시간 데이터 스트리밍 인프라

```
Day 1: Kafka 환경 구축
├── [ ] docker-compose.yml에 Kafka 추가
├── [ ] Zookeeper (Kafka 코디네이터)
├── [ ] Kafka (메시지 브로커)
└── [ ] Kafka UI (모니터링)
```

### 1. Kafka 서비스 시작
```bash
cd C:\B2_crawling
docker-compose up -d zookeeper kafka kafka-ui
```

### 2. 컨테이너 상태 확인
```bash
docker ps | findstr kafka
docker ps | findstr zookeeper
```
- `musinsa-zookeeper` ✅
- `musinsa-kafka` ✅
- `musinsa-kafka-ui` ✅

### 3. Kafka UI 접속
- **URL**: http://localhost:8088
- 클러스터 `musinsa-cluster` 확인

### 4. Topic 생성 테스트
```bash
docker exec -it musinsa-kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic musinsa-products \
  --partitions 3 \
  --replication-factor 1
```

### 5. Topic 목록 확인
```bash
docker exec -it musinsa-kafka kafka-topics --list \
  --bootstrap-server localhost:9092
```

---

## Day 2: Python 클라이언트 설정
- **뭘 하는 건가?**: kafka-python 설치 및 연결 테스트
- **왜 필요한가?**: Python에서 Kafka Producer/Consumer 사용 준비

```
Day 2: Python 클라이언트 설정
├── [x] kafka-python 설치
├── [x] src/kafka/config.py - 공통 설정
├── [x] src/kafka/test_connection.py - 연결 테스트
└── [x] 메시지 발행/소비 테스트
```

### 1. kafka-python 설치
```bash
pip install kafka-python
```

### 2. 연결 테스트 실행
```bash
cd C:\B2_crawling\src\kafka
python test_connection.py
```

### 3. 테스트 결과 (예시)
```
✅ Kafka 연결 성공: localhost:9092
   클러스터 ID: 0jAB3w9ITC6BbwqvJvqGhQ
✅ Topic 개수: 1 - musinsa-products
✅ 메시지 발행 성공! Partition: 2, Offset: 0
✅ 메시지 소비 성공!
🎉 모든 테스트 통과!
```

### 4. 파일 구조
```
src/kafka/
├── __init__.py        # 패키지 초기화
├── config.py          # 공통 설정 (브로커, Topic)
└── test_connection.py # 연결 테스트
```

---

## Day 3: Producer 구현
- **뭘 하는 건가?**: Python에서 Kafka로 상품 데이터 발행
- **왜 필요한가?**: 크롤러 → Kafka 연동 준비

```
Day 3: Producer 구현
├── [x] kafka_client/producer.py - Producer 클래스
├── [x] kafka_client/test_producer.py - 테스트 스크립트
└── [x] Kafka UI에서 메시지 확인
```

### 1. Producer 테스트
```bash
cd C:\B2_crawling\src
python -m kafka_client.test_producer
```

### 2. 예상 결과
```
📦 방법 1: ProductProducer 클래스
    [1] 테스트 패딩 자켓 - 블랙 → ✅ 성공
    [2] 테스트 맨투맨 - 그레이 → ✅ 성공

📦 방법 2: publish_products() 함수
    결과: 성공 3, 실패 0
```

### 3. Kafka UI 확인
- http://localhost:8088 → Topics → musinsa-products → Messages
- 6개 메시지 확인 (1개 테스트 + 5개 상품)
- JSON 데이터에 `published_at` 필드 추가됨

### 4. 파일 구조
```
src/kafka_client/
├── __init__.py
├── config.py          # 공통 설정
├── producer.py        # Producer 클래스
├── test_producer.py   # 테스트
└── test_connection.py
```

---

## Day 4: Consumer 구현
- **뭘 하는 건가?**: Kafka에서 데이터 받아서 PostgreSQL/OpenSearch에 저장
- **왜 필요한가?**: 실시간 데이터 처리, 저장소 분리

```
Day 4: Consumer 구현
├── [x] consumer.py - Consumer 기본 클래스
├── [x] consumer_postgres.py - PostgreSQL Consumer
├── [x] consumer_opensearch.py - OpenSearch Consumer
└── [x] 메시지 소비 테스트
```

### 1. 파일 구조
```
src/kafka_client/
├── consumer.py            # Consumer 기본 클래스
├── consumer_postgres.py   # Kafka → PostgreSQL
└── consumer_opensearch.py # Kafka → OpenSearch
```

### 2. Consumer 실행 (터미널 2개 필요)

**터미널 1 - PostgreSQL Consumer:**
```bash
cd C:\B2_crawling\src
python -m kafka_client.consumer_postgres
```

**터미널 2 - OpenSearch Consumer:**
```bash
cd C:\B2_crawling\src
python -m kafka_client.consumer_opensearch
```

### 3. Producer로 메시지 발행 (새 터미널)
```bash
cd C:\B2_crawling\src
python -m kafka_client.test_producer
```

### 4. 예상 로그
```
🐘 PostgreSQL Consumer:
    📝 UPDATE: https://www.musinsa.com/products/12345
    ✅ 처리 완료: partition=2, offset=1

🔍 OpenSearch Consumer:
    🔍 OpenSearch created: https://www.musinsa.com/products/12345
    📝 오프셋 커밋: 10건 처리됨
```

### 5. 전체 흐름
```
Producer → Kafka → Consumer → PostgreSQL/OpenSearch
```

---

## Day 5: 크롤러 Kafka 연동 + DLQ 개념
- **뭘 하는 건가?**: Airflow DAG에서 크롤링 → Kafka 발행 연동
- **왜 필요한가?**: 실제 크롤링 데이터가 Kafka를 통해 저장소로 전달

```
Day 5: 크롤러 Kafka 연동 + DLQ 개념
├── [x] airflow/Dockerfile - kafka-python 추가
├── [x] airflow/docker-compose.yml - Kafka 네트워크 연결
├── [x] musinsa_kafka_dag.py - Kafka 발행 DAG
└── [x] DLQ 개념 이해
```

### 1. 네트워크 설정 (핵심!)
Airflow와 Kafka가 다른 docker-compose에 있어서 네트워크 연결 필요:
```yaml
# airflow/docker-compose.yml
networks:
  b2_crawling_opensearch-net:
    external: true
```

### 2. Kafka 주소 설정
```python
# Airflow 컨테이너 내부에서:
bootstrap_servers='musinsa-kafka:29092'  # ✅ Docker 내부 주소

# 로컬 venv에서:
bootstrap_servers='localhost:9092'       # ✅ 호스트 주소
```

### 3. DAG 실행
```bash
# Airflow 재시작
cd C:\B2_crawling\airflow
docker-compose down && docker-compose up -d

# Airflow UI에서 musinsa_kafka_dag Trigger
```

### 4. 전체 흐름
```
[Airflow DAG]
     │
crawl_task → validate_task → publish_kafka_task
                                    │
                              [Kafka Topic]
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
       [PostgreSQL Consumer]         [OpenSearch Consumer]
```

### 5. DLQ (Dead Letter Queue) 개념

**DLQ란?** 처리 실패한 메시지를 별도 저장하는 큐

```
정상 흐름:  Producer → Topic → Consumer (성공)
DLQ 흐름:   Producer → Topic → Consumer (실패) → DLQ Topic
```

| 항목 | 설명 |
|------|------|
| **목적** | 실패 메시지 보존, 나중에 재처리 |
| **구현** | `musinsa-products-dlq` 토픽 생성 |
| **사용 시점** | JSON 파싱 실패, DB 저장 실패 등 |

> 💡 **이번에는 개념만** 학습. 실제 DLQ 구현은 선택사항

---

## 접속 주소 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| Kafka | localhost:9092 | 외부 접속용 |
| Kafka (내부) | kafka:29092 | 컨테이너 간 통신 |
| Zookeeper | localhost:2181 | Kafka 코디네이터 |
| Kafka UI | http://localhost:8088 | 모니터링 대시보드 |
