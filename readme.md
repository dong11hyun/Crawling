## 2025_11_22 
- project with z

## 개발 환경 설정 (Getting Started)

이 프로젝트를 로컬에서 실행하려면 다음 단계를 따르세요.

### 1. 가상환경 생성 및 실행
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 실행 (Windows)
venv\Scripts\activate

# 가상환경 실행 (Mac/Linux)
source venv/bin/activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정
```bash
python manage.py migrate
```

### 4. 서버 실행
```bash
python manage.py runserver
```
