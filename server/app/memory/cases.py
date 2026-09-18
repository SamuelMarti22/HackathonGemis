"""Repositorio de casos (colección `cases`)."""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database

DEFAULT_TITLE = "Nuevo caso"


def _oid(case_id: str) -> ObjectId | None:
    try:
        return ObjectId(case_id)
    except (InvalidId, TypeError):
        return None


def _serialize(doc: dict) -> dict:
    return {"id": str(doc["_id"]), "title": doc["title"], "created_at": doc["created_at"]}


class CaseRepository:
    def __init__(self, db: Database):
        self._col = db["cases"]

    def create(self, title: str = DEFAULT_TITLE) -> dict:
        doc = {"title": title[:80], "created_at": datetime.now(timezone.utc)}
        doc["_id"] = self._col.insert_one(doc).inserted_id
        return _serialize(doc)

    def get(self, case_id: str) -> dict | None:
        oid = _oid(case_id)
        doc = self._col.find_one({"_id": oid}) if oid else None
        return _serialize(doc) if doc else None

    def list_all(self) -> list[dict]:
        return [_serialize(d) for d in self._col.find().sort("created_at", -1)]

    def rename(self, case_id: str, title: str) -> None:
        oid = _oid(case_id)
        if oid:
            self._col.update_one({"_id": oid}, {"$set": {"title": title[:80]}})

    def delete(self, case_id: str) -> bool:
        oid = _oid(case_id)
        return bool(oid) and self._col.delete_one({"_id": oid}).deleted_count > 0
