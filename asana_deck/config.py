"""Configuration management — loads from .env and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""

    asana_access_token: str = ""
    anthropic_api_key: str = ""
    google_credentials_file: str = "credentials.json"
    output_format: str = "pptx"
    output_dir: Path = field(default_factory=lambda: Path("./output"))

    # Slide branding
    brand_color_primary: str = "#1A1A2E"
    brand_color_accent: str = "#E94560"
    brand_color_text: str = "#FFFFFF"
    brand_font_title: str = "Calibri"
    brand_font_body: str = "Calibri"

    @classmethod
    def from_env(cls, env_file: str | None = None) -> Config:
        """Load configuration from environment / .env file."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        return cls(
            asana_access_token=os.getenv("ASANA_ACCESS_TOKEN", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            google_credentials_file=os.getenv(
                "GOOGLE_CREDENTIALS_FILE", "credentials.json"
            ),
            output_format=os.getenv("OUTPUT_FORMAT", "pptx"),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            brand_color_primary=os.getenv("BRAND_COLOR_PRIMARY", "#1A1A2E"),
            brand_color_accent=os.getenv("BRAND_COLOR_ACCENT", "#E94560"),
            brand_color_text=os.getenv("BRAND_COLOR_TEXT", "#FFFFFF"),
            brand_font_title=os.getenv("BRAND_FONT_TITLE", "Calibri"),
            brand_font_body=os.getenv("BRAND_FONT_BODY", "Calibri"),
        )

    def validate(self) -> list[str]:
        """Return a list of missing required config values."""
        errors = []
        if not self.asana_access_token:
            errors.append("ASANA_ACCESS_TOKEN is required")
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")
        if self.output_format == "google_slides" and not Path(
            self.google_credentials_file
        ).exists():
            errors.append(
                f"Google credentials file not found: {self.google_credentials_file}"
            )
        return errors
