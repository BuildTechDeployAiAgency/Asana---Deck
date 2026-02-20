"""AI processing module — uses Claude to structure Asana tasks into slide content."""

from __future__ import annotations

import json

import anthropic

from asana_deck.models import AsanaTask, DeckContent, SlideContent

SYSTEM_PROMPT = """\
You are a presentation designer AI. You receive raw Asana task data and \
produce clean, structured JSON for generating professional slide decks.

Rules:
- Keep bullet points concise (max 12 words each).
- Use 3-5 bullet points per slide.
- Write executive summaries as a single punchy sentence.
- Choose slide_type from: title, section, content, timeline.
- Use "section" type for section divider slides.
- Use "title" type only for the first slide of the deck.
- Output valid JSON only — no markdown fences, no commentary.
"""

TASK_PROMPT_TEMPLATE = """\
Convert this Asana task into slide content JSON.

Task name: {name}
Section/Column: {section}
Description: {notes}
Assignee: {assignee}
Due date: {due_on}
Tags: {tags}
Custom fields: {custom_fields}

Return JSON with this exact schema:
{{
  "title": "Slide title (short, max 8 words)",
  "subtitle": "Optional subtitle",
  "bullets": ["bullet 1", "bullet 2", "bullet 3"],
  "executive_summary": "One-sentence summary",
  "slide_type": "content",
  "speaker_notes": "Detailed notes for the presenter"
}}
"""

DECK_PROMPT_TEMPLATE = """\
Create a title slide and section overview for a deck about this Asana project.

Project name: {project_name}
Sections: {sections}
Total tasks: {total_tasks}

Return JSON with this exact schema:
{{
  "title": "Deck title",
  "subtitle": "Deck subtitle",
  "date": "Presentation date or quarter",
  "section_summaries": [
    {{
      "section_name": "Section name",
      "summary": "One-sentence section summary",
      "task_count": 5
    }}
  ]
}}
"""


class AIProcessor:
    """Uses Claude to convert raw Asana data into structured slide content."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def _call_claude(self, user_prompt: str) -> dict:
        """Send a prompt to Claude and parse the JSON response."""
        message = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text.strip()

        # Strip markdown fences if the model wraps them anyway
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("\n", 1)[0]

        return json.loads(text)

    def process_task(self, task: AsanaTask) -> SlideContent:
        """Convert a single Asana task into SlideContent."""
        prompt = TASK_PROMPT_TEMPLATE.format(
            name=task.name,
            section=task.section,
            notes=task.notes or "(no description)",
            assignee=task.assignee or "Unassigned",
            due_on=task.due_on or "No due date",
            tags=", ".join(task.tags) if task.tags else "None",
            custom_fields=json.dumps(task.custom_fields) if task.custom_fields else "None",
        )
        data = self._call_claude(prompt)
        return SlideContent(
            title=data.get("title", task.name),
            subtitle=data.get("subtitle", ""),
            bullets=data.get("bullets", []),
            executive_summary=data.get("executive_summary", ""),
            slide_type=data.get("slide_type", "content"),
            speaker_notes=data.get("speaker_notes", ""),
            section_name=task.section,
        )

    def process_deck_overview(
        self,
        project_name: str,
        sections: list[str],
        total_tasks: int,
    ) -> DeckContent:
        """Generate deck-level metadata (title slide, section summaries)."""
        prompt = DECK_PROMPT_TEMPLATE.format(
            project_name=project_name,
            sections=", ".join(sections),
            total_tasks=total_tasks,
        )
        data = self._call_claude(prompt)
        return DeckContent(
            title=data.get("title", project_name),
            subtitle=data.get("subtitle", ""),
            date=data.get("date", ""),
        )

    def build_deck(
        self,
        project_name: str,
        tasks_by_section: dict[str, list[AsanaTask]],
    ) -> DeckContent:
        """Build a complete DeckContent from grouped tasks."""
        sections = list(tasks_by_section.keys())
        total_tasks = sum(len(t) for t in tasks_by_section.values())

        # Generate deck-level overview
        deck = self.process_deck_overview(project_name, sections, total_tasks)

        # Process each section and its tasks
        for section_name, tasks in tasks_by_section.items():
            # Add section divider slide
            deck.slides.append(
                SlideContent(
                    title=section_name,
                    subtitle=f"{len(tasks)} item{'s' if len(tasks) != 1 else ''}",
                    slide_type="section",
                    section_name=section_name,
                )
            )
            # Add a slide for each task
            for task in tasks:
                slide = self.process_task(task)
                deck.slides.append(slide)

        return deck
