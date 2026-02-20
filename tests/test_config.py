"""Tests for configuration loading."""

import os
from pathlib import Path

from asana_deck.config import Config


def test_config_defaults():
    config = Config()
    assert config.asana_access_token == ""
    assert config.output_format == "pptx"
    assert config.output_dir == Path("./output")
    assert config.brand_color_primary == "#1A1A2E"


def test_config_validate_missing_tokens():
    config = Config()
    errors = config.validate()
    assert "ASANA_ACCESS_TOKEN is required" in errors
    assert "ANTHROPIC_API_KEY is required" in errors


def test_config_validate_ok():
    config = Config(
        asana_access_token="xoxp-test",
        anthropic_api_key="sk-test",
    )
    errors = config.validate()
    assert errors == []


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("ASANA_ACCESS_TOKEN", "tok-abc")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-xyz")
    monkeypatch.setenv("OUTPUT_FORMAT", "google_slides")
    monkeypatch.setenv("BRAND_COLOR_ACCENT", "#FF0000")

    config = Config.from_env()
    assert config.asana_access_token == "tok-abc"
    assert config.anthropic_api_key == "sk-xyz"
    assert config.output_format == "google_slides"
    assert config.brand_color_accent == "#FF0000"
