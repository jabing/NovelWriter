# tests/test_llm/test_deepseek.py
"""Tests for DeepSeek LLM integration."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from src.novel_agent.llm.base import LLMResponse
from src.novel_agent.llm.deepseek import DeepSeekLLM, _retry_with_backoff


class TestDeepSeekInitialization:
    """Tests for DeepSeekLLM initialization."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with explicit API key."""
        llm = DeepSeekLLM(api_key="test_key")
        assert llm.api_key == "test_key"
        assert llm.model == "deepseek-chat"
        assert llm.temperature == 0.7
        assert llm.max_tokens == 4096

    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        llm = DeepSeekLLM(
            api_key="test_key",
            model="deepseek-coder",
            temperature=0.5,
            max_tokens=2048,
            max_retries=5,
        )
        assert llm.model == "deepseek-coder"
        assert llm.temperature == 0.5
        assert llm.max_tokens == 2048
        assert llm._max_retries == 5

    def test_init_requires_api_key(self) -> None:
        """Test that API key is required."""
        # Clear environment variable
        old_val = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="DeepSeek API key required"):
                DeepSeekLLM()
        finally:
            if old_val:
                os.environ["DEEPSEEK_API_KEY"] = old_val

    def test_init_from_env(self) -> None:
        """Test initialization from environment variable."""
        old_val = os.environ.get("DEEPSEEK_API_KEY")
        os.environ["DEEPSEEK_API_KEY"] = "env_key"
        try:
            llm = DeepSeekLLM()
            assert llm.api_key == "env_key"
        finally:
            if old_val:
                os.environ["DEEPSEEK_API_KEY"] = old_val
            else:
                os.environ.pop("DEEPSEEK_API_KEY", None)


class TestTokenCounting:
    """Tests for token counting functionality."""

    def test_initial_token_count(self) -> None:
        """Test that initial token count is zero."""
        llm = DeepSeekLLM(api_key="test_key")
        assert llm.total_tokens_used == 0

    def test_reset_token_count(self) -> None:
        """Test resetting token count."""
        llm = DeepSeekLLM(api_key="test_key")
        llm._total_tokens_used = 1000
        llm.reset_token_count()
        assert llm.total_tokens_used == 0


class TestRetryLogic:
    """Tests for retry with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_try(self) -> None:
        """Test that successful call doesn't retry."""
        call_count = 0

        async def success_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await _retry_with_backoff(success_func, max_retries=3)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self) -> None:
        """Test retry on failure."""
        call_count = 0

        async def fail_then_succeed() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await _retry_with_backoff(
            fail_then_succeed,
            max_retries=3,
            base_delay=0.01,  # Fast for testing
        )
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        """Test that exception is raised after all retries."""
        call_count = 0

        async def always_fail() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            await _retry_with_backoff(
                always_fail,
                max_retries=3,
                base_delay=0.01,
            )
        assert call_count == 3


class TestGenerateMethods:
    """Tests for generate methods."""

    @pytest.mark.asyncio
    async def test_generate_calls_generate_with_system(self) -> None:
        """Test that generate calls generate_with_system with default system prompt."""
        llm = DeepSeekLLM(api_key="test_key")

        with patch.object(llm, 'generate_with_system', new_callable=AsyncMock) as mock:
            mock.return_value = LLMResponse(
                content="test content",
                tokens_used=100,
                model="deepseek-chat",
            )

            result = await llm.generate("test prompt")

            mock.assert_called_once()
            assert mock.call_args[1]["system_prompt"] == "You are a creative fiction writer."
            assert mock.call_args[1]["user_prompt"] == "test prompt"
            assert result.content == "test content"

    @pytest.mark.asyncio
    async def test_sync_wrapper(self) -> None:
        """Test synchronous wrapper exists and is callable."""
        # Note: We can't actually test sync wrapper in async context
        # because asyncio.run() cannot be called from running event loop
        # Just verify the method exists
        llm = DeepSeekLLM(api_key="test_key")
        assert hasattr(llm, 'generate_sync')
        assert callable(llm.generate_sync)


class TestOpenAICompatibility:
    """Tests for OpenAI API compatibility."""

    def test_base_url(self) -> None:
        """Test correct DeepSeek base URL."""
        assert DeepSeekLLM.BASE_URL == "https://api.deepseek.com/v1"

    def test_available_models(self) -> None:
        """Test available models are defined."""
        assert "deepseek-chat" in DeepSeekLLM.MODELS
        assert "deepseek-coder" in DeepSeekLLM.MODELS
