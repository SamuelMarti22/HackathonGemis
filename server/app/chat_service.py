"""Un turno de conversación: memoria (Mongo) + RAG (pgvector) + Gemini."""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.memory.cases import DEFAULT_TITLE, CaseRepository
from app.memory.documents import DocumentRepository
from app.memory.messages import MODEL, USER, MessageRepository
from app.rag import (
    DocumentGenerationError,
    build_normas_response,
    generate_document,
    retrieve_for_case,
    stream_resumen,
)

HISTORY_MESSAGES = 6  # cuántos mensajes previos se le pasan al modelo
MAX_CHARS = 1500  # recorte por mensaje previo
RETRIEVAL_USER_TURNS = 3  # cuántos mensajes del usuario alimentan la búsqueda de normas


class ChatService:
    def __init__(
        self, cases: CaseRepository, messages: MessageRepository, documents: DocumentRepository
    ):
        self._cases = cases
        self._messages = messages
        self._documents = documents

    def stream_turn(self, db: Session, case_id: str, mensaje: str) -> Iterator[tuple[str, dict | str]]:
        """Genera eventos (nombre, datos): resumen*, normas, documento?, done.

        `documento` solo aparece si hay mecanismo de protección aplicable; si su generación
        falla se emite `error_documento` y el turno sigue con el resumen y las normas.

        Pregunta y respuesta se guardan juntas al final; si algo falla a mitad, el
        historial del caso no queda con un mensaje huérfano.
        """
        history = self._messages.history(case_id)

        chunks = retrieve_for_case(db, self._retrieval_query(history, mensaje))

        caso = self._compose_case(history, mensaje)
        resumen_parts: list[str] = []
        for piece in stream_resumen(caso):
            resumen_parts.append(piece)
            yield "resumen", piece

        respuesta = build_normas_response(db, mensaje, chunks)
        yield "normas", respuesta.model_dump()

        documento_id = None
        try:
            generated = generate_document(db, caso, respuesta)
        except DocumentGenerationError as exc:
            generated = None
            yield "error_documento", {"detail": str(exc)}
        if generated:
            saved = self._documents.create(
                case_id,
                tipo=generated.tipo,
                titulo=generated.titulo,
                cuerpo=generated.cuerpo,
                explicacion_mecanismo=generated.explicacion_mecanismo,
            )
            documento_id = saved["id"]
            yield "documento", {k: v for k, v in saved.items() if k != "cuerpo"}

        self._messages.add(case_id, USER, mensaje)
        self._messages.add(
            case_id, MODEL, "".join(resumen_parts), normas=respuesta.model_dump(), documento_id=documento_id
        )
        if not history:
            self._cases.rename(case_id, mensaje)
        yield "done", {}

    @staticmethod
    def _compose_case(history: list[dict], mensaje: str) -> str:
        if not history:
            return mensaje
        previous = "\n".join(
            f"{'Persona' if m['role'] == USER else 'Tutor'}: {m['content'][:MAX_CHARS]}"
            for m in history[-HISTORY_MESSAGES:]
        )
        return (
            f"Conversación previa:\n{previous}\n\n"
            f"Nuevo mensaje de la persona (respóndelo teniendo en cuenta lo anterior):\n{mensaje}"
        )

    @staticmethod
    def _retrieval_query(history: list[dict], mensaje: str) -> str:
        previous_user = [m["content"] for m in history if m["role"] == USER]
        return "\n".join(previous_user[-(RETRIEVAL_USER_TURNS - 1):] + [mensaje])
