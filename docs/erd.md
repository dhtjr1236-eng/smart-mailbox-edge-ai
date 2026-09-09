# Database ERD

## 테이블 구조

### detections (감지 기록)

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | 자동 증가 ID |
| `detected` | BOOLEAN | 우편물 감지 여부 |
| `confidence` | FLOAT | YOLO 신뢰도 |
| `label` | VARCHAR(100) | 감지 레이블 |
| `gemini_result` | TEXT | Gemini 분석 결과 |
| `image_path` | VARCHAR(500) | 저장된 이미지 경로 |
| `telegram_sent` | BOOLEAN | Telegram 알림 발송 여부 |
| `created_at` | TIMESTAMP | 감지 시각 |

### SQL 예시

```sql
CREATE TABLE detections (
  id            SERIAL PRIMARY KEY,
  detected      BOOLEAN NOT NULL DEFAULT FALSE,
  confidence    FLOAT,
  label         VARCHAR(100),
  gemini_result TEXT,
  image_path    VARCHAR(500),
  telegram_sent BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);
```
