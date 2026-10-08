from fastapi import FastAPI, Request, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from contextlib import asynccontextmanager
import time
import logging

from .database import init_database
from .logger import logger
from .telemetry import setup_telemetry
from .users.router import router as users_router
from .auth.router import router as auth_router


API_PREFIX = "/api/v1"


setup_telemetry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the application")
    logger.info("Initializing the database")

    try:
        await init_database()
    except Exception as err:
        logger.error(f"Error initializing the database: {err}")

    yield

    logger.info("Stopping the application")


app = FastAPI(lifespan=lifespan)


FastAPIInstrumentor.instrument_app(app, exclude_spans=["send", "receive"])


def get_log_level(http_status_code):
    if http_status_code >= 500:
        return logging.ERROR
    elif http_status_code < 500 and http_status_code >= 400:
        return logging.WARN
    else:
        return logging.INFO


@app.middleware("http")
async def log_response_events(request: Request, call_next):
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    latency = time.perf_counter() - start_time
    extra = {
        "httpRequest": {
            "latency": f"{latency:.3f}s",
            "protocol": "HTTP/1.1",
            "remoteIP": request.client.host if request.client else None,
            "requestMethod": request.method,
            "requestUrl": str(request.url),
            "status": response.status_code,
            "userAgent": request.headers.get("User-Agent")
        }
    }
    log_level_name = logging.getLevelName(get_log_level(response.status_code))
    message = f"{log_level_name}\t{request.url}"
    logger.log(get_log_level(response.status_code), msg=message, extra=extra)
    return response


app.include_router(users_router, prefix=API_PREFIX)

app.include_router(auth_router, prefix=API_PREFIX)


@app.get("/")
def index():
    return {"message": "App is running!"}
