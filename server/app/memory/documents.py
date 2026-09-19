"""Repositorio de documentos generados (colección `documents`): tutelas, derechos de petición, etc."""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING
from pymongo.database import Database


def _oid(doc_id: str) -> ObjectId | None:
    try:
        return ObjectId(doc_id)
    except (InvalidId, TypeError):
        return None


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "case_id": doc["case_id"],
        "tipo": doc["tipo"],
        "titulo": doc["titulo"],
        "explicacion_mecanismo": doc.get("explicacion_mecanismo", ""),
        "cuerpo": doc["cuerpo"],
        "aceptado": doc.get("aceptado", False),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


class DocumentRepository:
    def __init__(self, db: Database):
        self._col = db["documents"]
        self._col.create_index([("case_id", 1)])

    def create(
        self, case_id: str, tipo: str, titulo: str, cuerpo: str, explicacion_mecanismo: str = ""
    ) -> dict:
        now = datetime.now(timezone.utc)
        doc = {
            "case_id": case_id,
            "tipo": tipo,
            "titulo": titulo,
            "explicacion_mecanismo": explicacion_mecanismo,
            "cuerpo": cuerpo,
            "aceptado": False,
            "created_at": now,
            "updated_at": now,
        }
        doc["_id"] = self._col.insert_one(doc).inserted_id
        return _serialize(doc)

    def get(self, doc_id: str) -> dict | None:
        oid = _oid(doc_id)
        doc = self._col.find_one({"_id": oid}) if oid else None
        return _serialize(doc) if doc else None

    def list_all(self, case_id: str | None = None) -> list[dict]:
        query = {"case_id": case_id} if case_id else {}
        return [_serialize(d) for d in self._col.find(query).sort("created_at", DESCENDING)]

    def update(self, doc_id: str, fields: dict) -> dict | None:
        """Actualiza solo titulo, cuerpo y aceptado; devuelve el documento o None si no existe."""
        oid = _oid(doc_id)
        allowed = {k: v for k, v in fields.items() if k in {"titulo", "cuerpo", "aceptado"}}
        if not oid:
            return None
        allowed["updated_at"] = datetime.now(timezone.utc)
        self._col.update_one({"_id": oid}, {"$set": allowed})
        return self.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        oid = _oid(doc_id)
        return bool(oid) and self._col.delete_one({"_id": oid}).deleted_count > 0
