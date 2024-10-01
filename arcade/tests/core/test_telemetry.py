from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from arcade.core.telemetry import OTELHandler, ShutdownError


@pytest.fixture
def app():
    return FastAPI()


@pytest.fixture
def handler_disabled(app):
    return OTELHandler(app, enable=False)


@patch("arcade.core.telemetry.logging")
@patch("arcade.core.telemetry.FastAPIInstrumentor")
@patch("arcade.core.telemetry.OTLPLogExporter")
@patch("arcade.core.telemetry.OTLPMetricExporter")
@patch("arcade.core.telemetry.OTLPSpanExporter")
def test_init_with_enable_true(
    mock_span_exporter,
    mock_metric_exporter,
    mock_log_exporter,
    mock_instrumentor,
    mock_logging,
    app,
):
    # Mock the methods that may cause network calls
    mock_span_exporter.return_value.shutdown = MagicMock()
    mock_metric_exporter.return_value.shutdown = MagicMock()
    mock_log_exporter.return_value.shutdown = MagicMock()

    # Initialize OTELHandler within the scope of the mocks
    handler = OTELHandler(app, enable=True)

    # Verify that the resource is set correctly
    assert handler.resource.attributes["service.name"] == "arcade-actor"
    assert "environment" in handler.resource.attributes

    # Verify that initialization methods are called
    assert handler._tracer_provider is not None
    assert handler._tracer_span_exporter is not None
    assert handler._meter_provider is not None
    assert handler._meter_reader is not None
    assert handler._logger_provider is not None
    assert handler._log_processor is not None

    # Verify that FastAPIInstrumentor is used
    mock_instrumentor.return_value.instrument_app.assert_called_once_with(app)


@patch("arcade.core.telemetry.logging")
@patch("arcade.core.telemetry.FastAPIInstrumentor")
def test_init_with_enable_false(mock_instrumentor, mock_logging, app):
    handler = OTELHandler(app, enable=False)

    # Verify that resources are not initialized
    assert handler._tracer_provider is None
    assert handler._tracer_span_exporter is None
    assert handler._meter_provider is None
    assert handler._meter_reader is None
    assert handler._logger_provider is None
    assert handler._log_processor is None

    # Verify that FastAPIInstrumentor is not called
    mock_instrumentor.return_value.instrument_app.assert_not_called()


def test_init_tracer_export_exception(app):
    # Simulate an exception during exporter initialization

    with pytest.raises(ConnectionError) as exc_info:
        OTELHandler(app, enable=True)

    assert "Could not connect to OpenTelemetry Tracer endpoint" in str(exc_info.value)


@patch("arcade.core.telemetry.OTLPLogExporter")
@patch("arcade.core.telemetry.OTLPMetricExporter")
@patch("arcade.core.telemetry.OTLPSpanExporter")
def test_shutdown(mock_span_exporter, mock_metric_exporter, mock_log_exporter, app):
    # Mock the shutdown methods
    mock_span_exporter.return_value.shutdown = MagicMock()
    mock_metric_exporter.return_value.shutdown = MagicMock()
    mock_log_exporter.return_value.shutdown = MagicMock()

    handler = OTELHandler(app, enable=True)

    # Call shutdown method
    handler.shutdown()

    # Verify that shutdown methods are called
    mock_span_exporter.return_value.shutdown.assert_called_once()
    mock_metric_exporter.return_value.shutdown.assert_called_once()
    mock_log_exporter.return_value.shutdown.assert_called_once()


def test_shutdown_tracer_not_initialized(handler_disabled):
    with pytest.raises(ShutdownError) as exc_info:
        handler_disabled._shutdown_tracer()
    assert "Tracer provider not initialized" in str(exc_info.value)


def test_shutdown_metrics_not_initialized(handler_disabled):
    with pytest.raises(ShutdownError) as exc_info:
        handler_disabled._shutdown_metrics()
    assert "Meter provider not initialized" in str(exc_info.value)


def test_shutdown_logging_not_initialized(handler_disabled):
    with pytest.raises(ShutdownError) as exc_info:
        handler_disabled._shutdown_logging()
    assert "Log provider not initialized" in str(exc_info.value)


@patch("arcade.core.telemetry.get_meter_provider")
@patch("arcade.core.telemetry.OTLPLogExporter")
@patch("arcade.core.telemetry.OTLPMetricExporter")
@patch("arcade.core.telemetry.OTLPSpanExporter")
def test_get_meter(
    mock_span_exporter, mock_metric_exporter, mock_log_exporter, mock_get_meter_provider, app
):
    # Mock the methods that may cause network calls
    mock_span_exporter.return_value.shutdown = MagicMock()
    mock_metric_exporter.return_value.shutdown = MagicMock()
    mock_log_exporter.return_value.shutdown = MagicMock()

    handler = OTELHandler(app, enable=True)

    # Call get_meter method
    handler.get_meter()

    # Verify that get_meter_provider is called
    mock_get_meter_provider.assert_called_once()