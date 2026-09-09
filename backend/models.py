from db import get_connection

def insert_detection(detected, confidence, label, gemini_result, image_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO detections (detected, confidence, label, gemini_result, image_path)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """, (detected, confidence, label, gemini_result, image_path))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row["id"]

def get_detections(page=1, limit=20, date_filter=None, detected_only=False):
    conn = get_connection()
    cur = conn.cursor()
    conditions = []
    params = []
    if date_filter:
        conditions.append("DATE(created_at) = %s")
        params.append(date_filter)
    if detected_only:
        conditions.append("detected = TRUE")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * limit
    cur.execute(f"SELECT * FROM detections {where} ORDER BY created_at DESC LIMIT %s OFFSET %s;", params + [limit, offset])
    rows = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) AS total FROM detections {where};", params)
    total = cur.fetchone()["total"]
    cur.close()
    conn.close()
    return list(rows), total

def get_detection_by_id(detection_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM detections WHERE id = %s;", (detection_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def mark_telegram_sent(detection_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE detections SET telegram_sent = TRUE WHERE id = %s;", (detection_id,))
    conn.commit()
    cur.close()
    conn.close()
