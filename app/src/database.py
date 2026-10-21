from pymongo import AsyncMongoClient
from beanie import init_beanie
from beanie.exceptions import CollectionWasNotInitialized

from .users.model import User
from .logger import logger

import os
import time


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "test-db")


async def init_database():
    db_initialized = False
    retry_count = 0
    client = AsyncMongoClient(MONGO_URI)
    while not db_initialized:
        try:
            logger.info(f"Initializing the database... Retry count: {retry_count}")
            await init_beanie(client[DB_NAME], document_models=[User])
            db_initialized = True
        except CollectionWasNotInitialized as err:
            time.sleep(5)
            logger.error("Error occured while trying to connect to database", extra={"error": err})
            retry_count += 1
