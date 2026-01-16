# Airflow + Playwright 커스텀 이미지
FROM apache/airflow:2.8.0-python3.11

USER root

# Playwright 의존성 설치 (Chromium 포함)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Python 패키지 설치
RUN pip install --no-cache-dir \
    playwright==1.40.0 \
    opensearch-py \
    sqlalchemy \
    psycopg2-binary

# Playwright Chromium 설치
RUN playwright install chromium
