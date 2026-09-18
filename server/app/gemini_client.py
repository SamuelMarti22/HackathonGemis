import time
from collections.abc import Iterator
from functools import lru_cache

from google import genai
from google.genai import types
from google.genai.errors import ServerError

from app.config import get_settings

settings = get_settings()

MAX_RETRIES = 4
BASE_DELAY_SECONDS = 2.0


@lru_cache
def get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _with_retry(fn):
    """Gemini devuelve 503 (modelo con alta demanda) con cierta frecuencia
    incluso en condiciones normales; reintenta con backoff antes de fallar."""
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except ServerError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(BASE_DELAY_SECONDS * (2**attempt))
    raise RuntimeError("unreachable")


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embeddings para indexar (guardar en la base de datos)."""
    client = get_client()

    def call():
        return client.models.embed_content(
            model=settings.embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=settings.embedding_dim,
            ),
        )

    return [e.values for e in _with_retry(call).embeddings]


def embed_query(text: str) -> list[float]:
    """Embedding para una pregunta/caso del usuario."""
    client = get_client()

    def call():
        return client.models.embed_content(
            model=settings.embedding_model,
            contents=[text],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=settings.embedding_dim,
            ),
        )

    return _with_retry(call).embeddings[0].values


def stream_text(prompt: str, system_instruction: str) -> Iterator[str]:
    client = get_client()
    config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)

    for attempt in range(MAX_RETRIES):
        yielded_anything = False
        try:
            for chunk in client.models.generate_content_stream(
                model=settings.chat_model, contents=prompt, config=config
            ):
                if chunk.text:
                    yielded_anything = True
                    yield chunk.text
            return
        except ServerError:
            # Sólo es seguro reintentar si todavía no se le mostró nada al
            # usuario (si no, reintentar duplicaría el resumen).
            if yielded_anything or attempt == MAX_RETRIES - 1:
                raise
            time.sleep(BASE_DELAY_SECONDS * (2**attempt))


def generate_json(prompt: str, system_instruction: str, json_schema: dict) -> str:
    client = get_client()

    def call():
        return client.models.generate_content(
            model=settings.chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                response_mime_type="application/json",
                response_json_schema=json_schema,
            ),
        )

    return _with_retry(call).text
