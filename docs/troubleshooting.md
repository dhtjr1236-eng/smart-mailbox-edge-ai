# Troubleshooting

## 1. Jetson → Flask 연결 실패

**증상**: `ConnectionRefusedError: [Errno 111]`

**원인**: Flask 서버가 실행되지 않았거나 IP 주소가 틀림

**해결**:
```bash
# 서버 측에서 Flask 실행 확인
docker-compose ps

# Jetson에서 서버 IP 확인 후 detector.py에서 SERVER_URL 수정
SERVER_URL = "http://192.168.x.x:5000"
```

---

## 2. YOLO 모델 로드 실패

**증상**: `FileNotFoundError: yolov8n.pt not found`

**해결**:
```bash
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

---

## 3. Telegram 알림 미발송

**증상**: 감지 기록은 저장되지만 Telegram 알림이 오지 않음

**원인**: Bot Token 또는 Chat ID 오류

**해결**:
```bash
# Bot Token 테스트
curl https://api.telegram.org/bot{TOKEN}/getMe

# Chat ID 확인
curl https://api.telegram.org/bot{TOKEN}/getUpdates
```

---

## 4. PostgreSQL 연결 오류

**증상**: `psycopg2.OperationalError: could not connect`

**해결**:
```bash
# Docker 컨테이너 상태 확인
docker ps

# 컨테이너 내부에서 psql 접속 테스트
docker exec -it mailbox_db psql -U admin -d mailbox
```

---

## 5. 이미지 파일이 저장 안 됨

**증상**: 감지 기록은 있지만 이미지가 없음

**원인**: Flask 서버의 uploads 디렉토리 권한 문제

**해결**:
```bash
chmod 755 backend/static/images/
```
