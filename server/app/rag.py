"""
Orquestación del RAG del tutor jurídico.

Diseño anti-alucinación (el requisito explícito del proyecto: "según este
artículo, lo que procede es esto", nunca una norma inventada):

1. Recuperación: se buscan los `top_k` fragmentos más parecidos al caso en
   pgvector. Si ni el mejor resultado supera `min_similarity`, se responde
   directamente que no se encontró norma aplicable — nunca se le pide al
   modelo que "se las arregle" sin contexto.
2. El bloque CONTEXTO que ve el modelo enumera los artículos candidatos con
   su número exacto. El modelo sólo puede citar `numero_articulo` values que
   aparezcan ahí (se lo decimos explícitamente en el prompt).
3. Verificación programática: después de generar, se descarta cualquier
   norma citada cuyo (tipo, numero_articulo) no esté literalmente entre los
   candidatos recuperados. El modelo no elige ni conoce la URL ni el texto
   final citado al usuario — el backend los toma directamente de la base de
   datos a partir del número validado. Así, aunque el modelo "alucinara" un
   número, nunca se lo mostraríamos al usuario como si fuera real.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.gemini_client import generate_json, stream_text
from app.retrieval import RetrievedChunk, best_similarity, has_enough_evidence, retrieve
from app.schemas import (
    DISCLAIMER,
    NormaCitada,
    RespuestaJuridica,
    RespuestaJuridicaLLM,
)

RESUMEN_SYSTEM_PROMPT = """Eres un tutor jurídico que le explica a una persona sin formación \
legal, en español claro y cercano, qué significa en términos legales la situación que describe.

Reglas:
- Resume la situación en 3 a 6 frases, usando terminología jurídica básica pero explicada.
- No cites números de artículos todavía (eso se hace en otro paso).
- No des consejos legales definitivos ni digas "tienes razón" o "vas a ganar".
- No inventes hechos que la persona no mencionó.
- Deja claro, si aplica, que esto es una primera lectura y no una asesoría legal formal."""

NORMAS_SYSTEM_PROMPT = """Eres un tutor jurídico especializado en la Constitución Política de \
Colombia. Tu única fuente de verdad es la lista CANDIDATOS que se te da en cada mensaje: son \
artículos recuperados de una base de datos porque son semánticamente parecidos al caso.

Reglas estrictas (no negociables):
1. SOLO puedes usar como "numero_articulo" un valor que aparezca literalmente en CANDIDATOS, \
con el mismo "tipo" (articulo/transitorio). Nunca escribas de memoria un artículo que no esté \
en CANDIDATOS, aunque creas conocerlo.
2. Si ningún candidato aplica de verdad al caso, responde hay_normas_aplicables=false y deja \
normas_aplicables como lista vacía. Es preferible decir "no encontré una norma aplicable" que \
inventar una.
3. En "por_que_aplica" explica la conexión entre el texto del artículo (dado en CANDIDATOS) y \
los hechos del caso, en lenguaje sencillo.
4. Las recomendaciones deben ser pasos concretos y realizables (a quién acudir, qué documento \
presentar, qué plazo tener en cuenta), basados únicamente en lo que dicen los candidatos y el \
caso descrito. No des consejos genéricos que no se apoyen en el contexto."""


def _format_candidates(chunks: list[RetrievedChunk]) -> str:
    seen: set[tuple[str, str]] = set()
    lines = []
    for c in chunks:
        key = (c.kind, c.number)
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"- tipo={c.kind} | numero_articulo={c.number} | {c.citation}"
            f" ({c.titulo or 's/d'}{' - ' + c.capitulo if c.capitulo else ''})\n"
            f"  Texto: {c.text[:1200]}"
        )
    return "\n".join(lines)


def stream_resumen(caso: str) -> Iterator[str]:
    prompt = f'Situación descrita por la persona:\n"""\n{caso}\n"""'
    yield from stream_text(prompt, RESUMEN_SYSTEM_PROMPT)


def build_normas_response(db: Session, caso: str, chunks: list[RetrievedChunk]) -> RespuestaJuridica:
    if not chunks or not has_enough_evidence(chunks):
        return RespuestaJuridica(
            hay_normas_aplicables=False,
            normas_aplicables=[],
            recomendaciones=[
                "No encontré en la Constitución un artículo que aplique claramente a este caso. "
                "Te recomiendo consultar con un abogado o un consultorio jurídico para una "
                "revisión más completa."
            ],
            disclaimer=DISCLAIMER,
        )

    candidates_block = _format_candidates(chunks)
    prompt = (
        f'Caso descrito por la persona:\n"""\n{caso}\n"""\n\n'
        f"CANDIDATOS (únicos artículos que puedes citar):\n{candidates_block}"
    )

    raw = generate_json(prompt, NORMAS_SYSTEM_PROMPT, RespuestaJuridicaLLM)
    llm_response = RespuestaJuridicaLLM.model_validate(json.loads(raw))

    by_key = {(c.kind, c.number): c for c in chunks}
    normas: list[NormaCitada] = []
    for n in llm_response.normas_aplicables:
        chunk = by_key.get((n.tipo, n.numero_articulo))
        if chunk is None:
            # El modelo citó algo que no estaba en los candidatos: se descarta,
            # nunca se muestra al usuario una norma no verificada.
            continue
        normas.append(
            NormaCitada(
                citation=chunk.citation,
                tipo=chunk.kind,
                titulo=chunk.titulo,
                capitulo=chunk.capitulo,
                url=chunk.source_url,
                por_que_aplica=n.por_que_aplica,
                extracto=chunk.text[:600],
            )
        )

    if not normas:
        return RespuestaJuridica(
            hay_normas_aplicables=False,
            normas_aplicables=[],
            recomendaciones=llm_response.recomendaciones
            or [
                "No encontré un artículo de la Constitución que aplique con certeza. "
                "Te recomiendo consultar con un abogado o un consultorio jurídico."
            ],
            disclaimer=DISCLAIMER,
        )

    return RespuestaJuridica(
        hay_normas_aplicables=True,
        normas_aplicables=normas,
        recomendaciones=llm_response.recomendaciones,
        disclaimer=DISCLAIMER,
    )


def retrieve_for_case(db: Session, caso: str) -> list[RetrievedChunk]:
    return retrieve(db, caso)


__all__ = [
    "stream_resumen",
    "build_normas_response",
    "retrieve_for_case",
    "best_similarity",
]
