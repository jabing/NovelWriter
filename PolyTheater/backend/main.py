import time
from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS

from config import DevelopmentConfig
from app.api.characters import characters_bp
from app.api.simulation import simulation_bp
from app.api.narratives import narratives_bp
from app.api.projects import projects_bp
from app.database import db

# 记录应用启动时间
START_TIME = time.time()


def create_app(config_class=DevelopmentConfig):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 初始化 CORS
    CORS(
        app,
        origins=app.config['CORS_ORIGINS'],
        supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
        methods=app.config['CORS_METHODS'],
        allow_headers=app.config['CORS_ALLOW_HEADERS']
    )
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建数据库表
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created successfully")
        except Exception as e:
            print(f"✗ Failed to create database tables: {e}")
    
    # 注册蓝图
    app.register_blueprint(characters_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(narratives_bp)
    app.register_blueprint(projects_bp)
    
    # 健康检查端点
    @app.route('/health')
    def health():
        db_status = "disconnected"
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
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

    # 根路径
    @app.route('/')
    def root():
        return jsonify({
            "welcome": "PolyTheater API",
            "version": "1.0.0",
            "description": "多视角故事世界引擎 - One World, Infinite Perspectives",
            "endpoints": [
                {"path": "/", "method": "GET", "description": "本欢迎页面"},
                {"path": "/health", "method": "GET", "description": "健康检查"},
                {"path": "/api/v1/status", "method": "GET", "description": "API 状态"},
                {"path": "/api/characters", "method": "GET, POST", "description": "角色管理"},
                {"path": "/api/simulation", "method": "GET, POST", "description": "模拟控制"},
                {"path": "/api/narratives", "method": "GET, POST", "description": "叙事生成"},
                {"path": "/api/projects", "method": "GET, POST", "description": "项目管理"}
            ],
            "docs": "https://github.com/code-yeongyu/PolyTheater"
        })

    # API 状态端点
    @app.route('/api/v1/status')
    def status():
        return jsonify({
            "status": "running",
            "version": "1.0.0"
        })

    return app


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    print(f"Starting PolyTheater API server...")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.run(
        host=app.config['FLASK_HOST'],
        port=app.config['FLASK_PORT'],
        debug=app.config['FLASK_DEBUG']
    )
