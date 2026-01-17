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
> (예정)

---

## Day 3: Producer 구현
> (예정)

---

## Day 4: Consumer 구현
> (예정)

---

## Day 5: 에러 처리 및 DLQ
> (예정)

---

## 접속 주소 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| Kafka | localhost:9092 | 외부 접속용 |
| Kafka (내부) | kafka:29092 | 컨테이너 간 통신 |
| Zookeeper | localhost:2181 | Kafka 코디네이터 |
| Kafka UI | http://localhost:8088 | 모니터링 대시보드 |
