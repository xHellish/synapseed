"""Tests del cliente LLM (parseo JSON y errores explícitos)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from app.config import Settings
from app.services.llm_client import LLMError, OpenRouterLLMClient, _extract_json


def test_extract_json_invalid_raises_llm_error():
    with pytest.raises(LLMError, match="JSON válido"):
        _extract_json("esto no es json {")


def test_extract_json_non_object_raises_llm_error():
    with pytest.raises(LLMError, match="objeto JSON"):
        _extract_json("[1, 2, 3]")


@pytest.mark.asyncio
async def test_openrouter_complete_json_invalid_response_raises():
    class SampleModel(BaseModel):
        name: str

    settings = Settings(
        openrouter_api_key="test-key",
        openrouter_base_url="https://openrouter.example/api/v1",
        openrouter_chat_model="test/model",
        openrouter_max_retries=1,
    )
    client = OpenRouterLLMClient(settings=settings)

    mock_response = MagicMock()
    mock_response.content = "respuesta libre sin json"
    mock_chat = MagicMock()
    mock_chat.ainvoke = AsyncMock(return_value=mock_response)
    client._chat = mock_chat

    with pytest.raises(LLMError, match="JSON"):
        await client.complete_json(
            system_prompt="system",
            user_prompt="user",
            response_model=SampleModel,
        )
