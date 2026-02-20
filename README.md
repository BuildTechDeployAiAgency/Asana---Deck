# Asana Deck

Generate polished slide decks from Asana project boards using AI.

**Pipeline:** Asana Board → Claude AI → PowerPoint / Google Slides

## How It Works

1. **Reads** all tasks from an Asana project, grouped by board section (column)
2. **Sends** each task to Claude, which returns structured JSON (title, bullets, summary, speaker notes)
3. **Renders** a branded slide deck — one section divider per column, one content slide per task

## Quick Start

```bash
# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your Asana PAT and Anthropic API key

# Generate a deck
asana-deck <PROJECT_GID>
```

Find your project GID in the Asana URL: `https://app.asana.com/0/<PROJECT_GID>/...`

## CLI Options

```
Usage: asana-deck [OPTIONS] PROJECT_GID

Options:
  --format [pptx|google_slides]  Output format (default: from .env or pptx)
  -o, --output PATH              Output file path for pptx
  --project-name TEXT             Human-readable name for the deck title
  --include-completed             Include completed tasks
  --env-file PATH                 Path to .env file
  --model TEXT                    Claude model to use (default: claude-sonnet-4-20250514)
  --help                          Show this message and exit
```

## Examples

```bash
# Basic — generates output/deck_<timestamp>.pptx
asana-deck 1234567890

# Custom output path and project name
asana-deck 1234567890 -o launch_deck.pptx --project-name "Q1 Product Launch"

# Google Slides output (requires OAuth setup)
asana-deck 1234567890 --format google_slides

# Include completed tasks
asana-deck 1234567890 --include-completed
```

## Configuration

All config lives in `.env` (see `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `ASANA_ACCESS_TOKEN` | Yes | Asana Personal Access Token |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `OUTPUT_FORMAT` | No | `pptx` (default) or `google_slides` |
| `OUTPUT_DIR` | No | Output directory (default: `./output`) |
| `GOOGLE_CREDENTIALS_FILE` | For Google Slides | Path to OAuth credentials JSON |
| `BRAND_COLOR_PRIMARY` | No | Hex color for slide backgrounds (default: `#1A1A2E`) |
| `BRAND_COLOR_ACCENT` | No | Hex color for accents (default: `#E94560`) |
| `BRAND_COLOR_TEXT` | No | Hex color for text (default: `#FFFFFF`) |
| `BRAND_FONT_TITLE` | No | Title font family (default: `Calibri`) |
| `BRAND_FONT_BODY` | No | Body font family (default: `Calibri`) |

## Architecture

```
asana_deck/
├── __init__.py
├── cli.py                 # Click CLI entry point
├── config.py              # .env / environment config
├── models.py              # AsanaTask, SlideContent, DeckContent dataclasses
├── asana_client.py        # Asana SDK wrapper
├── ai_processor.py        # Claude API integration
├── generators/
│   ├── __init__.py
│   ├── pptx_generator.py          # python-pptx output
│   └── google_slides_generator.py # Google Slides API output
└── templates/
    └── __init__.py
```

## Slide Types

The AI assigns each slide one of these types:

- **title** — Opening slide with deck title, subtitle, date
- **section** — Divider slide for each Asana board column
- **content** — Task slide with title, bullets, executive summary, speaker notes
- **timeline** — (Future) Timeline/Gantt-style layout

## Google Slides Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Google Slides API and Google Drive API
3. Create OAuth 2.0 credentials (Desktop app) and download as `credentials.json`
4. Set `GOOGLE_CREDENTIALS_FILE=credentials.json` in `.env`
5. On first run, a browser window opens for OAuth consent; token is cached in `token.json`

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

## Tech Stack

| Layer | Tool |
|---|---|
| Asana data | `asana` Python SDK |
| AI structuring | Claude API (`anthropic`) |
| PowerPoint | `python-pptx` |
| Google Slides | `google-api-python-client` |
| CLI | `click` + `rich` |
| Config | `python-dotenv` |
