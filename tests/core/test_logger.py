import json
import logging
import sys
from types import ModuleType

from app.core import logger as logger_module
from app.core.logger import (
    CorrelationIDFilter,
    DevFormatter,
    JSONFormatter,
    build_logging_config,
    correlation_id_var,
    setup_logging,
)


def test_correlation_id_filter_sets_default_and_preserves_existing():
    record_without_id = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    correlation_id_var.set("cid-123")
    filter_instance = CorrelationIDFilter()

    assert filter_instance.filter(record_without_id) is True
    assert record_without_id.correlation_id == "cid-123"

    record_with_id = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record_with_id.correlation_id = "existing-cid"

    assert filter_instance.filter(record_with_id) is True
    assert record_with_id.correlation_id == "existing-cid"


def test_dev_formatter_includes_extra_data_block():
    formatter = DevFormatter("%(levelname)s %(name)s [%(correlation_id)s]: %(message)s")

    record = logging.LogRecord(
        name="test.dev",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="dev log",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "cid-dev"
    record.custom_field = "custom"

    rendered = formatter.format(record)

    assert "dev log" in rendered
    assert "--- extra data ---" in rendered
    assert "custom_field" in rendered


def test_json_formatter_includes_standard_and_extra_fields():
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test.json",
        level=logging.WARNING,
        pathname=__file__,
        lineno=25,
        msg="json log",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "cid-json"
    record.custom_key = "custom-value"

    rendered = formatter.format(record)
    payload = json.loads(rendered)

    assert payload["level"] == "WARNING"
    assert payload["logger"] == "test.json"
    assert payload["message"] == "json log"
    assert payload["correlation_id"] == "cid-json"
    assert payload["extra"]["custom_key"] == "custom-value"


def test_build_logging_config_switches_formatter_by_mode():
    text_config = build_logging_config("INFO", use_json=False)
    json_config = build_logging_config("DEBUG", use_json=True)

    text_formatter = text_config["formatters"]["default"]
    json_formatter = json_config["formatters"]["default"]

    assert text_formatter["()"] is DevFormatter
    assert json_formatter["()"] is JSONFormatter
    assert text_config["root"]["level"] == "INFO"
    assert json_config["root"]["level"] == "DEBUG"


def test_setup_logging_development_uses_text_config(monkeypatch):
    captured = {}

    def _fake_dict_config(config):
        captured["config"] = config

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOG_LEVEL", "warning")
    monkeypatch.setattr(logger_module.logging.config, "dictConfig", _fake_dict_config)

    setup_logging()

    formatter = captured["config"]["formatters"]["default"]
    assert formatter["()"] is DevFormatter
    assert captured["config"]["root"]["level"] == "WARNING"


def test_setup_logging_production_without_ddtrace(monkeypatch):
    captured = {}

    def _fake_dict_config(config):
        captured["config"] = config

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setattr(logger_module.logging.config, "dictConfig", _fake_dict_config)
    monkeypatch.delitem(sys.modules, "ddtrace", raising=False)

    setup_logging()

    formatter = captured["config"]["formatters"]["default"]
    assert formatter["()"] is JSONFormatter


def test_setup_logging_production_with_ddtrace_patch(monkeypatch):
    captured = {"patched": False}

    def _fake_dict_config(config):
        captured["config"] = config

    def _fake_patch(*, logging):
        captured["patched"] = logging

    fake_ddtrace = ModuleType("ddtrace")
    fake_ddtrace.patch = _fake_patch

    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    monkeypatch.setattr(logger_module.logging.config, "dictConfig", _fake_dict_config)
    monkeypatch.setitem(sys.modules, "ddtrace", fake_ddtrace)

    setup_logging()

    assert captured["patched"] is True
    assert captured["config"]["root"]["level"] == "ERROR"
