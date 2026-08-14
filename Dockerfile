# Multi-stage Dockerfile for Discord Bot & Web Health Server on Railway / Cloud Run
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    nodejs \
    npm \
    fonts-noto-core \
    fonts-noto-arabic \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# Install Node dependencies for server.ts health check
RUN npm install

EXPOSE 3000

RUN chmod +x start.sh

CMD ["./start.sh"]
