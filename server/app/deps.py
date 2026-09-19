"""Dependencias compartidas de la API: crea una vez los repositorios de Mongo y el servicio de chat."""
from functools import lru_cache

from app.chat_service import ChatService
from app.config import get_settings
from app.memory.cases import CaseRepository
from app.memory.database import get_database
from app.memory.documents import DocumentRepository
from app.memory.messages import MessageRepository


@lru_cache
def get_cases() -> CaseRepository:
    return CaseRepository(get_database(get_settings()))


@lru_cache
def get_messages() -> MessageRepository:
    return MessageRepository(get_database(get_settings()))


@lru_cache
def get_documents() -> DocumentRepository:
    return DocumentRepository(get_database(get_settings()))


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(get_cases(), get_messages(), get_documents())
