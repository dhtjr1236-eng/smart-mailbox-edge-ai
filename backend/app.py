import os
from flask import Flask
from db import init_db
from routes.detection import detection_bp
from routes.notify import notify_bp

app = Flask(__name__, static_folder="../frontend", template_folder="../frontend")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static/images")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.register_blueprint(detection_bp, url_prefix="/api")
app.register_blueprint(notify_bp, url_prefix="/api")

with app.app_context():
    init_db()

@app.route("/")
def index():
    from flask import send_from_directory
    return send_from_directory("../frontend", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
