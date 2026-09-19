"""Endpoints de documentos generados (Mis documentos)."""
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.deps import get_documents
from app.memory.documents import DocumentRepository

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    cuerpo: str | None = Field(default=None, min_length=1)
    aceptado: bool | None = None


def _require(documents: DocumentRepository, doc_id: str) -> dict:
    doc = documents.get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.get("")
def list_documents(
    case_id: str | None = None, documents: DocumentRepository = Depends(get_documents)
) -> list[dict]:
    return documents.list_all(case_id)


@router.get("/{doc_id}")
def get_document(doc_id: str, documents: DocumentRepository = Depends(get_documents)) -> dict:
    return _require(documents, doc_id)


@router.put("/{doc_id}")
def update_document(
    doc_id: str, body: DocumentUpdate, documents: DocumentRepository = Depends(get_documents)
) -> dict:
    _require(documents, doc_id)
    return documents.update(doc_id, body.model_dump(exclude_none=True))


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str, documents: DocumentRepository = Depends(get_documents)) -> Response:
    _require(documents, doc_id)
    documents.delete(doc_id)
    return Response(status_code=204)
