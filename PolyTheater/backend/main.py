import time
from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS

from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    CORS_ORIGINS, CORS_SUPPORTS_CREDENTIALS, CORS_METHODS, CORS_ALLOW_HEADERS,
    SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME, ZEP_API_KEY,
    DEFAULT_MAX_ROUNDS, DEFAULT_MINUTES_PER_ROUND,
    DEFAULT_ACTIVE_AGENTS_MIN, DEFAULT_ACTIVE_AGENTS_MAX,
    UPLOAD_FOLDER, MAX_CONTENT_LENGTH
)
from app.api.characters import characters_bp
from app.api.simulation import simulation_bp
from app.api.narratives import narratives_bp
from app.database import db

# 记录应用启动时间
START_TIME = time.time()

app = Flask(__name__)
app.config.from_object(__name__)
CORS(
    app,
    origins=CORS_ORIGINS,
    supports_credentials=CORS_SUPPORTS_CREDENTIALS,
    methods=CORS_METHODS,
    allow_headers=CORS_ALLOW_HEADERS
)

db.init_app(app)

# Register API blueprints
app.register_blueprint(characters_bp)
app.register_blueprint(simulation_bp)
app.register_blueprint(narratives_bp)


@app.route('/health')
def health():
    db_status = "disconnected"
    try:
        with db.engine.connect():
            db_status = "connected"
    except Exception:
        db_status = "disconnected"

    uptime_seconds = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    return jsonify({
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0",
        "uptime": uptime_str,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    })


@app.route('/api/v1/status')
def status():
    return jsonify({
        "status": "running",
        "version": "1.0.0"
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )
