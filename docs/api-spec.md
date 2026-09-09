# REST API Specification

## Base URL

```
http://<server-ip>:5000/api
```

---

## Endpoints

### POST /api/detections

Jetson에서 감지 결과 및 이미지를 서버로 전송

**Request**

```
Content-Type: multipart/form-data
```

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `image` | file | ✅ | 촬영 이미지 |
| `detected` | bool | ✅ | 우편물 감지 여부 |
| `confidence` | float | ✅ | 감지 신뢰도 (0.0 ~ 1.0) |
| `label` | string | - | 감지된 객체 레이블 |
| `gemini_result` | string | - | Gemini API 분석 결과 |
| `timestamp` | string | ✅ | ISO 8601 형식 타임스탬프 |

**Response**

```json
{
  "status": "ok",
  "detection_id": 42,
  "message": "Detection saved."
}
```

---

### GET /api/detections

감지 이력 목록 조회

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `page` | int | 페이지 번호 (기본값: 1) |
| `limit` | int | 페이지당 건수 (기본값: 20) |
| `date` | string | 날짜 필터 (YYYY-MM-DD) |
| `detected_only` | bool | 감지된 기록만 조회 |

**Response**

```json
{
  "total": 128,
  "page": 1,
  "results": [
    {
      "id": 42,
      "detected": true,
      "confidence": 0.94,
      "label": "mail",
      "gemini_result": "소형 우편물이 감지되었습니다.",
      "image_url": "/static/images/2026-09-09_10-00-00.jpg",
      "timestamp": "2026-09-09T10:00:00Z"
    }
  ]
}
```

---

### GET /api/detections/:id

특정 감지 기록 상세 조회

**Response**

```json
{
  "id": 42,
  "detected": true,
  "confidence": 0.94,
  "label": "mail",
  "gemini_result": "소형 우편물이 감지되었습니다.",
  "image_url": "/static/images/2026-09-09_10-00-00.jpg",
  "timestamp": "2026-09-09T10:00:00Z"
}
```
