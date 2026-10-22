from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from .config import OTEL_ENDPOINT


def setup_telemetry():
    if not OTEL_ENDPOINT:
        return

    resource = Resource.create({
        "service.name": "mongo-app",
    })

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=OTEL_ENDPOINT,
        insecure=True,
    )

    provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    metric_exporter = OTLPMetricExporter(
        endpoint=OTEL_ENDPOINT,
        insecure=True,
    )

    metric_reader = PeriodicExportingMetricReader(
        metric_exporter
    )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    trace.set_tracer_provider(provider)
    metrics.set_meter_provider(meter_provider)

    PymongoInstrumentor().instrument()
