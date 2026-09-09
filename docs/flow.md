# Processing Flow

## 상세 처리 흐름

```
[Step 1] 우편함 개폐 감지
  자기 센서가 우편함 뚜껑 열림을 감지
  → Jetson Python 모듈에 신호 전달

[Step 2] 카메라 촬영
  Jetson이 카메라를 통해 우편함 내부 촬영
  → 이미지 파일 임시 저장

[Step 3] YOLO v8 감지
  온디바이스 YOLO 모델로 객체 감지
  → 우편물 존재 여부 1차 판단
  → 신뢰도(confidence) 점수 산출

[Step 4] Gemini Vision API 분석 (선택적)
  YOLO 신뢰도가 낮거나, 정밀 분석 필요 시
  → Gemini Vision API로 이미지 전송
  → 문맥 분석 (무엇이 들어왔는지, 어떤 종류인지)

[Step 5] Flask API 전송
  Jetson → Flask 서버로 HTTP POST
  전송 데이터:
  - 이미지 파일 (multipart/form-data)
  - 감지 결과 JSON (detected: bool, confidence: float, label: str)
  - 타임스탬프

[Step 6] 서버 처리
  Flask 수신 후:
  - 이미지를 서버 스토리지에 저장
  - PostgreSQL에 감지 기록 삽입

[Step 7] Telegram 알림
  감지 결과가 양성(우편물 있음)이면:
  - 이미지 + 메시지를 Telegram Bot으로 전송
  - 예: "📬 우편물이 도착했습니다! [시간]"

[Step 8] 웹 대시보드 업데이트
  감지 이력이 DB에 저장되면
  - 웹 대시보드에서 최신 이력 확인 가능
  - 이미지 뷰어로 촬영 이미지 조회 가능
```

## 에러 처리 흐름

- Gemini API 실패 시: YOLO 결과만으로 판단하고 계속 진행
- Flask 서버 연결 실패 시: Jetson에서 로컬 로그 기록 후 재시도
- Telegram 전송 실패 시: 서버 로그에 기록하고 DB에는 저장 완료
