"""Lógica del tutor jurídico: orquesta prompt + LLM. Aquí se enchufarán memoria y RAG."""
from typing import Iterator

from app.llm import GeminiClient
from app.prompts import load_prompt


class LegalTutor:
    def __init__(self, llm: GeminiClient):
        self._llm = llm
        self._system_prompt = load_prompt("system_prompt")

    def answer(self, case: str) -> Iterator[str]:
        return self._llm.stream(self._system_prompt, case)
