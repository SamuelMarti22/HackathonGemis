"""Un turno de conversación: memoria (Mongo) + RAG (pgvector) + Gemini."""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.memory.cases import DEFAULT_TITLE, CaseRepository
from app.memory.messages import MODEL, USER, MessageRepository
from app.rag import build_normas_response, retrieve_for_case, stream_resumen

HISTORY_MESSAGES = 6  # cuántos mensajes previos se le pasan al modelo
MAX_CHARS = 1500  # recorte por mensaje previo
RETRIEVAL_USER_TURNS = 3  # cuántos mensajes del usuario alimentan la búsqueda de normas


class ChatService:
    def __init__(self, cases: CaseRepository, messages: MessageRepository):
        self._cases = cases
        self._messages = messages

    def stream_turn(self, db: Session, case_id: str, mensaje: str) -> Iterator[tuple[str, dict | str]]:
        """Genera eventos (nombre, datos): resumen*, normas, done.

        Pregunta y respuesta se guardan juntas al final; si algo falla a mitad, el
        historial del caso no queda con un mensaje huérfano.
        """
        history = self._messages.history(case_id)

        chunks = retrieve_for_case(db, self._retrieval_query(history, mensaje))

        resumen_parts: list[str] = []
        for piece in stream_resumen(self._compose_case(history, mensaje)):
            resumen_parts.append(piece)
            yield "resumen", piece

        respuesta = build_normas_response(db, mensaje, chunks).model_dump()
        yield "normas", respuesta

        self._messages.add(case_id, USER, mensaje)
        self._messages.add(case_id, MODEL, "".join(resumen_parts), normas=respuesta)
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
