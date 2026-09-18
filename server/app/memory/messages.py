"""Repositorio de mensajes (colección `messages`): preguntas del usuario y respuestas del modelo."""
from datetime import datetime, timezone

from pymongo import ASCENDING
from pymongo.database import Database

USER = "user"
MODEL = "model"  # nombre de rol que usa Gemini


class MessageRepository:
    def __init__(self, db: Database):
        self._col = db["messages"]
        self._col.create_index([("case_id", ASCENDING), ("created_at", ASCENDING)])

    def add(self, case_id: str, role: str, content: str, normas: dict | None = None) -> None:
        doc = {
            "case_id": case_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        }
        if normas is not None:
            doc["normas"] = normas  # respuesta jurídica estructurada (normas, recomendaciones)
        self._col.insert_one(doc)

    def list(self, case_id: str) -> list[dict]:
        """Mensajes completos de un caso, en orden (lo que consume el cliente)."""
        cursor = self._col.find({"case_id": case_id}).sort("created_at", ASCENDING)
        return [
            {
                "role": d["role"],
                "content": d["content"],
                "normas": d.get("normas"),
                "created_at": d["created_at"],
            }
            for d in cursor
        ]

    def history(self, case_id: str) -> list[dict]:
        return [{"role": m["role"], "content": m["content"]} for m in self.list(case_id)]

    def delete_by_case(self, case_id: str) -> None:
        self._col.delete_many({"case_id": case_id})
