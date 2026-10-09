import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Response
from starlette.requests import Request

from src import telemetry


@pytest.fixture
def main_module(monkeypatch):
    monkeypatch.setattr(telemetry, "setup_telemetry", MagicMock())
    from src import main

    return main


@pytest.mark.parametrize(
    "status_code,expected_level",
    [(200, logging.INFO), (400, logging.WARNING), (500, logging.ERROR)],
)
def test_get_log_level_maps_http_status(main_module, status_code, expected_level):
    assert main_module.get_log_level(status_code) == expected_level


def make_request(method="GET", user_agent="unit-test"):
    return Request({
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/test",
        "raw_path": b"/test",
        "query_string": b"",
        "headers": [(b"user-agent", user_agent.encode())],
        "server": ("test", 80),
        "client": ("127.0.0.1", 1234),
    })


async def return_response(response):
    return response


@pytest.mark.parametrize(
    "status_code,expected_level",
    [(204, logging.INFO), (404, logging.WARNING), (503, logging.ERROR)],
)
def test_response_middleware_logs_request_and_status(monkeypatch, main_module, status_code, expected_level):
    timestamps = iter([10.0, 10.125])
    monkeypatch.setattr(main_module.time, "perf_counter", lambda: next(timestamps))
    logged = {}
    monkeypatch.setattr(
        main_module.logger,
        "log",
        lambda level, msg, extra: logged.update(level=level, msg=msg, extra=extra),
    )
    response = Response(status_code=status_code)

    result = asyncio.run(main_module.log_response_events(make_request("POST"), lambda _: return_response(response)))

    assert result is response
    assert logged["level"] == expected_level
    assert logged["extra"]["httpRequest"] == {
        "latency": "0.125s",
        "protocol": "HTTP/1.1",
        "remoteIP": "127.0.0.1",
        "requestMethod": "POST",
        "requestUrl": "http://test/test",
        "status": status_code,
        "userAgent": "unit-test",
    }


def test_response_middleware_handles_missing_client(monkeypatch, main_module):
    monkeypatch.setattr(main_module.time, "perf_counter", iter([1.0, 1.1]).__next__)
    logged = {}
    monkeypatch.setattr(main_module.logger, "log", lambda level, msg, extra: logged.update(extra=extra))
    request = make_request()
    request.scope["client"] = None

    asyncio.run(main_module.log_response_events(request, lambda _: return_response(Response(status_code=200))))

    assert logged["extra"]["httpRequest"]["remoteIP"] is None


def test_lifespan_initializes_database_and_logs_shutdown(monkeypatch, main_module):
    events = []

    async def initialize_database():
        events.append("database")

    monkeypatch.setattr(main_module, "init_database", initialize_database)
    monkeypatch.setattr(main_module.logger, "info", lambda message: events.append(message))

    async def run_lifespan():
        async with main_module.lifespan(main_module.app):
            assert events == ["Starting the application", "Initializing the database", "database"]

    asyncio.run(run_lifespan())

    assert events[-1] == "Stopping the application"


def test_lifespan_continues_when_database_initialization_fails(monkeypatch, main_module):
    events = []

    async def fail_database():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main_module, "init_database", fail_database)
    monkeypatch.setattr(main_module.logger, "info", lambda message: events.append(message))
    monkeypatch.setattr(main_module.logger, "error", lambda message: events.append(message))

    async def run_lifespan():
        async with main_module.lifespan(main_module.app):
            assert any("database unavailable" in message for message in events)

    asyncio.run(run_lifespan())

    assert events[-1] == "Stopping the application"


def test_index_endpoint_reports_app_status(main_module):
    assert main_module.index() == {"message": "App is running!"}


def test_logger_formats_structured_json():
    from src.logger import formater

    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
    formatted = json.loads(formater.format(record))

    assert formatted["severity"] == "INFO"
    assert formatted["message"] == "hello"
    assert "timestamp" in formatted


def test_database_initialization_creates_client_and_registers_user_model(monkeypatch):
    from src import database

    client = MagicMock()
    database_client = object()
    client.__getitem__.return_value = database_client
    init_beanie = AsyncMock()
    monkeypatch.setattr(database, "AsyncMongoClient", lambda uri: client)
    monkeypatch.setattr(database, "init_beanie", init_beanie)

    asyncio.run(database.init_database())

    client.__getitem__.assert_called_once_with(database.DB_NAME)
    init_beanie.assert_awaited_once_with(database_client, document_models=[database.User])


def test_telemetry_setup_registers_tracing_metrics_and_mongodb_instrumentation(monkeypatch):
    resource = object()
    tracer_provider = MagicMock()
    meter_provider = MagicMock()
    trace_exporter = object()
    metric_exporter = object()
    trace_processor = object()
    metric_reader = object()
    instrumentor = MagicMock()
    trace_setter = MagicMock()
    metric_setter = MagicMock()
    resource_factory = MagicMock(return_value=resource)
    tracer_factory = MagicMock(return_value=tracer_provider)
    meter_factory = MagicMock(return_value=meter_provider)
    trace_exporter_factory = MagicMock(return_value=trace_exporter)
    metric_exporter_factory = MagicMock(return_value=metric_exporter)
    trace_processor_factory = MagicMock(return_value=trace_processor)
    metric_reader_factory = MagicMock(return_value=metric_reader)

    monkeypatch.setattr(telemetry.Resource, "create", resource_factory)
    monkeypatch.setattr(telemetry, "TracerProvider", tracer_factory)
    monkeypatch.setattr(telemetry, "MeterProvider", meter_factory)
    monkeypatch.setattr(telemetry, "OTLPSpanExporter", trace_exporter_factory)
    monkeypatch.setattr(telemetry, "OTLPMetricExporter", metric_exporter_factory)
    monkeypatch.setattr(telemetry, "BatchSpanProcessor", trace_processor_factory)
    monkeypatch.setattr(telemetry, "PeriodicExportingMetricReader", metric_reader_factory)
    monkeypatch.setattr(telemetry.trace, "set_tracer_provider", trace_setter)
    monkeypatch.setattr(telemetry.metrics, "set_meter_provider", metric_setter)
    monkeypatch.setattr(telemetry, "PymongoInstrumentor", lambda: instrumentor)

    telemetry.setup_telemetry()

    resource_factory.assert_called_once_with({"service.name": "mongo-app"})
    trace_exporter_factory.assert_called_once_with(endpoint=telemetry.OTEL_ENDPOINT, insecure=True)
    tracer_provider.add_span_processor.assert_called_once_with(trace_processor)
    trace_setter.assert_called_once_with(tracer_provider)
    metric_exporter_factory.assert_called_once_with(endpoint=telemetry.OTEL_ENDPOINT, insecure=True)
    meter_factory.assert_called_once_with(resource=resource, metric_readers=[metric_reader])
    metric_setter.assert_called_once_with(meter_provider)
    instrumentor.instrument.assert_called_once_with()
