"""División de artículos largos en fragmentos aptos para embeddings.

gemini-embedding-001 trunca la entrada más allá de cierto largo, así que un
artículo muy extenso (ej. el 361, sobre regalías) pierde recall si se indexa
como un solo vector. Se parte en fragmentos por párrafo, con solapamiento
para no cortar una idea a la mitad."""

from __future__ import annotations

MAX_CHARS = 1500
OVERLAP_CHARS = 200


def chunk_text(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n")
    chunks: list[str] = []
    current = ""

    def push_current() -> None:
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        push_current()
        current = paragraph
        # Párrafo individual más largo que max_chars: cortar duro con solapamiento.
        while len(current) > max_chars:
            chunks.append(current[:max_chars])
            current = current[max_chars - overlap :]

    push_current()
    return chunks
