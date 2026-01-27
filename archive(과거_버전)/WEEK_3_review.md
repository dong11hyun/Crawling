# Week 3 Review: Kafka 실시간 파이프라인

> Week 3에서 배운 개념, 기술 스택, 코드 리뷰를 정리한 문서  
> 마지막 업데이트: 2026-01-17

---

# 📚 Part 1: 핵심 개념 정리

## 1. Kafka 기본 개념

### Apache Kafka란?
- **분산 이벤트 스트리밍 플랫폼**
- 대용량 실시간 데이터 처리
- LinkedIn에서 개발, 현재 Apache 프로젝트

### 기존 방식 vs Kafka
```
기존 방식 (직접 연결):
크롤러 → PostgreSQL (직접 저장)
       → OpenSearch (직접 저장)
- 결합도 높음, 장애 전파

Kafka 방식 (메시지 큐):
크롤러 → Kafka → Consumer → PostgreSQL
              → Consumer → OpenSearch
- 느슨한 결합, 장애 격리
- 버퍼링, 재처리 가능
```

---

## 2. Kafka 구성 요소

### 핵심 컴포넌트
| 컴포넌트 | 역할 |
|----------|------|
| **Zookeeper** | 클러스터 코디네이터, 메타데이터 관리 |
| **Broker** | 메시지 저장 및 전달 (Kafka 서버) |
| **Topic** | 메시지 카테고리 (폴더 개념) |
| **Partition** | Topic 내 병렬 처리 단위 |
| **Producer** | 메시지 발행자 |
| **Consumer** | 메시지 소비자 |

### Topic과 Partition
```
Topic: musinsa-products
├── Partition 0: [msg1, msg4, msg7...]
├── Partition 1: [msg2, msg5, msg8...]
└── Partition 2: [msg3, msg6, msg9...]
```
- **Partition 수** = 병렬 처리 정도
- 같은 Key는 **같은 Partition**에 저장 (순서 보장)

---

## 3. Producer와 Consumer

### Producer 설정
```python
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',        # 모든 복제본 확인
    retries=3,         # 재시도 횟수
)
```

### acks 옵션
| 값 | 의미 | 안정성 | 성능 |
|----|------|:------:|:----:|
| `0` | 확인 안 함 | 낮음 | 높음 |
| `1` | 리더만 확인 | 중간 | 중간 |
| `all` | 모든 복제본 확인 | 높음 | 낮음 |

### Consumer 설정
```python
consumer = KafkaConsumer(
    'musinsa-products',
    bootstrap_servers='localhost:9092',
    group_id='postgres-consumer-group',
    auto_offset_reset='earliest',    # 처음부터 읽기
    enable_auto_commit=False,        # 수동 커밋
)
```

---

## 4. Consumer Group

### 개념
- 같은 `group_id`를 가진 Consumer들의 집합
- **파티션을 나눠서 소비** (병렬 처리)

### 예시
```
Topic: musinsa-products (3 partitions)
Consumer Group: postgres-consumer-group
├── Consumer A → Partition 0
├── Consumer B → Partition 1
└── Consumer C → Partition 2
```

### 주의점
- Consumer 수 > Partition 수 → **일부 Consumer 유휴**
- Consumer 수 < Partition 수 → **일부 Consumer가 여러 파티션 처리**

---

## 5. Offset과 Commit

### Offset이란?
- Partition 내 **메시지 위치** (순번)
- Consumer가 "어디까지 읽었는지" 추적

### Commit 방식
| 방식 | 설명 | 장단점 |
|------|------|--------|
| **Auto Commit** | 일정 간격으로 자동 커밋 | 편리, 메시지 유실 가능 |
| **Manual Commit** | 직접 커밋 호출 | 정확, 코드 복잡 |

```python
# 수동 커밋
for message in consumer:
    process(message)
    consumer.commit()  # 처리 후 커밋
```

---

## 6. DLQ (Dead Letter Queue)

### 개념
- 처리 **실패한 메시지**를 별도 저장하는 큐
- 나중에 **재처리** 또는 **분석** 가능

### 흐름
```
정상: Producer → Topic → Consumer (성공)
DLQ:  Producer → Topic → Consumer (실패) → DLQ Topic
```

### 사용 시점
- JSON 파싱 실패
- DB 저장 실패
- 유효성 검증 실패

---

# 🛠️ Part 2: 기술 스택별 역할 및 튜닝

## 1. Kafka Broker

### 역할
- 메시지 저장 및 전달
- 파티션 관리, 복제

### docker-compose 설정
```yaml
kafka:
  image: confluentinc/cp-kafka:7.5.0
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

### ADVERTISED_LISTENERS 이해
```
PLAINTEXT://kafka:29092       → Docker 내부 통신
PLAINTEXT_HOST://localhost:9092 → 호스트에서 접근
```

---

## 2. Zookeeper

### 역할
- Kafka 클러스터 **메타데이터 관리**
- 브로커 상태 추적
- 컨트롤러 선출

### 설정
```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
    ZOOKEEPER_TICK_TIME: 2000
```

> 💡 Kafka 3.x부터는 Zookeeper 없이 KRaft 모드 지원

---

## 3. Kafka UI

### 역할
- 웹 기반 **모니터링 대시보드**
- Topic, Consumer, 메시지 확인

### 설정
```yaml
kafka-ui:
  image: provectuslabs/kafka-ui:latest
  ports:
    - "8088:8080"
  environment:
    KAFKA_CLUSTERS_0_NAME: musinsa-cluster
    KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
