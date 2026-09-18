from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres + pgvector: fragmentos indexados de la Constitución (RAG).
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/tutor_juridico"

    # Mongo: historial de casos/mensajes (ver app/memory/).
    mongo_uri: str = "mongodb://localhost:27019"
    mongo_db: str = "tutor_juridico"

    gemini_api_key: str = ""
    chat_model: str = "gemini-flash-latest"
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768

    # Recuperación: cuántos artículos pasar como contexto y qué tan
    # parecido (similitud coseno, 0-1) debe ser el mejor resultado para
    # considerar que sí hay norma aplicable. Si el mejor resultado queda
    # por debajo, el bot debe admitir que no encontró norma y no inventar.
    retrieval_top_k: int = 6
    min_similarity: float = 0.55


@lru_cache
def get_settings() -> Settings:
    return Settings()
