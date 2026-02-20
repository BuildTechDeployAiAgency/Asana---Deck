"""Tests for AI processor (with mocked Claude API)."""

import json
from unittest.mock import MagicMock, patch

from asana_deck.ai_processor import AIProcessor
from asana_deck.models import AsanaTask


def _make_mock_response(data: dict) -> MagicMock:
    """Build a mock Anthropic message response."""
    content_block = MagicMock()
    content_block.text = json.dumps(data)
    msg = MagicMock()
    msg.content = [content_block]
    return msg


@patch("asana_deck.ai_processor.anthropic.Anthropic")
def test_process_task(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        {
            "title": "Launch Widget",
            "subtitle": "Q1 Initiative",
            "bullets": ["Ship by March", "Beta feedback positive", "Docs ready"],
            "executive_summary": "Widget launch is on track.",
            "slide_type": "content",
            "speaker_notes": "Discuss timeline with team.",
        }
    )

    processor = AIProcessor(api_key="sk-test")
    task = AsanaTask(
        gid="1",
        name="Launch Widget",
        section="In Progress",
        notes="We need to ship the widget.",
    )
    slide = processor.process_task(task)

    assert slide.title == "Launch Widget"
    assert len(slide.bullets) == 3
    assert slide.slide_type == "content"
    assert slide.section_name == "In Progress"
    mock_client.messages.create.assert_called_once()


@patch("asana_deck.ai_processor.anthropic.Anthropic")
def test_process_deck_overview(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        {
            "title": "Product Launch Q1",
            "subtitle": "All hands deck",
            "date": "Q1 2026",
        }
    )

    processor = AIProcessor(api_key="sk-test")
    deck = processor.process_deck_overview(
        "Product Launch", ["Planning", "In Progress", "Done"], 15
    )

    assert deck.title == "Product Launch Q1"
    assert deck.date == "Q1 2026"


@patch("asana_deck.ai_processor.anthropic.Anthropic")
def test_build_deck(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    # First call: deck overview. Subsequent calls: per-task slides.
    mock_client.messages.create.side_effect = [
        _make_mock_response(
            {"title": "My Deck", "subtitle": "Sub", "date": "Q1 2026"}
        ),
        _make_mock_response(
            {
                "title": "Task A",
                "subtitle": "",
                "bullets": ["Bullet 1"],
                "executive_summary": "Summary A",
                "slide_type": "content",
                "speaker_notes": "",
            }
        ),
        _make_mock_response(
            {
                "title": "Task B",
                "subtitle": "",
                "bullets": ["Bullet 2"],
                "executive_summary": "Summary B",
                "slide_type": "content",
                "speaker_notes": "",
            }
        ),
    ]

    processor = AIProcessor(api_key="sk-test")
    tasks_by_section = {
        "Backlog": [
            AsanaTask(gid="1", name="Task A"),
            AsanaTask(gid="2", name="Task B"),
        ],
    }
    deck = processor.build_deck("Project X", tasks_by_section)

    assert deck.title == "My Deck"
    # 1 section divider + 2 task slides
    assert len(deck.slides) == 3
    assert deck.slides[0].slide_type == "section"
    assert deck.slides[1].title == "Task A"
    assert deck.slides[2].title == "Task B"
