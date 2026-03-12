# src/deployment/config.py
"""Production configuration management."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: str = "deepseek"
    api_key: str = ""
    model: str = "deepseek-chat"
    max_tokens: int = 4000
    temperature: float = 0.7
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class MemoryConfig:
    """Memory system configuration."""
    backend: str = "file"
    base_path: str = "data/memory"
    max_context_tokens: int = 8000
    cache_size: int = 1000


@dataclass
class PlatformConfig:
    """Platform configuration."""
    wattpad_api_key: str = ""
    royalroad_username: str = ""
    royalroad_password: str = ""
    kdp_access_key: str = ""
    kdp_secret_key: str = ""


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    enabled: bool = True
    daily_chapter_time: str = "08:00"
    comment_check_interval: int = 3600  # seconds
    max_retries: int = 3


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    log_level: str = "INFO"
    alert_webhook: str = ""
    cost_alert_threshold: float = 10.0  # dollars


@dataclass
class AppConfig:
    """Main application configuration."""
    app_name: str = "NovelAgent"
    version: str = "1.0.0"
    debug: bool = False
    llm: LLMConfig = field(default_factory=LLMConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    platforms: PlatformConfig = field(default_factory=PlatformConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "deepseek"),
                api_key=os.getenv("DEEPSEEK_API_KEY", os.getenv("LLM_API_KEY", "")),
                model=os.getenv("LLM_MODEL", "deepseek-chat"),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            ),
            memory=MemoryConfig(
                backend=os.getenv("MEMORY_BACKEND", "file"),
                base_path=os.getenv("MEMORY_PATH", "data/memory"),
            ),
            platforms=PlatformConfig(
                wattpad_api_key=os.getenv("WATTPAD_API_KEY", ""),
                royalroad_username=os.getenv("ROYALROAD_USERNAME", ""),
                royalroad_password=os.getenv("ROYALROAD_PASSWORD", ""),
                kdp_access_key=os.getenv("KDP_ACCESS_KEY", ""),
                kdp_secret_key=os.getenv("KDP_SECRET_KEY", ""),
            ),
            scheduler=SchedulerConfig(
                enabled=os.getenv("SCHEDULER_ENABLED", "true").lower() == "true",
                daily_chapter_time=os.getenv("DAILY_CHAPTER_TIME", "08:00"),
            ),
            monitoring=MonitoringConfig(
                enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                alert_webhook=os.getenv("ALERT_WEBHOOK", ""),
            ),
        )

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        """Load configuration from JSON file.

        Args:
            path: Path to config file

        Returns:
            AppConfig instance
        """
        config_path = Path(path)
        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            data = json.load(f)

        return cls(
            app_name=data.get("app_name", "NovelAgent"),
            version=data.get("version", "1.0.0"),
            debug=data.get("debug", False),
            llm=LLMConfig(**data.get("llm", {})),
            memory=MemoryConfig(**data.get("memory", {})),
            platforms=PlatformConfig(**data.get("platforms", {})),
            scheduler=SchedulerConfig(**data.get("scheduler", {})),
            monitoring=MonitoringConfig(**data.get("monitoring", {})),
        )

    def to_file(self, path: str) -> None:
        """Save configuration to JSON file.

        Args:
            path: Path to save config
        """
        data = {
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
            },
            "memory": {
                "backend": self.memory.backend,
                "base_path": self.memory.base_path,
            },
            "scheduler": {
                "enabled": self.scheduler.enabled,
                "daily_chapter_time": self.scheduler.daily_chapter_time,
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "log_level": self.monitoring.log_level,
            },
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def validate(self) -> list[str]:
        """Validate configuration.

        Returns:
            List of validation errors
        """
        errors = []

        if not self.llm.api_key:
            errors.append("LLM API key is required")

        if self.llm.temperature < 0 or self.llm.temperature > 2:
            errors.append("Temperature must be between 0 and 2")

        if self.llm.max_tokens < 100:
            errors.append("Max tokens must be at least 100")

        return errors


# Global configuration
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get global configuration."""
    global _config
    if _config is None:
        # Try file first, then environment
        config_path = os.getenv("CONFIG_PATH", "config.json")
        if Path(config_path).exists():
            _config = AppConfig.from_file(config_path)
        else:
            _config = AppConfig.from_env()
    return _config


def set_config(config: AppConfig) -> None:
    """Set global configuration."""
    global _config
    _config = config
