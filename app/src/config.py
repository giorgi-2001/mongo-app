import os
import dotenv
from datetime import timedelta

dotenv.load_dotenv()


ACCESS_TOKEN_SECRET_KEY = os.getenv(
    "ACCESS_TOKEN_SECRET_KEY",
    "8f7de60ea91109f3d944cff11ae32a80c0f38d30dd62f8048abf43cf8ab79db4"
)
REFRESH_TOKEN_SECRET_KEY = os.getenv(
    "REFRESH_TOKEN_SECRET_KEY",
    "1b8acc0fcbdf6e36b12cf17f081a1c68a3b1855980a9cdb4de647f36e6fab7e6"
)
MIDLEWARE_SECRET_KEY = os.getenv(
    "MIDLEWARE_SECRET_KEY",
    "c8e54b87c4e7ae13e293ca3cee901c4d50136f038c7749257429260919a90494"
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=10)
REFRESH_TOKEN_EXPIRE = timedelta(days=5)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "test-db")

OTEL_ENDPOINT = os.getenv("OTEL_ENDPOINT")
FRONTEND_HOSTNAME = os.getenv("FRONTEND_HOSTNAME", "http://localhost:80")

# very sensitive secrets
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
