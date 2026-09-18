"""Conexión a MongoDB: único módulo que crea el cliente de la BD."""
from pymongo import MongoClient
from pymongo.database import Database

from app.config import Settings


def get_database(settings: Settings) -> Database:
    return MongoClient(settings.mongo_uri)[settings.mongo_db]
