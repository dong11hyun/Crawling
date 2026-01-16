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
> (예정)

---

## Day 3: Task 분리 및 모듈화
> (예정)

---

## Day 4: XCom 데이터 전달
> (예정)

---

## Day 5: 알림 및 재시도 로직
> (예정)

---

## 접속 주소 요약

| 서비스 | URL | 비고 |
|--------|-----|------|
| Airflow UI | http://localhost:8080 | admin / admin |
| Airflow PostgreSQL | localhost:5432 | airflow DB (내부용) |
