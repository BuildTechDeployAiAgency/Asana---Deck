"""Data models for Asana tasks and slide content."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AsanaTask:
    """Represents a single Asana task with relevant fields."""

    gid: str
    name: str
    notes: str = ""
    section: str = ""
    assignee: str = ""
    due_on: str | None = None
    tags: list[str] = field(default_factory=list)
    custom_fields: dict[str, str] = field(default_factory=dict)
    completed: bool = False


@dataclass
class SlideContent:
    """AI-structured content for a single slide."""

    title: str
    subtitle: str = ""
    bullets: list[str] = field(default_factory=list)
    executive_summary: str = ""
    slide_type: str = "content"  # title, section, content, timeline
    speaker_notes: str = ""
    section_name: str = ""


@dataclass
class DeckContent:
    """Full deck structure ready for rendering."""

    title: str
    subtitle: str = ""
    date: str = ""
    slides: list[SlideContent] = field(default_factory=list)
