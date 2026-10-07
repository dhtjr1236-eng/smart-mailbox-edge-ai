"""Mailbox capture/detection pipeline; importing this module never opens hardware."""
from __future__ import annotations

import argparse
import logging
import math
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    server_url: str = "http://localhost:5000"
    sensor_pin: int = 11
    camera: int | str = 0
    model_path: str = "yolov8n.pt"
    confidence: float = 0.5
    gemini_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    save_dir: Path = Path(__file__).resolve().parent / "captured"
    timeout: float = 10.0

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        camera = env.get("MAILBOX_CAMERA", "0")
        config = cls(
            server_url=env.get("MAILBOX_SERVER_URL", cls.server_url).rstrip("/"),
            sensor_pin=int(env.get("MAILBOX_SENSOR_PIN", "11")),
            camera=int(camera) if camera.isdecimal() else camera,
            model_path=env.get("MAILBOX_MODEL_PATH", cls.model_path),
            confidence=float(env.get("MAILBOX_CONFIDENCE", "0.5")),
            gemini_key=env.get("GEMINI_API_KEY", ""),
            gemini_model=env.get("MAILBOX_GEMINI_MODEL", cls.gemini_model),
            save_dir=Path(env.get("MAILBOX_SAVE_DIR", str(cls.save_dir))),
            timeout=float(env.get("MAILBOX_TIMEOUT", "10")),
        )
        url = urlsplit(config.server_url)
        if url.scheme not in {"http", "https"} or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError("MAILBOX_SERVER_URL must be an HTTP(S) base URL without credentials/query/fragment")
        if config.sensor_pin <= 0 or (isinstance(config.camera, int) and config.camera < 0):
            raise ValueError("Invalid GPIO pin or camera index")
        if not math.isfinite(config.confidence) or not 0 <= config.confidence <= 1:
            raise ValueError("MAILBOX_CONFIDENCE must be between 0 and 1")
        if not math.isfinite(config.timeout) or config.timeout <= 0:
            raise ValueError("MAILBOX_TIMEOUT must be positive")
        return config


def capture_image(config, cv2_module):
    config.save_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2_module.VideoCapture(config.camera)
    try:
        if not cap.isOpened():
            raise RuntimeError("카메라를 열 수 없습니다.")
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("이미지 캡처 실패")
    finally:
        cap.release()
    path = config.save_dir / f"capture_{uuid.uuid4().hex}.jpg"
    if not cv2_module.imwrite(str(path), frame):
        raise RuntimeError("이미지 저장 실패")
    return path


def run_yolo(image_path, model, threshold):
    # Preserve the existing highest-confidence object selection. Mail-specific
    # classification/model training is a separate, not-yet-implemented task.
    result = {"detected": False, "confidence": 0.0, "label": ""}
    for prediction in model(str(image_path), conf=threshold):
        for box in prediction.boxes:
            confidence = float(box.conf)
            if confidence > result["confidence"]:
                result = {"detected": True, "confidence": confidence,
                          "label": model.names[int(box.cls)]}
    return result


def run_gemini(image_path, model):
    if model is None:
        return ""
    try:
        response = model.generate_content([
            "이 우편함 내부 이미지를 분석해서 우편물이 있는지, 있다면 어떤 종류인지 한 문장으로 설명해줘.",
            {"mime_type": "image/jpeg", "data": Path(image_path).read_bytes()},
        ])
        return response.text.strip()
    except Exception:
        logger.warning("Gemini 분석 실패; 기본 감지 결과로 계속 진행합니다.")
        return ""


def send_to_server(image_path, result, analysis, config, http):
    with Path(image_path).open("rb") as image:
        response = http.post(
            f"{config.server_url}/api/detections",
            files={"image": (Path(image_path).name, image, "image/jpeg")},
            data={"detected": str(result["detected"]).lower(),
                  "confidence": result["confidence"], "label": result["label"],
                  "gemini_result": analysis,
                  "timestamp": datetime.now(timezone.utc).isoformat()},
            timeout=config.timeout,
        )
        response.raise_for_status()
        return response.json()


class Pipeline:
    def __init__(self, capture, detect, analyze, send):
        self.capture, self.detect, self.analyze, self.send = capture, detect, analyze, send

    def run(self):
        path = self.capture()
        result = self.detect(path)
        analysis = self.analyze(path) if result["confidence"] < 0.7 else ""
        return self.send(path, result, analysis)


def build_pipeline(config):
    # Optional device dependencies are loaded only for real execution.
    import cv2
    import requests
    from ultralytics import YOLO

    model = YOLO(config.model_path)
    gemini = None
    if config.gemini_key:
        import google.generativeai as genai
        genai.configure(api_key=config.gemini_key)
        gemini = genai.GenerativeModel(config.gemini_model)
    return Pipeline(
        lambda: capture_image(config, cv2),
        lambda path: run_yolo(path, model, config.confidence),
        lambda path: run_gemini(path, gemini),
        lambda path, result, analysis: send_to_server(path, result, analysis, config, requests),
    )


def simulation_pipeline(config, image_path, send=False):
    """Use a supplied JPEG and a labelled fake result; no camera/GPIO/YOLO."""
    if not image_path.is_file():
        raise ValueError("Simulation requires an existing JPEG supplied with --image")
    if image_path.read_bytes()[:3] != b"\xff\xd8\xff":
        raise ValueError("--image must be a JPEG file")

    def deliver(path, result, analysis):
        if send:
            import requests
            return send_to_server(path, result, analysis, config, requests)
        logger.info("SIMULATION: capture=%s result=%s (no network request)", path, result)
        return {"status": "simulated", "result": result}

    return Pipeline(lambda: image_path,
                    lambda _: {"detected": True, "confidence": 0.6, "label": "simulation"},
                    lambda _: "SIMULATION: 실제 AI 분석 결과가 아닙니다.", deliver)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", help="explicit offline simulation")
    parser.add_argument("--image", type=Path, help="JPEG fixture for simulation")
    parser.add_argument("--send", action="store_true", help="allow simulation to upload a test record")
    parser.add_argument("--once", action="store_true", help="run one capture without GPIO polling")
    args = parser.parse_args(argv)
    if args.simulate and args.image is None:
        parser.error("--simulate requires --image path/to/test.jpg")
    if not args.simulate and (args.image is not None or args.send):
        parser.error("--image and --send are simulation-only options")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    gpio = None
    try:
        config = Config.from_env()
        if not args.simulate and not args.once:
            import Jetson.GPIO as gpio
            gpio.setmode(gpio.BOARD)
            gpio.setup(config.sensor_pin, gpio.IN)
        pipeline = (simulation_pipeline(config, args.image, args.send)
                    if args.simulate else build_pipeline(config))
        if args.once:
            pipeline.run()
            return 0
        while True:
            if args.simulate or gpio.input(config.sensor_pin) == gpio.HIGH:
                try:
                    pipeline.run()
                except Exception as exc:
                    logger.error("파이프라인 실패 (%s); 다음 이벤트를 기다립니다.", type(exc).__name__)
                time.sleep(10 if args.simulate else 5)
            time.sleep(0.1)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        logger.error("실행 실패 (%s). 설정·의존성·장치를 확인하세요.", type(exc).__name__)
        return 1
    finally:
        if gpio is not None:
            gpio.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
