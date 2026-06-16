"""Cliente reutilizable para OpenRouter (chat/razonamiento).

Usa ``langchain-openai`` con base URL de OpenRouter. No usar Gemini aquí.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Error al invocar o parsear respuesta del LLM."""


class LLMClient(ABC):
    """Contrato mockeable para todos los agentes."""

    @abstractmethod
    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """Invoca el LLM y valida la respuesta contra un modelo Pydantic."""

    @abstractmethod
    async def complete_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Invoca el LLM y retorna texto plano."""


def _extract_json(text: str) -> dict[str, Any]:
    """Extrae JSON de respuesta cruda (incluye bloques markdown)."""
    text = text.strip()
    # Limpiar tokens de padding que algunos modelos gratuitos emiten
    text = re.sub(r"<\|?pad\|?>", "", text, flags=re.IGNORECASE)
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Respuesta no es JSON válido: {exc}") from exc
    if not isinstance(parsed, dict):
        raise LLMError("Se esperaba un objeto JSON en la raíz.")
    return parsed


class OpenRouterLLMClient(LLMClient):
    """Implementación production-ready contra OpenRouter."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._chat = ChatOpenAI(
            model=self._settings.openrouter_chat_model,
            openai_api_key=self._settings.openrouter_api_key,
            openai_api_base=self._settings.openrouter_base_url,
            temperature=0.2,
            max_retries=0,
        )
        self._max_attempts = self._settings.openrouter_max_retries

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        @retry(
            retry=retry_if_exception_type((LLMError, ValidationError)),
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=32),
            reraise=True,
        )
        async def _invoke() -> T:
            json_instruction = (
                "Responde ÚNICAMENTE con un objeto JSON válido, sin markdown ni texto extra. "
                f"Debe cumplir el schema: {response_model.model_json_schema()}"
            )
            messages = [
                SystemMessage(content=f"{system_prompt}\n\n{json_instruction}"),
                HumanMessage(content=user_prompt),
            ]
            try:
                response = await self._chat.ainvoke(messages)
            except Exception as exc:
                logger.exception("Fallo de red/API OpenRouter")
                raise LLMError("Error al invocar OpenRouter") from exc

            content = response.content
            if not isinstance(content, str):
                raise LLMError("Respuesta vacía o no textual del LLM.")
            data = _extract_json(content)
            return response_model.model_validate(data)

        return await _invoke()

    async def complete_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        try:
            response = await self._chat.ainvoke(messages)
        except Exception as exc:
            raise LLMError("Error al invocar OpenRouter") from exc
        content = response.content
        if not isinstance(content, str) or not content.strip():
            raise LLMError("Respuesta vacía del LLM.")
        return content.strip()


class MockLLMClient(LLMClient):
    """Cliente determinista para tests unitarios."""

    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self._responses = responses or {}
        self.calls: list[dict[str, str]] = []

    def register(self, key: str, payload: dict[str, Any]) -> None:
        self._responses[key] = payload

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        self.calls.append({"system": system_prompt, "user": user_prompt})
        for key, payload in self._responses.items():
            if key in user_prompt or key in system_prompt:
                return response_model.model_validate(payload)
        if "default" in self._responses:
            return response_model.model_validate(self._responses["default"])
        raise LLMError(f"No hay respuesta mock registrada para: {user_prompt[:80]}")

    async def complete_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        self.calls.append({"system": system_prompt, "user": user_prompt})
        if "default_text" in self._responses:
            return str(self._responses["default_text"])
        return "mock text response"
