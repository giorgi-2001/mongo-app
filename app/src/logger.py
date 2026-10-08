import logging

from pythonjsonlogger.json import JsonFormatter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource


OTEL_ENDPOINT = "http://otel-collector:4317"


formater = JsonFormatter(
    "{asctime} {levelname} {message}",
    style="{",
    rename_fields={
        "asctime": "timestamp",
        "levelname": "severity",
    },
)


provider = LoggerProvider(resource=Resource.create({"service.name": "task-api"}))
provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter(OTEL_ENDPOINT))
)

otel_handler = LoggingHandler(
    level=logging.INFO,
    logger_provider=provider,
)

stream_handler = logging.StreamHandler()

logger = logging.getLogger()

stream_handler.setFormatter(formater)

logger.setLevel(logging.INFO)

logger.addHandler(stream_handler)
logger.addHandler(otel_handler)