```

---

## 4. 네트워크 설정 (핵심!)

### 문제 상황
```
Airflow 컨테이너 → localhost:9092 → 접속 실패!
(Airflow와 Kafka가 다른 docker-compose에 있음)
```

### 해결책
```yaml
# airflow/docker-compose.yml
networks:
  b2_crawling_opensearch-net:
    external: true  # 외부 네트워크 참조

services:
  airflow-webserver:
    networks:
      - airflow-net
      - b2_crawling_opensearch-net  # Kafka 네트워크 추가
```

### Kafka 주소 정리
| 접속 위치 | 주소 |
|-----------|------|
| 로컬 venv (Windows) | `localhost:9092` |
| Airflow 컨테이너 | `musinsa-kafka:29092` |
| 같은 네트워크 컨테이너 | `kafka:29092` |

---

# 💻 Part 3: 코드 리뷰

## 1. config.py (Kafka 설정)

```python
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC_PRODUCTS = "musinsa-products"
TOPIC_PRODUCTS_DLQ = "musinsa-products-dlq"

PRODUCER_CONFIG = {
    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    "value_serializer": lambda v: json.dumps(v).encode('utf-8'),
    "acks": "all",
    "retries": 3,
}
```

### 리뷰 포인트
- ✅ 설정 **중앙 집중화**
- ✅ DLQ Topic 미리 정의
- ✅ 안전한 acks='all' 설정

---

## 2. producer.py

```python
class ProductProducer:
    def send(self, product: Dict, key: str = None) -> bool:
        key = key or product.get("url", "unknown")
        product["published_at"] = datetime.now(KST).isoformat()
        
        future = self.producer.send(TOPIC_PRODUCTS, key=key, value=product)
        result = future.get(timeout=10)
        return True
```

### 리뷰 포인트
- ✅ URL을 Key로 사용 → **같은 상품은 같은 파티션**
- ✅ `published_at` 타임스탬프 추가
- ✅ 동기 전송 (`future.get()`)으로 신뢰성 확보

---

## 3. consumer.py

```python
class ProductConsumer:
    def consume(self, handler: Callable, batch_size: int = 10):
        while self.running:
            messages = self.consumer.poll(timeout_ms=1000)
            for record in messages:
                handler(record.value)
            
            if processed % batch_size == 0:
                self.consumer.commit()  # 배치 커밋
```

### 리뷰 포인트
- ✅ **배치 커밋**으로 성능 최적화
- ✅ `enable_auto_commit=False`로 정확한 처리 보장
- ✅ 시그널 핸들러로 **안전한 종료**

---

## 4. musinsa_kafka_dag.py

```python
def run_publish_to_kafka(**context):
    producer = KafkaProducer(
        bootstrap_servers='musinsa-kafka:29092',  # Docker 내부 주소
        ...
    )
    for item in data:
        producer.send('musinsa-products', key=key, value=item)
```

### 리뷰 포인트
- ✅ Airflow → Kafka 연동 완성
- ✅ Docker 네트워크 주소 사용
- ⚠️ 에러 처리 추가 필요 (DLQ)

---

# 🎯 Part 4: 면접 대비 Q&A

### Q1. Kafka를 왜 사용하나요?
- **비동기 처리**: Producer/Consumer 분리
- **버퍼링**: 순간 트래픽 흡수
- **재처리**: Offset으로 과거 메시지 재소비
- **확장성**: 파티션으로 병렬 처리

### Q2. Partition의 역할은?
- Topic 내 **병렬 처리 단위**
- 같은 Key는 같은 Partition (순서 보장)
- Partition 수 = 최대 병렬 Consumer 수

### Q3. Consumer Group이란?
- **같은 group_id의 Consumer 집합**
- 파티션을 나눠서 병렬 소비
- 한 파티션은 그룹 내 **한 Consumer만** 소비

### Q4. acks='all' vs acks='1'의 차이는?
- `acks='1'`: 리더만 확인 → 빠름, 유실 가능
- `acks='all'`: 모든 복제본 확인 → 느림, 안전

### Q5. DLQ는 언제 사용하나요?
- **처리 실패 메시지** 보존
- 재처리 또는 원인 분석
- 메인 처리 흐름 **블로킹 방지**

### Q6. Docker 네트워크 이슈 해결법은?
- 다른 docker-compose의 서비스 접근 시
- `external: true`로 외부 네트워크 참조
- 서비스명:내부포트로 접근 (예: `kafka:29092`)

---

# ✅ Week 3 핵심 역량 체크리스트

| 역량 | 세부 내용 | 습득 |
|------|----------|:----:|
| Kafka 환경 구축 | Zookeeper, Kafka, Kafka UI Docker 설정 | ✅ |
| Topic 생성 | kafka-topics 명령어, Partition 설정 | ✅ |
| Producer 구현 | KafkaProducer, 직렬화, acks | ✅ |
| Consumer 구현 | KafkaConsumer, Consumer Group, Offset | ✅ |
| 배치 커밋 | 수동 커밋, 배치 단위 커밋 | ✅ |
| Airflow 연동 | DAG에서 Kafka 발행 | ✅ |
| 네트워크 설정 | Docker 네트워크, external 참조 | ✅ |
| DLQ 개념 | 실패 메시지 처리 전략 이해 | ✅ |
