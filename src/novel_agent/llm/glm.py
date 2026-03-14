"""GLM LLM implementation for Zhipu AI."""

import os
from typing import Any

from src.novel_agent.llm.base import BaseLLM, LLMResponse
from src.novel_agent.monitoring import async_trace, async_track_errors, timer


class GLMLLM(BaseLLM):
    """GLM LLM client for Zhipu AI."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "glm-5",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        """Initialize GLM client."""
        api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError("ZHIPU_API_KEY required")

        super().__init__(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
        )
        self._client = None

    def _get_client(self):
        """Lazy initialization of Zhipu client."""
        if self._client is None:
            try:
                from zhipuai import ZhipuAI
            except ImportError:
                # Fallback to OpenAI-compatible API
                from openai import OpenAI

                return OpenAI(api_key=self.api_key, base_url="https://open.bigmodel.cn/api/paas/v4")
            self._client = ZhipuAI(api_key=self.api_key)
        return self._client

    @timer("llm.generate.glm")
    @async_trace("llm.generate.glm")
    @async_track_errors()
    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from prompt."""
        return await self.generate_with_system(
            system_prompt="You are a helpful assistant.",
            user_prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @timer("llm.generate_with_system.glm")
    @async_trace("llm.generate_with_system.glm")
    @async_track_errors()
    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate with system and user prompts."""
        import asyncio

        client = self._get_client()

        # Run synchronous API call in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs,
            ),
        )

        content = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0

        self._total_tokens_used += tokens_used

        return LLMResponse(
            content=content,
            tokens_used=tokens_used,
            model=self.model,
            finish_reason=response.choices[0].finish_reason,
        )
