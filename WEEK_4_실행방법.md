# Week 4: Kubernetes 실행방법

> 동료가 처음부터 따라할 때 **반드시 실행해야 하는 명령어** 모음  
> 마지막 업데이트: 2026-01-17

---

## Day 1: Dockerfile 작성
- **뭘 하는 건가?**: API 서버와 Consumer를 Docker 이미지로 빌드
- **왜 필요한가?**: K8s에서 실행하려면 컨테이너 이미지 필요

```
Day 1: Dockerfile 작성
├── [x] Dockerfile.api - FastAPI 서버
├── [x] Dockerfile.consumer - Kafka Consumer
├── [x] requirements 파일 생성
└── [x] 로컬 빌드 테스트
```

### 1. 파일 구조
```
C:\B2_crawling\
├── Dockerfile.api           # FastAPI 서버
├── Dockerfile.consumer      # Kafka Consumer
├── requirements-api.txt     # API 의존성
├── requirements-consumer.txt # Consumer 의존성
└── docker/
    └── consumer-entrypoint.sh  # Consumer 실행 스크립트
```

### 2. 이미지 빌드
```bash
cd C:\B2_crawling

# API 이미지 빌드
docker build -f Dockerfile.api -t musinsa-api:latest .

# Consumer 이미지 빌드
docker build -f Dockerfile.consumer -t musinsa-consumer:latest .
```

### 3. 빌드 확인
```bash
docker images | findstr musinsa
```

### 4. 예상 결과
```
musinsa-api:latest       xxx    343MB
musinsa-consumer:latest  xxx    299MB
```

---

## Day 2: 이미지 빌드 및 테스트
- **뭘 하는 건가?**: 빌드된 이미지가 정상 작동하는지 확인
- **왜 필요한가?**: K8s 배포 전 이미지 검증

```
Day 2: 이미지 빌드 및 테스트
├── [x] 기본 확인 (Python 버전)
├── [x] Consumer 이미지 실제 연결 테스트
└── [x] Kafka 연결 성공 확인
```

### 1. 기본 확인
```bash
docker run --rm musinsa-api:latest python --version
docker run --rm musinsa-consumer:latest python --version
```

### 2. Consumer 실제 연결 테스트
```bash           네트워크 이름은 현재 b2인데, 폴더명마다 다름
docker run --rm --network b2_crawling_opensearch-net ^
  -e KAFKA_BOOTSTRAP_SERVERS=musinsa-kafka:29092 ^
  -e CONSUMER_TYPE=postgres ^
  -e MUSINSA_DB_URL=postgresql://crawler:password@musinsa-postgres:5432/musinsa_db ^
  musinsa-consumer:latest
```

### 3. 예상 결과
```
✅ Consumer 연결 성공: musinsa-kafka:29092
   Group ID: postgres-consumer-group
   Topics: ['musinsa-products']
🚀 Consumer 시작, 메시지 대기 중...
Successfully joined group postgres-consumer-group
```

---

## Day 3: K8s 기본 리소스 배포
- **뭘 하는 건가?**: Docker 이미지를 Kubernetes(Minikube)에 배포
- **왜 필요한가?**: 컨테이너 오케스트레이션, 자동 복구, 확장성

```
Day 3: K8s 기본 리소스 배포
├── [x] Minikube 시작
├── [x] Docker 이미지 로드
├── [x] Namespace 생성
├── [x] API Deployment + Service 배포
├── [x] Consumer Deployment 배포
└── [x] 배포 확인
```

### 1. 사전 준비
```powershell
# Docker Compose 인프라 실행 (K8s에서 연결할 DB/Kafka)
cd C:\Crawling
docker-compose up -d postgres redis kafka zookeeper
```

### 2. Minikube 시작
```powershell
# Minikube 시작 (처음 한 번, 또는 PC 재시작 후)
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" start --driver=docker

# 상태 확인
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" status

# kubectl 연결 확인
kubectl cluster-info
```

### 3. Docker 이미지 로드
```powershell
# Minikube에 이미지 로드 (각각 1-2분 소요)
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" image load musinsa-api:latest
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" image load musinsa-consumer:latest

# 확인
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" image list | findstr musinsa
```

### 4. K8s 리소스 배포
```powershell
# 네임스페이스 생성
kubectl apply -f k8s/namespace.yaml

# API 배포 (잠시 대기 후)
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml

# Consumer 배포
kubectl apply -f k8s/consumer-deployment.yaml
```

### 5. 배포 확인
```powershell
# Pod 상태 확인
kubectl get pods -n musinsa

# 서비스 확인
kubectl get svc -n musinsa

# 로그 확인
kubectl logs deployment/musinsa-api -n musinsa --tail=20
kubectl logs deployment/musinsa-consumer -n musinsa --tail=20
```

### 6. 서비스 접속 테스트
```powershell
# 서비스 URL 확인 (터널 생성)
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" service musinsa-api -n musinsa --url
```

### 7. 예상 결과
```
NAME                                READY   STATUS    
musinsa-api-xxx                     1/1     Running   
musinsa-consumer-xxx                1/1     Running   
```

### 8. 유용한 명령어
```powershell
# Pod 재시작
kubectl rollout restart deployment/musinsa-api -n musinsa

# 상세 정보 보기
kubectl describe pod -n musinsa -l app=musinsa-api

# 전체 리소스 보기
kubectl get all -n musinsa

# Minikube 중지/시작
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" stop
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" start
```

---

## Day 4: ConfigMap, Secret 관리
> (예정)

---

## Day 5: 모니터링 및 로깅
> (예정)

---

## 접속 주소 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| **K8s API 서버** | `minikube service musinsa-api -n musinsa --url` | Minikube 터널 필요 |
| PostgreSQL | localhost:5434 | Docker Compose |
| Kafka | localhost:9092 | Docker Compose |
| Redis | localhost:6380 | Docker Compose |

---

## K8s 파일 구조
```
k8s/
├── namespace.yaml           # musinsa 네임스페이스
├── api-deployment.yaml      # API 서버 Deployment
├── api-service.yaml         # API 서비스 (NodePort)
└── consumer-deployment.yaml # Consumer Deployment
```

