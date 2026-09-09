import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from models import insert_detection, get_detections, get_detection_by_id
from routes.notify import send_telegram

detection_bp = Blueprint("detection", __name__)

@detection_bp.route("/detections", methods=["POST"])
def receive_detection():
    detected = request.form.get("detected", "false").lower() == "true"
    confidence = float(request.form.get("confidence", 0))
    label = request.form.get("label", "")
    gemini_result = request.form.get("gemini_result", "")
    image_path = ""
    if "image" in request.files:
        image_file = request.files["image"]
        filename = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        image_file.save(save_path)
        image_path = f"/static/images/{filename}"
    detection_id = insert_detection(detected, confidence, label, gemini_result, image_path)
    if detected:
        send_telegram(detection_id, image_path, gemini_result)
    return jsonify({"status": "ok", "detection_id": detection_id}), 200

@detection_bp.route("/detections", methods=["GET"])
def list_detections():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    date_filter = request.args.get("date")
    detected_only = request.args.get("detected_only", "false").lower() == "true"
    rows, total = get_detections(page, limit, date_filter, detected_only)
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "detected": row["detected"],
            "confidence": row["confidence"],
            "label": row["label"],
            "gemini_result": row["gemini_result"],
            "image_url": row["image_path"],
            "timestamp": row["created_at"].isoformat() if row["created_at"] else None,
        })
    return jsonify({"total": total, "page": page, "results": results}), 200

@detection_bp.route("/detections/<int:detection_id>", methods=["GET"])
def get_detection(detection_id):
    row = get_detection_by_id(detection_id)
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "id": row["id"],
        "detected": row["detected"],
        "confidence": row["confidence"],
        "label": row["label"],
        "gemini_result": row["gemini_result"],
        "image_url": row["image_path"],
        "timestamp": row["created_at"].isoformat() if row["created_at"] else None,
    }), 200
