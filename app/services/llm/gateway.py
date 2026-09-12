import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.services.llm.types import (
    LLMResult,
    LLMUsage,
)


class LLMServiceError(RuntimeError):
    pass


def ns_to_ms(
    value: int | float | None,
) -> float | None:
    if value is None:
        return None

    return float(value) / 1_000_000


class OllamaGateway:
    """
    Single application-level gateway for Ollama.

    Business services should not call Ollama directly.
    """

    def __init__(self) -> None:
        self.base_url = (
            settings.ollama_base_url.rstrip("/")
        )

        self.model = (
            settings.ollama_model
        )

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=120.0,
                write=30.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=60.0,
            ),
        )

    async def health(self) -> bool:
        try:
            response = await self.client.get(
                f"{self.base_url}/api/tags"
            )

            return response.is_success

        except httpx.HTTPError:
            return False

    async def warmup(self) -> None:
        """
        Load the primary model into memory.
        """

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "",
                    "stream": False,
                    "keep_alive": "30m",
                },
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise LLMServiceError(
                f"Unable to warm Ollama model: {exc}"
            ) from exc

    async def chat(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        num_predict: int = 256,
    ) -> LLMResult:

        started = time.perf_counter()

        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "keep_alive": "30m",
                    "options": {
                        "temperature": temperature,
                        "num_predict": num_predict,
                    },
                },
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise LLMServiceError(
                f"Ollama chat request failed: {exc}"
            ) from exc

        payload = response.json()

        wall_ms = (
            time.perf_counter()
            - started
        ) * 1000

        content = (
            payload
            .get("message", {})
            .get("content", "")
        )

        usage = self._usage_from_payload(
            payload
        )

        if (
            usage.total_duration_ms
            is None
        ):
            usage.total_duration_ms = (
                wall_ms
            )

        return LLMResult(
            content=content,
            usage=usage,
        )

    async def structured(
        self,
        *,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        model: str | None = None,
    ) -> BaseModel:

        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": (
                        model
                        or self.model
                    ),
                    "messages": messages,
                    "stream": False,
                    "format": (
                        schema.model_json_schema()
                    ),
                    "keep_alive": "30m",
                    "options": {
                        "temperature": 0,
                        "num_predict": 80,
                        "num_ctx": 1024,
                    },
                },
                timeout=httpx.Timeout(
                    connect=2.0,
                    read=2.5,
                    write=3.0,
                    pool=2.0,
                ),
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise LLMServiceError(
                f"Ollama structured request failed: {exc}"
            ) from exc

        payload = response.json()

        raw = (
            payload
            .get("message", {})
            .get("content", "")
        )

        try:
            return schema.model_validate_json(
                raw
            )

        except Exception as exc:
            raise LLMServiceError(
                "Ollama returned invalid structured output."
            ) from exc

    async def stream_chat(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        num_predict: int = 384,
    ) -> AsyncIterator[str]:

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": "30m",
                    "options": {
                        "temperature": temperature,
                        "num_predict": num_predict,
                    },
                },
            ) as response:

                response.raise_for_status()

                async for line in response.aiter_lines():

                    if not line:
                        continue

                    payload: dict[str, Any] = (
                        json.loads(line)
                    )

                    content = (
                        payload
                        .get("message", {})
                        .get("content", "")
                    )

                    if content:
                        yield content

                    if payload.get(
                        "done"
                    ):
                        break

        except (
            httpx.HTTPError,
            json.JSONDecodeError,
        ) as exc:
            raise LLMServiceError(
                f"Ollama streaming failed: {exc}"
            ) from exc

    @staticmethod
    def _usage_from_payload(
        payload: dict[str, Any],
    ) -> LLMUsage:

        eval_count = payload.get(
            "eval_count"
        )

        eval_duration = payload.get(
            "eval_duration"
        )

        tokens_per_second = None

        if (
            eval_count
            and eval_duration
            and eval_duration > 0
        ):
            tokens_per_second = (
                eval_count
                / (
                    eval_duration
                    / 1_000_000_000
                )
            )

        return LLMUsage(
            model=payload.get(
                "model",
                "unknown",
            ),

            total_duration_ms=ns_to_ms(
                payload.get(
                    "total_duration"
                )
            ),

            load_duration_ms=ns_to_ms(
                payload.get(
                    "load_duration"
                )
            ),

            prompt_tokens=payload.get(
                "prompt_eval_count"
            ),

            prompt_duration_ms=ns_to_ms(
                payload.get(
                    "prompt_eval_duration"
                )
            ),

            completion_tokens=eval_count,

            completion_duration_ms=ns_to_ms(
                eval_duration
            ),

            tokens_per_second=(
                tokens_per_second
            ),
        )


llm_gateway = OllamaGateway()
