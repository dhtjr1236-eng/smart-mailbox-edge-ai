# Deployment Guide

## 필요 사항

- Docker + Docker Compose 설치
- Python 3.10+
- Jetson JetPack 6.x
- PostgreSQL 15

## 서버 배포 (Docker Compose)

```bash
# 1. 저장소 클론
git clone https://github.com/dhtjr1236-eng/smart-mailbox-edge-ai.git
cd smart-mailbox-edge-ai

# 2. 환경 변수 설정
cp .env.example .env
nano .env

# 3. Docker Compose 실행
docker-compose -f docker/docker-compose.yml up -d

# 4. 상태 확인
docker-compose ps
```

## 환경 변수 (.env)

```env
POSTGRES_DB=mailbox
POSTGRES_USER=admin
POSTGRES_PASSWORD=yourpassword
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
FLASK_SECRET_KEY=your_secret_key
```

## Jetson 실행

```bash
cd edge
pip install -r requirements.txt
python detector.py
```

## 포트 정보

| 서비스 | 포트 |
|---|---|
| Flask Web Server | 5000 |
| PostgreSQL | 5432 |
| Nginx | 80 |
