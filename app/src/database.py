from pymongo import AsyncMongoClient
from beanie import init_beanie

from .users.model import User

import os


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "test-db")


async def init_database():
    client = AsyncMongoClient(MONGO_URI)
    await init_beanie(client[DB_NAME], document_models=[User])
