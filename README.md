<div align="center">

# 📬 Smart Mailbox Edge AI System

**Jetson Orin Nano 기반 우편함 AI 감지 + 웹 관리 시스템 + Telegram 알림 자동화**

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-black?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![YOLO](https://img.shields.io/badge/YOLO-v8-FF4B4B)
![Jetson](https://img.shields.io/badge/Jetson-Orin_Nano-76B900?logo=nvidia)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram)

</div>

Jetson에서 촬영한 이미지를 분석하고, 감지 기록을 웹 대시보드에서 확인하는
스마트 우편함 프로젝트입니다. Flask·PostgreSQL 백엔드와 Telegram 알림 연동 코드를 포함합니다.

## 현재 상태 · 2026-10-07

| 항목 | 이번 반영 내용 |
|---|---|
| Edge 감지 모듈 | Python 문법 오류 복구, 환경변수 설정, import 시 장치 접근 방지 |
| 시뮬레이션 | JPEG 입력으로 장치·네트워크 없이 실행, 명시적으로 선택한 경우에만 테스트 업로드 |
| 대시보드 | JavaScript 문법 오류 복구, 안전한 DOM 렌더링, 이미지 URL 제한·실패 대체 표시, 신뢰도 0% 표시 |
| 검증 | Python 테스트 12개 + DOM 테스트 8개 통과, Python·JavaScript 문법 검사 통과 |

**검증 범위:** 실제 Jetson·카메라·외부 서비스 연동은 미검증입니다.
Chromium 다운로드 실패로 실제 브라우저 검증도 남아 있습니다.
Docker·정적 파일 경로, 인증, 우편물 판정 정확도와 전송 재시도는 후속 개선 항목입니다.

실행 방법과 검증 상세는 [Edge 가이드](docs/edge-runtime.md)와
[대시보드 가이드](docs/dashboard-repair.md)를 참고하세요.

---

## 🚩 문제 정의

기존 우편함 관리 방식은 완전히 **수동**으로 이루어져 아래와 같은 문제가 발생합니다.

| 문제 | 설명 |
|---|---|
| 📭 누락 | 우편물 도착 여부를 직접 확인해야 해서 놓치는 경우 발생 |
| ⏱️ 지연 | 알림 수단이 없어 중요 문서를 제때 받지 못함 |
| 🗂️ 기록 없음 | 언제, 무엇이 들어왔는지 이력이 남지 않음 |

---

## 💡 해결책

Edge AI + 웹 대시보드 + Telegram 알림을 하나의 파이프라인으로 통합하여,  
**우편물 도착을 자동으로 감지 → 분석 → 기록 → 알림**합니다.

```
카메라 / 센서
    ↓
[Jetson Orin Nano] YOLO 감지 + Gemini Vision API 분석
    ↓
[Flask Web Server] 이미지 저장 + 감지 기록 저장 (PostgreSQL)
    ↓
[Web Dashboard] 실시간 감지 이력 확인
    ↓
[Telegram Bot] 즉시 알림 전송
```

---

## 🏗️ 시스템 구성

### 하드웨어

| 컴포넌트 | 사양 |
|---|---|
| Edge AI 보드 | NVIDIA Jetson Orin Nano |
| 카메라 | USB / CSI 카메라 |
| 센서 | 자기 센서 (우편함 개폐 감지) |
| 서버 | Mac mini M4 / Ubuntu 서버 |

### 소프트웨어 스택

| 계층 | 기술 |
|---|---|
| Edge AI | YOLO v8, Gemini Vision API, Python |
| 백엔드 | Flask, PostgreSQL, Docker Compose |
| 프론트엔드 | HTML / CSS / JavaScript |
| 알림 | Telegram Bot API |
| 배포 | Docker, Nginx |

---

## ⚙️ 처리 흐름

```
[1] 우편함 개폐 감지 (자기 센서)
       ↓
[2] 카메라 촬영 (Jetson)
       ↓
[3] YOLO 객체 감지 → 우편물 여부 판단
       ↓
[4] Gemini Vision API 문맥 분석 (고급 판별)
       ↓
[5] Flask API로 이미지 + 결과 전송
       ↓
[6] PostgreSQL에 감지 기록 저장
       ↓
[7] Web Dashboard에서 이력 확인 가능
       ↓
[8] Telegram Bot으로 즉시 알림 전송
```

상세 흐름은 [docs/flow.md](./docs/flow.md) 참고.

---

## 🧠 기술 선택 이유

| 기술 | 선택 이유 |
|---|---|
| **Jetson Orin Nano** | Edge에서 온디바이스 고속 추론. 서버 의존 없이 실시간 감지 가능 |
| **YOLO v8** | 경량 모델로 Jetson에서 실시간 처리 가능 |
| **Gemini Vision API** | YOLO의 한계(문맥 이해 부재)를 클라우드 멀티모달 AI로 보완 |
| **Flask** | 경량 백엔드로 빠른 프로토타이핑. REST API 구축에 적합 |
| **PostgreSQL** | 신뢰성 높은 RDBMS. 감지 이력 장기 보관에 적합 |
| **Docker Compose** | 환경 의존성 제거, 재현 가능한 배포 환경 구성 |
| **Telegram Bot** | 무료, 빠름, 별도 앱 설치 없이 실시간 알림 수신 가능 |

---

## 📁 폴더 구조

```
smart-mailbox-edge-ai/
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
├── docs/
│   ├── architecture.md      # 시스템 전체 구조
│   ├── flow.md              # 처리 흐름 상세
│   ├── api-spec.md          # REST API 명세
│   ├── erd.md               # 데이터베이스 ERD
│   ├── deployment.md        # 배포 방법
│   └── troubleshooting.md   # 자주 발생하는 오류
├── edge/
│   ├── detector.py
│   └── sender.py
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── routes/
│   └── db.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── nginx.conf
└── assets/
    ├── architecture.png
    └── dashboard.png
```

---

## 🚀 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/dhtjr1236-eng/smart-mailbox-edge-ai.git
cd smart-mailbox-edge-ai
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에서 PostgreSQL, Telegram Bot 토큰 등 설정
```

### 3. Docker Compose 실행

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### 4. Jetson에서 감지 모듈 실행

저장소 루트에서 Edge 환경변수를 설정한 뒤 실행합니다.

```bash
cp edge/.env.example edge/.env
# edge/.env 수정 후 (POSIX shell):
set -a
. edge/.env
set +a
python edge/detector.py
```

오프라인 시뮬레이션, 장치 의존성 및 검증 범위는
[Edge 실행 가이드](docs/edge-runtime.md)를 참고하세요.

### 5. 웹 대시보드 확인

```
http://localhost:5000
```

---

## 📸 화면 예시

> 스크린샷 및 시연 GIF는 `assets/` 폴더에 업데이트 예정

---

## 🔮 향후 확장 계획

- [ ] 사용자 권한(RBAC) 관리
- [ ] 실시간 로그 스트리밍
- [ ] 감지 기록 검색 기능
- [ ] 모바일 최적화 (반응형 웹)
- [ ] 이상 감지 알림 (낯선 접근 등)
- [ ] 다중 우편함 지원

자세한 계획은 [ROADMAP.md](./ROADMAP.md) 참고.

---

## 📄 라이선스

MIT License

---

## 👤 개발자

**오석환**  
Frontend / Edge AI / Embedded Developer  
GitHub: [dhtjr1236-eng](https://github.com/dhtjr1236-eng)

## 감지 모듈·대시보드 복구 검증

- [Edge 실행·시뮬레이션 가이드](docs/edge-runtime.md)
- [대시보드 수정 내용·테스트·미검증 범위](docs/dashboard-repair.md)

장치 없는 Python 테스트 12개와 대시보드 DOM 테스트 8개를 제공하며,
실제 Jetson 및 브라우저 검증 여부는 위 가이드에 구분하여 기록합니다.
