# System Architecture

## 전체 구성

```
┌─────────────────────────┐
│   우편함 (물리)          │
│  카메라 + 자기 센서       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Jetson Orin Nano        │
│  - YOLO v8 감지          │
│  - Gemini Vision 분석    │
│  - Python edge 모듈      │
└────────────┬────────────┘
             │ HTTP POST (이미지 + 감지 결과)
             ▼
┌─────────────────────────┐
│  Flask Web Server        │
│  - REST API              │
│  - 이미지 저장           │
│  - 감지 기록 저장        │
└────────┬───────┬─────────┘
         │       │
         ▼       ▼
   PostgreSQL   Telegram Bot
   (기록 저장)  (알림 전송)
         │
         ▼
┌─────────────────────────┐
│  Web Dashboard           │
│  - 감지 이력 조회        │
│  - 이미지 확인           │
│  - 통계 확인             │
└─────────────────────────┘
```

## 컴포넌트별 역할

| 컴포넌트 | 역할 |
|---|---|
| Jetson Orin Nano | 온디바이스 YOLO 감지, Gemini API 호출, 결과 전송 |
| Flask Server | REST API, 이미지 수신 및 저장, DB 기록, Telegram 알림 트리거 |
| PostgreSQL | 감지 이력, 이미지 경로, 타임스탬프, 분석 결과 영구 저장 |
| Telegram Bot | 감지 즉시 사용자에게 이미지 + 메시지 전송 |
| Web Dashboard | 브라우저에서 감지 이력 조회 및 이미지 확인 |

## 네트워크 흐름

- Jetson → Flask: 로컬 네트워크 HTTP POST
- Flask → PostgreSQL: 내부 Docker 네트워크
- Flask → Telegram: HTTPS (Telegram Bot API)
- 사용자 브라우저 → Flask: HTTP (추후 HTTPS)
