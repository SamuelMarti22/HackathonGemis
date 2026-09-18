"""Endpoints de casos y conversación."""
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.chat_service import ChatService
from app.db import SessionLocal
from app.deps import get_cases, get_chat_service, get_messages
from app.memory.cases import CaseRepository
from app.memory.messages import MessageRepository
from app.schemas import ChatRequest
from app.sse import sse

router = APIRouter(prefix="/cases", tags=["cases"])


def _require_case(cases: CaseRepository, case_id: str) -> dict:
    case = cases.get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return case


@router.post("", status_code=201)
def create_case(cases: CaseRepository = Depends(get_cases)) -> dict:
    return cases.create()


@router.get("")
def list_cases(cases: CaseRepository = Depends(get_cases)) -> list[dict]:
    return cases.list_all()


@router.get("/{case_id}")
def get_case(
    case_id: str,
    cases: CaseRepository = Depends(get_cases),
    messages: MessageRepository = Depends(get_messages),
) -> dict:
    case = _require_case(cases, case_id)
    return {**case, "messages": messages.list(case_id)}


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case_id: str,
    cases: CaseRepository = Depends(get_cases),
    messages: MessageRepository = Depends(get_messages),
) -> Response:
    _require_case(cases, case_id)
    messages.delete_by_case(case_id)
    cases.delete(case_id)
    return Response(status_code=204)


@router.post("/{case_id}/chat")
def chat(
    case_id: str,
    req: ChatRequest,
    cases: CaseRepository = Depends(get_cases),
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    _require_case(cases, case_id)

    def event_stream() -> Iterator[str]:
        db = SessionLocal()
        try:
            for event, data in service.stream_turn(db, case_id, req.mensaje):
                yield sse(event, data)
        except Exception as exc:  # noqa: BLE001
            yield sse("error", {"detail": str(exc)})
        finally:
            db.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
