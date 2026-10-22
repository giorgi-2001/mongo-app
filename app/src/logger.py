import logging

from pythonjsonlogger.json import JsonFormatter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from .config import OTEL_ENDPOINT


formater = JsonFormatter(
    "{asctime} {levelname} {message}",
    style="{",
    rename_fields={
        "asctime": "timestamp",
        "levelname": "severity",
    },
)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formater)


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)


if OTEL_ENDPOINT:
    provider = LoggerProvider(resource=Resource.create({"service.name": "mongo-app"}))
    provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(OTEL_ENDPOINT))
    )
    otel_handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=provider,
    )
    logger.addHandler(otel_handler)
