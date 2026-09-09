import os
import requests
import logging
from flask import Blueprint
from models import mark_telegram_sent

notify_bp = Blueprint("notify", __name__)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "http://localhost:5000")

def send_telegram(detection_id: int, image_path: str, gemini_result: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram 설정 없음. 알림 건너뜀.")
        return
    message = f"\U0001f4ec *우편물이 도착했습니다!*\n\n"
    if gemini_result:
        message += f"\U0001f4cb 분석 결과: {gemini_result}\n"
    message += f"\U0001f517 대시보드: {SERVER_BASE_URL}"
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    if image_path:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "photo": f"{SERVER_BASE_URL}{image_path}", "caption": message, "parse_mode": "Markdown"}
        resp = requests.post(f"{api_url}/sendPhoto", data=payload, timeout=10)
    else:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        resp = requests.post(f"{api_url}/sendMessage", json=payload, timeout=10)
    if resp.status_code == 200:
        logger.info(f"Telegram 알림 전송 성공 (id={detection_id})")
        mark_telegram_sent(detection_id)
    else:
        logger.error(f"Telegram 실패: {resp.status_code}")
