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
import re
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.gemini_client import generate_json, stream_text
from app.retrieval import RetrievedChunk, best_similarity, get_article, has_enough_evidence, retrieve
from app.schemas import (
    DISCLAIMER,
    MECANISMOS,
    DocumentoGenerado,
    DocumentoGeneradoLLM,
    MecanismoRecomendado,
    NormaCitada,
    RespuestaJuridica,
    RespuestaJuridicaLLM,
)


class DocumentGenerationError(Exception):
    """Se intentó generar un documento pero falló (error de la API de Gemini,
    o el borrador citaba un artículo no verificado). El resumen y las normas
    ya generados siguen siendo válidos: quien llame no debe descartarlos."""

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
caso descrito. No des consejos genéricos que no se apoyen en el contexto.
5. Si hay_normas_aplicables es true, SIEMPRE debes completar "mecanismo_recomendado" con el \
mecanismo de protección ciudadana (tutela, derecho de petición, acción de cumplimiento, acción \
popular, habeas corpus o habeas data) más adecuado para que la persona haga valer su derecho — \
elige uno solo, el más pertinente, no una lista. Si hay_normas_aplicables es false, déjalo en null."""

DOCUMENTO_SYSTEM_PROMPT = """Eres un tutor jurídico que redacta, en español formal pero \
comprensible, un borrador completo y listo para editar del mecanismo de protección ciudadana \
indicado, basado en el caso descrito por la persona.

Reglas estrictas (no negociables):
1. SOLO puedes citar, dentro del cuerpo del documento, los artículos que aparecen en la lista \
"Artículos verificados". Nunca cites de memoria un artículo que no esté ahí.
2. Usa placeholders entre corchetes para cualquier dato personal que no conozcas: \
[Nombre completo], [Número de cédula], [Dirección], [Ciudad], [Fecha], [Entidad accionada], etc.
3. Estructura el documento como corresponde al mecanismo (destinatario, hechos basados \
únicamente en lo que la persona contó, fundamentos de derecho citando los artículos \
verificados, petición concreta, firma).
4. No inventes hechos que la persona no haya mencionado."""


ARTICULO_MENTION_RE = re.compile(r"[Aa]rt[íi]culo\s+(?:transitorio\s+)?(\d+[A-Za-z]?)")


def _citation_number(citation: str) -> str | None:
    match = re.search(r"(\d+[A-Za-z]?)$", citation)
    return match.group(1) if match else None


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

    mecanismo = _resolve_mecanismo(db, llm_response)

    return RespuestaJuridica(
        hay_normas_aplicables=True,
        normas_aplicables=normas,
        recomendaciones=llm_response.recomendaciones,
        mecanismo_recomendado=mecanismo,
        disclaimer=DISCLAIMER,
    )


def _resolve_mecanismo(db: Session, llm_response: RespuestaJuridicaLLM) -> MecanismoRecomendado | None:
    rec = llm_response.mecanismo_recomendado
    if rec is None:
        return None
    info = MECANISMOS.get(rec.tipo)
    if info is None:
        # Tipo fuera del enum validado por pydantic no debería pasar, pero
        # por defensa en profundidad no se muestra nada no reconocido.
        return None

    base_article = get_article(db, "articulo", info["articulo_base"])
    return MecanismoRecomendado(
        tipo=rec.tipo,
        nombre=info["nombre"],
        justificacion=rec.justificacion,
        articulo_base=base_article.citation if base_article else f"Artículo {info['articulo_base']}",
        articulo_base_url=base_article.source_url if base_article else None,
    )


def generate_document(db: Session, caso: str, respuesta: RespuestaJuridica) -> DocumentoGenerado | None:
    """Redacta el borrador del mecanismo recomendado en `respuesta`. Devuelve
    None cuando no hay caso/mecanismo real (no es un error). Lanza
    DocumentGenerationError si se intentó generar pero falló — el llamador
    puede capturarlo sin perder el resumen ni las normas ya obtenidos."""
    if not respuesta.hay_normas_aplicables or respuesta.mecanismo_recomendado is None:
        return None

    mecanismo = respuesta.mecanismo_recomendado

    citation_numbers = {n.citation: _citation_number(n.citation) for n in respuesta.normas_aplicables}
    allowed_numbers = {v for v in citation_numbers.values() if v}
    base_number = _citation_number(mecanismo.articulo_base)
    if base_number:
        allowed_numbers.add(base_number)

    normas_lines = [f"- {n.citation}: {n.extracto[:500]}" for n in respuesta.normas_aplicables]
    if mecanismo.articulo_base not in citation_numbers:
        normas_lines.insert(0, f"- {mecanismo.articulo_base} (consagra el mecanismo {mecanismo.nombre})")

    prompt = (
        f'Caso descrito por la persona:\n"""\n{caso}\n"""\n\n'
        f"Mecanismo a redactar: {mecanismo.nombre} ({mecanismo.tipo})\n"
        f"Por qué aplica: {mecanismo.justificacion}\n\n"
        f"Artículos verificados que puedes citar (ningún otro):\n" + "\n".join(normas_lines)
    )

    try:
        raw = generate_json(prompt, DOCUMENTO_SYSTEM_PROMPT, DocumentoGeneradoLLM)
        llm_doc = DocumentoGeneradoLLM.model_validate(json.loads(raw))
    except Exception as exc:  # noqa: BLE001
        raise DocumentGenerationError(f"No se pudo generar el documento: {exc}") from exc

    mentioned = {m.group(1) for m in ARTICULO_MENTION_RE.finditer(llm_doc.cuerpo)}
    if not mentioned <= allowed_numbers:
        # El borrador citó un artículo no verificado: no se muestra un
        # documento legal potencialmente alucinado, se falla explícitamente.
        raise DocumentGenerationError(
            "El borrador generado citaba artículos no verificados; se descartó por seguridad."
        )

    normas_citadas = list(citation_numbers.keys())
    if mecanismo.articulo_base not in citation_numbers:
        normas_citadas.insert(0, mecanismo.articulo_base)

    return DocumentoGenerado(
        tipo=mecanismo.tipo,
        titulo=llm_doc.titulo,
        explicacion_mecanismo=llm_doc.explicacion_mecanismo,
        cuerpo=llm_doc.cuerpo,
        normas_citadas=normas_citadas,
    )


def retrieve_for_case(db: Session, caso: str) -> list[RetrievedChunk]:
    return retrieve(db, caso)


__all__ = [
    "stream_resumen",
    "build_normas_response",
    "retrieve_for_case",
    "best_similarity",
    "generate_document",
    "DocumentGenerationError",
]
