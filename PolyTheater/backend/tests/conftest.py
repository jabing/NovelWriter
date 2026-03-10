"""
测试夹具配置

提供通用的 mock fixtures 用于测试。
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import asyncio
import tempfile
import os


# 配置 asyncio 模式
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_client():
    """Mock LLM 客户端"""
    client = MagicMock()
    client.chat.return_value = "Test response from LLM"
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    return client


@pytest.fixture
def mock_zep_client():
    """Mock Zep 知识图谱客户端"""
    client = MagicMock()
    client.create_graph.return_value = "test-graph-id"
    client.add_episode.return_value = "test-episode-id"
    client.get_graph.return_value = {"nodes": [], "edges": []}
    return client


@pytest.fixture
def mock_async_llm_client():
    """Mock 异步 LLM 客户端"""
    client = MagicMock()
    client.chat = AsyncMock(return_value="Async test response")
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Async test response"))]
        )
    )
    return client


@pytest.fixture
def mock_async_zep_client():
    """Mock 异步 Zep 客户端"""
    client = MagicMock()
    client.create_graph = AsyncMock(return_value="test-graph-id")
    client.add_episode = AsyncMock(return_value="test-episode-id")
    client.get_graph = AsyncMock(return_value={"nodes": [], "edges": []})
    return client


@pytest.fixture
def sample_story_world():
    """示例故事世界数据"""
    return {
        "name": "测试故事世界",
        "genre": "悬疑",
        "characters": [
            {"id": "char_1", "name": "主角A", "role": "protagonist"},
            {"id": "char_2", "name": "配角B", "role": "supporting"},
        ],
        "settings": {"time_period": "现代", "location": "城市"},
    }


@pytest.fixture
def sample_character():
    """示例角色数据"""
    return {
        "id": "char_1",
        "name": "张三",
        "role": "protagonist",
        "traits": {
            "mbti": "INTJ",
            "gender": "male",
            "cognitive_style": "analytical",
        },
        "background": "一名经验丰富的侦探",
    }


@pytest.fixture
def sample_milestone():
    """示例里程碑事件"""
    return {
        "id": "milestone_1",
        "name": "关键发现",
        "chapter": 3,
        "description": "主角发现了关键线索",
        "impact_characters": ["char_1", "char_2"],
        "required": True,
    }


@pytest.fixture
def test_app():
    """创建测试 Flask 应用"""
    from flask import Flask, jsonify
    from flask_cors import CORS
    from app.database import db
    from app.api.characters import characters_bp
    from app.api.simulation import simulation_bp
    from app.api.narratives import narratives_bp
    from app.api.projects import projects_bp
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    CORS(app)
    db.init_app(app)
    
    # Add health and status routes (from main.py)
    import time
    from datetime import datetime, timezone
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0",
            "uptime": "0h 0m 0s",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
    
    @app.route('/')
    def root():
        return jsonify({
            "welcome": "PolyTheater API",
            "version": "1.0.0"
        })
    
    @app.route('/api/v1/status')
    def status():
        return jsonify({
            "status": "running",
            "version": "1.0.0"
        })

    
    app.register_blueprint(characters_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(narratives_bp)
    app.register_blueprint(projects_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_client(test_app):
    """创建测试客户端"""
    return test_app.test_client()


@pytest.fixture
def test_db(test_app):
    """测试数据库会话"""
    from app.database import db
    with test_app.app_context():
        yield db
