import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    # LLM 配置
    LLM_API_KEY = os.getenv('LLM_API_KEY')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL')
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini')
    ZEP_API_KEY = os.getenv('ZEP_API_KEY')
    
    # Flask 配置
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5001'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 模拟配置
    DEFAULT_MAX_ROUNDS = int(os.getenv('DEFAULT_MAX_ROUNDS', '144'))
    DEFAULT_MINUTES_PER_ROUND = int(os.getenv('DEFAULT_MINUTES_PER_ROUND', '60'))
    DEFAULT_ACTIVE_AGENTS_MIN = int(os.getenv('DEFAULT_ACTIVE_AGENTS_MIN', '5'))
    DEFAULT_ACTIVE_AGENTS_MAX = int(os.getenv('DEFAULT_ACTIVE_AGENTS_MAX', '20'))
    
    # 文件上传
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '52428800'))
    
    # 数据库配置 - 使用绝对路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    os.makedirs(DB_INSTANCE_DIR, exist_ok=True)
    DB_PATH = os.path.join(DB_INSTANCE_DIR, 'polytheater.db').replace(chr(92), "/")
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS 配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']


# 开发环境配置
class DevelopmentConfig(Config):
    FLASK_DEBUG = True


# 生产环境配置
class ProductionConfig(Config):
    FLASK_DEBUG = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
