"""Slide deck generators."""

from asana_deck.generators.pptx_generator import PptxGenerator

__all__ = ["PptxGenerator", "GoogleSlidesGenerator"]


def __getattr__(name: str):
    """Lazy-import GoogleSlidesGenerator to avoid hard dependency on google libs."""
    if name == "GoogleSlidesGenerator":
        from asana_deck.generators.google_slides_generator import (
            GoogleSlidesGenerator,
        )
        return GoogleSlidesGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
