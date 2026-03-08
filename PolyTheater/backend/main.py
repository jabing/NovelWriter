from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from app.api.characters import characters_bp
from app.api.simulation import simulation_bp
from app.api.narratives import narratives_bp
from app.database import db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=Config.CORS_ORIGINS)

db.init_app(app)

# Register API blueprints
app.register_blueprint(characters_bp)
app.register_blueprint(simulation_bp)
app.register_blueprint(narratives_bp)


@app.route('/health')
def health():
    return jsonify({"status": "healthy"})


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
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
