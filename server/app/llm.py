"""Cliente de Gemini: único módulo que conoce el SDK del proveedor."""
from typing import Iterator

from google import genai
from google.genai import types

from app.config import Settings


class GeminiClient:
    def __init__(self, settings: Settings):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    def stream(self, system_prompt: str, user_message: str) -> Iterator[str]:
        response = self._client.models.generate_content_stream(
            model=self._model,
            contents=user_message,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
