"""
Genera embeddings para cada artículo (parseado por parse_constitution.py) y
los carga en Postgres/pgvector.

Requiere que ya existan:
  - server/data/articles.json       (python -m ingest.parse_constitution)
  - server/data/article_links.json  (python -m ingest.build_article_links)

Uso:
    python -m ingest.ingest [--reset]

--reset borra todos los fragmentos existentes antes de insertar (útil al
volver a correr la ingesta tras cambiar el chunking o el modelo de embeddings).
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from google.genai.errors import ClientError

from app.db import SessionLocal, init_db
from app.gemini_client import embed_documents
from app.models import ArticleChunk
from ingest.chunking import chunk_text

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ARTICLES_PATH = DATA_DIR / "articles.json"
LINKS_PATH = DATA_DIR / "article_links.json"

RETRY_DELAY_RE = re.compile(r"'retryDelay':\s*'(\d+(?:\.\d+)?)s'")


def embed_with_retry(texts: list[str], max_retries: int = 8) -> list[list[float]]:
    """La cuota gratuita de embed_content es baja (~100 items/min): reintenta
    con el retryDelay que sugiere la API en vez de abortar la ingesta."""
    for attempt in range(max_retries):
        try:
            return embed_documents(texts)
        except ClientError as exc:
            if exc.code != 429 or attempt == max_retries - 1:
                raise
            match = RETRY_DELAY_RE.search(str(exc))
            delay = float(match.group(1)) + 1 if match else 15.0
            print(f"  rate limit, esperando {delay:.0f}s ...")
            time.sleep(delay)
    raise RuntimeError("unreachable")

EMBED_BATCH_SIZE = 10
PAUSE_BETWEEN_BATCHES_SECONDS = 3.0


def resolve_url(links: dict, kind: str, number: str) -> str | None:
    table = links.get(kind, {})
    if number in table:
        return table[number]
    return links.get("fallback_url")


def build_rows(articles: list[dict], links: dict) -> list[dict]:
    rows = []
    for art in articles:
        pieces = chunk_text(art["text"])
        url = resolve_url(links, art["kind"], art["number"])
        for idx, piece in enumerate(pieces):
            rows.append(
                {
                    "kind": art["kind"],
                    "number": art["number"],
                    "citation": art["citation"],
                    "titulo": art.get("titulo"),
                    "capitulo": art.get("capitulo"),
                    "source_url": url,
                    "chunk_index": idx,
                    "chunk_count": len(pieces),
                    "text": piece,
                }
            )
    return rows


def batched(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> None:
    reset = "--reset" in sys.argv

    if not ARTICLES_PATH.exists():
        sys.exit(f"No existe {ARTICLES_PATH}. Corre primero: python -m ingest.parse_constitution")
    if not LINKS_PATH.exists():
        sys.exit(f"No existe {LINKS_PATH}. Corre primero: python -m ingest.build_article_links")

    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    links = json.loads(LINKS_PATH.read_text(encoding="utf-8"))

    print("Preparando base de datos (extensión pgvector + tablas) ...")
    init_db()

    print("Generando fragmentos ...")
    rows = build_rows(articles, links)
    print(f"  -> {len(rows)} fragmentos a partir de {len(articles)} artículos")

    db = SessionLocal()
    try:
        if reset:
            print("Borrando fragmentos existentes ...")
            db.query(ArticleChunk).delete()
            db.commit()

        print("Generando embeddings e insertando (esto llama a la API de Gemini) ...")
        inserted = 0
        for batch in batched(rows, EMBED_BATCH_SIZE):
            texts = [r["text"] for r in batch]
            embeddings = embed_with_retry(texts)
            for row, embedding in zip(batch, embeddings, strict=True):
                db.add(ArticleChunk(**row, embedding=embedding))
            db.commit()
            inserted += len(batch)
            print(f"  {inserted}/{len(rows)}")
            time.sleep(PAUSE_BETWEEN_BATCHES_SECONDS)

        print("Listo.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
