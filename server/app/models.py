from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.db import Base

settings = get_settings()


class ArticleChunk(Base):
    """Un fragmento indexado de un artículo (o de un artículo transitorio) de
    la Constitución. Un artículo largo puede partirse en varios chunks; todos
    comparten kind/number/citation/source_url para que la cita mostrada al
    usuario sea siempre la del artículo completo, sin importar qué fragmento
    fue el que hizo match en la búsqueda."""

    __tablename__ = "article_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    kind: Mapped[str] = mapped_column(String(20))  # "articulo" | "transitorio"
    number: Mapped[str] = mapped_column(String(20))  # "100", "s/n-2"
    citation: Mapped[str] = mapped_column(String(120))  # "Artículo 100"
    titulo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    capitulo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=1)
    text: Mapped[str] = mapped_column(Text)

    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim))


Index(
    "ix_article_chunks_embedding",
    ArticleChunk.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)

Index("ix_article_chunks_kind_number", ArticleChunk.kind, ArticleChunk.number)
