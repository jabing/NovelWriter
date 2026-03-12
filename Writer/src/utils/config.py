# src/utils/config.py
"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Settings
    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    default_llm_model: str = Field(default="deepseek-chat", description="Default LLM model")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, ge=1)

    # Memory Settings
    openviking_data_dir: str = Field(
        default="data/openviking", description="OpenViking data directory"
    )

    # Vector Store Settings
    vector_store_type: str = Field(
        default="chroma", description="Vector store type: 'chroma' or 'pinecone'"
    )

    # Chroma Settings
    chroma_persist_path: str = Field(
        default="data/chroma", description="Chroma persistence directory"
    )
    chroma_collection_name: str = Field(
        default="novel-facts", description="Chroma collection name"
    )
    chroma_embedding_model: str = Field(
        default="shibing624/text2vec-base-multilingual",
        description="Chroma embedding model"
    )

    # Milvus Settings (备用向量存储)
    milvus_enabled: bool = Field(
        default=False, description="Enable Milvus vector store"
    )
    milvus_uri: str = Field(
        default="~/.memsearch/milvus.db", description="Milvus connection URI"
    )

    # Redis Settings (for Celery)
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL for Celery")

    # PostgreSQL Settings
    postgres_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/novel_agent",
        description="PostgreSQL database URL",
    )

    # Platform API Keys
    wattpad_api_key: str = Field(default="")
    wattpad_api_secret: str = Field(default="")
    royalroad_username: str = Field(default="")
    royalroad_password: str = Field(default="")

    # Publishing Settings
    auto_publish: bool = Field(default=False, description="Automatically publish after writing")
    default_platform: Literal["wattpad", "royalroad", "kindle"] = Field(default="wattpad")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_file: str = Field(default="logs/novel-agent.log")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
