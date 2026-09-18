from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.gemini_client import embed_query
from app.models import ArticleChunk

settings = get_settings()


@dataclass
class RetrievedChunk:
    kind: str
    number: str
    citation: str
    titulo: str | None
    capitulo: str | None
    source_url: str | None
    text: str
    similarity: float


def retrieve(db: Session, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Búsqueda por similitud coseno en pgvector. Devuelve los top_k chunks
    más parecidos junto con su similitud (1 = idéntico, 0 = sin relación),
    para que quien llame pueda decidir si hay suficiente evidencia o no."""
    k = top_k or settings.retrieval_top_k
    query_embedding = embed_query(query)

    # pgvector "<=>" es distancia coseno (0 = idéntico, 2 = opuesto);
    # similitud = 1 - distancia.
    distance = ArticleChunk.embedding.cosine_distance(query_embedding)
    stmt = select(ArticleChunk, distance.label("distance")).order_by(distance).limit(k)

    results = db.execute(stmt).all()
    return [
        RetrievedChunk(
            kind=row.ArticleChunk.kind,
            number=row.ArticleChunk.number,
            citation=row.ArticleChunk.citation,
            titulo=row.ArticleChunk.titulo,
            capitulo=row.ArticleChunk.capitulo,
            source_url=row.ArticleChunk.source_url,
            text=row.ArticleChunk.text,
            similarity=1 - row.distance,
        )
        for row in results
    ]


def best_similarity(chunks: list[RetrievedChunk]) -> float:
    return max((c.similarity for c in chunks), default=0.0)


def has_enough_evidence(chunks: list[RetrievedChunk]) -> bool:
    return best_similarity(chunks) >= settings.min_similarity
