# src/novel_agent/utils/config.py
"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.novel_agent.novel.continuity_config import ContinuityConfig

LLMProviderType = Literal["deepseek", "infini", "glm", "bailian", "volcengine", "kimi", "gemini"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Provider Selection
    llm_provider: LLMProviderType = Field(
        default="deepseek",
        description="LLM provider: deepseek, infini, glm, bailian, volcengine, kimi, gemini",
    )

    # DeepSeek Settings
    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API base URL",
    )

    # Infini AI Settings
    infini_api_key: str = Field(default="", description="Infini AI API key")
    infini_base_url: str = Field(
        default="https://cloud.infini-ai.com/maas/coding/v1",
        description="Infini AI API base URL",
    )

    # Zhipu GLM Settings
    zhipu_api_key: str = Field(default="", description="Zhipu AI (GLM) API key")
    zhipu_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        description="Zhipu GLM API base URL",
    )

    # Bailian (阿里百炼) Settings
    bailian_api_key: str = Field(default="", description="Bailian (阿里百炼) API key")
    bailian_base_url: str = Field(
        default="",
        description="Bailian API base URL (optional, uses default if empty)",
    )

    # Volcengine (火山引擎) Settings
    volcengine_api_key: str = Field(default="", description="Volcengine API key")
    volcengine_base_url: str = Field(
        default="",
        description="Volcengine API base URL (optional, uses default if empty)",
    )

    # Kimi (Moonshot) Settings
    kimi_api_key: str = Field(default="", description="Kimi/Moonshot API key")
    kimi_base_url: str = Field(
        default="https://api.moonshot.cn/v1",
        description="Kimi API base URL",
    )

    # Gemini Settings
    gemini_api_key: str = Field(default="", description="Gemini API key")
    gemini_base_url: str = Field(
        default="https://api.laozhang.ai/v1",
        description="Gemini API base URL (or proxy)",
    )

    # Default LLM Settings
    default_llm_model: str = Field(
        default="", description="Default LLM model (empty = use provider default)"
    )
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
    chroma_collection_name: str = Field(default="novel-facts", description="Chroma collection name")
    chroma_embedding_model: str = Field(
        default="shibing624/text2vec-base-multilingual", description="Chroma embedding model"
    )

    # Milvus Settings (备用向量存储)
    milvus_enabled: bool = Field(default=False, description="Enable Milvus vector store")
    milvus_uri: str = Field(default="~/.memsearch/milvus.db", description="Milvus connection URI")

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

    # Continuity Settings
    continuity_config: ContinuityConfig = Field(
        default_factory=ContinuityConfig, description="Continuity checking configuration"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def create_llm_from_config(
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> "BaseLLM":
    """Create LLM instance from configuration.

    Args:
        provider: LLM provider (defaults to llm_provider from config)
        model: Model name (defaults to default_llm_model or provider default)
        temperature: Temperature (defaults to llm_temperature from config)
        max_tokens: Max tokens (defaults to llm_max_tokens from config)

    Returns:
        BaseLLM instance configured according to settings

    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    from src.novel_agent.llm.base import BaseLLM
    from src.novel_agent.llm.bailian import BailianLLM
    from src.novel_agent.llm.deepseek import DeepSeekLLM
    from src.novel_agent.llm.gemini import GeminiLLM
    from src.novel_agent.llm.glm import GLMLLM
    from src.novel_agent.llm.infini import InfiniAILLM
    from src.novel_agent.llm.kimi import KimiLLM
    from src.novel_agent.llm.volcengine import VolcengineLLM

    settings = get_settings()

    provider = provider or settings.llm_provider
    temperature = temperature if temperature is not None else settings.llm_temperature
    max_tokens = max_tokens or settings.llm_max_tokens

    provider_configs = {
        "deepseek": {
            "class": DeepSeekLLM,
            "api_key": settings.deepseek_api_key,
            "base_url": settings.deepseek_base_url,
            "default_model": "deepseek-chat",
            "supports_base_url": False,
            "env_var": "DEEPSEEK_API_KEY",
        },
        "infini": {
            "class": InfiniAILLM,
            "api_key": settings.infini_api_key,
            "base_url": settings.infini_base_url,
            "default_model": "Qwen/Qwen3-235B-A22B",
            "supports_base_url": True,
            "env_var": "INFINI_API_KEY",
        },
        "glm": {
            "class": GLMLLM,
            "api_key": settings.zhipu_api_key,
            "base_url": settings.zhipu_base_url,
            "default_model": "glm-4-plus",
            "supports_base_url": False,
            "env_var": "ZHIPU_API_KEY",
        },
        "bailian": {
            "class": BailianLLM,
            "api_key": settings.bailian_api_key,
            "base_url": settings.bailian_base_url or None,
            "default_model": "qwen-turbo",
            "supports_base_url": True,
            "env_var": "BAILIAN_API_KEY",
        },
        "volcengine": {
            "class": VolcengineLLM,
            "api_key": settings.volcengine_api_key,
            "base_url": settings.volcengine_base_url or None,
            "default_model": "doubao-pro-32k",
            "supports_base_url": True,
            "env_var": "VOLCENGINE_API_KEY",
        },
        "kimi": {
            "class": KimiLLM,
            "api_key": settings.kimi_api_key,
            "base_url": settings.kimi_base_url,
            "default_model": "moonshot-v1-8k",
            "supports_base_url": True,
            "env_var": "KIMI_API_KEY",
        },
        "gemini": {
            "class": GeminiLLM,
            "api_key": settings.gemini_api_key,
            "base_url": settings.gemini_base_url,
            "default_model": "gemini-1.5-flash",
            "supports_base_url": True,
            "env_var": "GEMINI_API_KEY",
        },
    }

    if provider not in provider_configs:
        raise ValueError(
            f"Unknown LLM provider: {provider}. Supported: {list(provider_configs.keys())}"
        )

    config = provider_configs[provider]

    if not config["api_key"]:
        raise ValueError(
            f"API key not configured for provider '{provider}'. "
            f"Set {config['env_var']} in environment or .env file."
        )

    final_model = model or settings.default_llm_model or config["default_model"]

    llm_class = config["class"]
    kwargs: dict = {
        "api_key": config["api_key"],
        "model": final_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if config.get("supports_base_url", False) and config["base_url"]:
        kwargs["base_url"] = config["base_url"]

    return llm_class(**kwargs)


def get_default_llm() -> "BaseLLM":
    """Get default LLM instance based on configuration.

    Convenience function that calls create_llm_from_config with defaults.

    Returns:
        BaseLLM instance configured according to settings
    """
    return create_llm_from_config()
