import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class DevelopmentConfig:
    LLM_API_KEY = os.getenv('LLM_API_KEY')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL')
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini')
    ZEP_API_KEY = os.getenv('ZEP_API_KEY')
    
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5001'))
    FLASK_DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    DEFAULT_MAX_ROUNDS = int(os.getenv('DEFAULT_MAX_ROUNDS', '144'))
    DEFAULT_MINUTES_PER_ROUND = int(os.getenv('DEFAULT_MINUTES_PER_ROUND', '60'))
    DEFAULT_ACTIVE_AGENTS_MIN = int(os.getenv('DEFAULT_ACTIVE_AGENTS_MIN', '5'))
    DEFAULT_ACTIVE_AGENTS_MAX = int(os.getenv('DEFAULT_ACTIVE_AGENTS_MAX', '20'))
    
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '52428800'))
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/polytheater.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
