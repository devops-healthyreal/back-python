# ============================
# Stage 1 — Build dependencies
# ============================
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc pkg-config default-libmysqlclient-dev libopenmpi-dev openmpi-bin && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel --no-cache-dir && \
    pip install --no-cache-dir "numpy<2.0" cython==0.29.36 && \
    pip install --no-cache-dir -r requirements.txt && \
    find /root/.cache/pip -type f -delete

# ============================
# Stage 2 — Final runtime image
# ============================
FROM python:3.11-slim

WORKDIR /app

# 런타임 필수 라이브러리만 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libmariadb3 chromium chromium-driver fonts-liberation \
        libglib2.0-0 libnss3 libx11-xcb1 libxcomposite1 libxcursor1 \
        libxdamage1 libxi6 libxtst6 libxrandr2 libasound2 \
        libatk-bridge2.0-0 libxss1 libgtk-3-0 libgbm1 libgl1 libsm6 libxext6 libxrender1 && \
    rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMIUM_PATH=/usr/bin/chromium \
    PATH=$PATH:/usr/lib/chromium/

# builder에서 필요한 site-packages만 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
