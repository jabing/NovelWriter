# tests/test_deployment/test_config.py
"""Tests for deployment configuration."""

import json
import os
import tempfile

import pytest

from src.deployment.config import (
    AppConfig,
    LLMConfig,
    MemoryConfig,
    get_config,
    set_config,
)


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_llm_config_defaults(self) -> None:
        """Test default values."""
        config = LLMConfig()

        assert config.provider == "deepseek"
        assert config.api_key == ""
        assert config.model == "deepseek-chat"
        assert config.max_tokens == 4000
        assert config.temperature == 0.7

    def test_llm_config_custom(self) -> None:
        """Test custom values."""
        config = LLMConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
            max_tokens=2000,
            temperature=0.5,
        )

        assert config.provider == "openai"
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.max_tokens == 2000
        assert config.temperature == 0.5


class TestMemoryConfig:
    """Tests for MemoryConfig."""

    def test_memory_config_defaults(self) -> None:
        """Test default values."""
        config = MemoryConfig()

        assert config.backend == "file"
        assert config.base_path == "data/memory"

    def test_memory_config_custom(self) -> None:
        """Test custom values."""
        config = MemoryConfig(
            backend="redis",
            base_path="/custom/path",
        )

        assert config.backend == "redis"
        assert config.base_path == "/custom/path"


class TestAppConfig:
    """Tests for AppConfig."""

    def test_app_config_defaults(self) -> None:
        """Test default values."""
        config = AppConfig()

        assert config.app_name == "NovelAgent"
        assert config.version == "1.0.0"
        assert config.debug is False
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.memory, MemoryConfig)

    def test_app_config_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading from environment."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")
        monkeypatch.setenv("LLM_MODEL", "custom-model")
        monkeypatch.setenv("DEBUG", "true")

        config = AppConfig.from_env()

        assert config.llm.api_key == "test-api-key"
        assert config.llm.model == "custom-model"
        assert config.debug is True

    def test_app_config_from_file(self) -> None:
        """Test loading from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "app_name": "TestApp",
                "debug": True,
                "llm": {
                    "provider": "test",
                    "model": "test-model",
                },
            }, f)
            config_path = f.name

        try:
            config = AppConfig.from_file(config_path)

            assert config.app_name == "TestApp"
            assert config.debug is True
            assert config.llm.provider == "test"
            assert config.llm.model == "test-model"
        finally:
            os.unlink(config_path)

    def test_app_config_to_file(self) -> None:
        """Test saving to file."""
        config = AppConfig(
            app_name="SaveTest",
            debug=True,
            llm=LLMConfig(api_key="test-key"),
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = f.name

        try:
            config.to_file(config_path)

            with open(config_path) as f:
                data = json.load(f)

            assert data["app_name"] == "SaveTest"
            assert data["debug"] is True
        finally:
            os.unlink(config_path)

    def test_app_config_validate_valid(self) -> None:
        """Test validation with valid config."""
        config = AppConfig(
            llm=LLMConfig(api_key="test-key")
        )

        errors = config.validate()

        assert len(errors) == 0

    def test_app_config_validate_missing_key(self) -> None:
        """Test validation with missing API key."""
        config = AppConfig()

        errors = config.validate()

        assert "LLM API key is required" in errors

    def test_app_config_validate_invalid_temperature(self) -> None:
        """Test validation with invalid temperature."""
        config = AppConfig(
            llm=LLMConfig(api_key="test-key", temperature=3.0)
        )

        errors = config.validate()

        assert any("Temperature" in e for e in errors)


class TestGlobalConfig:
    """Tests for global configuration."""

    def test_set_and_get_config(self) -> None:
        """Test setting and getting global config."""
        config = AppConfig(app_name="TestGlobal")
        set_config(config)

        result = get_config()

        assert result.app_name == "TestGlobal"
