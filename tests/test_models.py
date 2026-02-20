"""Tests for data models."""

from asana_deck.models import AsanaTask, DeckContent, SlideContent


def test_asana_task_defaults():
    task = AsanaTask(gid="123", name="Test Task")
    assert task.gid == "123"
    assert task.name == "Test Task"
    assert task.notes == ""
    assert task.section == ""
    assert task.assignee == ""
    assert task.due_on is None
    assert task.tags == []
    assert task.custom_fields == {}
    assert task.completed is False


def test_asana_task_full():
    task = AsanaTask(
        gid="456",
        name="Launch Feature X",
        notes="Full description",
        section="In Progress",
        assignee="Alice",
        due_on="2026-03-01",
        tags=["urgent", "launch"],
        custom_fields={"Priority": "High"},
        completed=False,
    )
    assert task.section == "In Progress"
    assert task.tags == ["urgent", "launch"]
    assert task.custom_fields["Priority"] == "High"


def test_slide_content_defaults():
    slide = SlideContent(title="Slide 1")
    assert slide.title == "Slide 1"
    assert slide.slide_type == "content"
    assert slide.bullets == []


def test_deck_content():
    deck = DeckContent(
        title="Q1 Product Launch",
        subtitle="Overview deck",
        date="Q1 2026",
        slides=[
            SlideContent(title="Section A", slide_type="section"),
            SlideContent(
                title="Feature X",
                bullets=["Point 1", "Point 2"],
                executive_summary="Feature X is great.",
            ),
        ],
    )
    assert len(deck.slides) == 2
    assert deck.slides[0].slide_type == "section"
    assert deck.slides[1].bullets == ["Point 1", "Point 2"]
