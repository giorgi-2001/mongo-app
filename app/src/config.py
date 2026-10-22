import os
import dotenv

dotenv.load_dotenv()


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "test-db")

OTEL_ENDPOINT = os.getenv("OTEL_ENDPOINT")
FRONTEND_HOSTNAME = os.getenv("FRONTEND_HOSTNAME", "http://localhost:80")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
