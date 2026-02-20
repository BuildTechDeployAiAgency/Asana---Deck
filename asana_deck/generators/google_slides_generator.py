"""Google Slides generator — creates presentations via the Google Slides API."""

from __future__ import annotations

import uuid
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from asana_deck.config import Config
from asana_deck.models import DeckContent, SlideContent

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
]


def _hex_to_rgb_dict(hex_color: str) -> dict:
    """Convert '#RRGGBB' to Google Slides rgbColor dict (0-1 floats)."""
    h = hex_color.lstrip("#")
    return {
        "red": int(h[0:2], 16) / 255,
        "green": int(h[2:4], 16) / 255,
        "blue": int(h[4:6], 16) / 255,
    }


class GoogleSlidesGenerator:
    """Creates a Google Slides presentation from DeckContent."""

    TOKEN_FILE = "token.json"

    def __init__(self, config: Config) -> None:
        self._config = config
        self._creds = self._authenticate()
        self._service = build("slides", "v1", credentials=self._creds)

    def _authenticate(self) -> Credentials:
        """OAuth2 flow — reuses cached token when available."""
        creds = None
        token_path = Path(self.TOKEN_FILE)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(token_path), SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._config.google_credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json())

        return creds

    @staticmethod
    def _uid() -> str:
        return uuid.uuid4().hex[:12]

    # ── Slide request builders ────────────────────────────────────────

    def _title_slide_requests(
        self, deck: DeckContent
    ) -> list[dict]:
        slide_id = self._uid()
        title_id = self._uid()
        subtitle_id = self._uid()

        requests: list[dict] = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": "0",
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                }
            },
            # Background
            {
                "updatePageProperties": {
                    "objectId": slide_id,
                    "pageProperties": {
                        "pageBackgroundFill": {
                            "solidFill": {
                                "color": {
                                    "rgbColor": _hex_to_rgb_dict(
                                        self._config.brand_color_primary
                                    )
                                }
                            }
                        }
                    },
                    "fields": "pageBackgroundFill",
                }
            },
            # Title textbox
            {
                "createShape": {
                    "objectId": title_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": 600, "unit": "PT"},
                            "height": {"magnitude": 80, "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": 60,
                            "translateY": 160,
                            "unit": "PT",
                        },
                    },
                }
            },
            {
                "insertText": {
                    "objectId": title_id,
                    "text": deck.title,
                    "insertionIndex": 0,
                }
            },
            {
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": {
                        "fontSize": {"magnitude": 36, "unit": "PT"},
                        "bold": True,
                        "fontFamily": self._config.brand_font_title,
                        "foregroundColor": {
                            "opaqueColor": {
                                "rgbColor": _hex_to_rgb_dict(
                                    self._config.brand_color_text
                                )
                            }
                        },
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "fontSize,bold,fontFamily,foregroundColor",
                }
            },
        ]

        if deck.subtitle:
            requests.extend(
                [
                    {
                        "createShape": {
                            "objectId": subtitle_id,
                            "shapeType": "TEXT_BOX",
                            "elementProperties": {
                                "pageObjectId": slide_id,
                                "size": {
                                    "width": {"magnitude": 600, "unit": "PT"},
                                    "height": {"magnitude": 40, "unit": "PT"},
                                },
                                "transform": {
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "translateX": 60,
                                    "translateY": 260,
                                    "unit": "PT",
                                },
                            },
                        }
                    },
                    {
                        "insertText": {
                            "objectId": subtitle_id,
                            "text": deck.subtitle,
                            "insertionIndex": 0,
                        }
                    },
                    {
                        "updateTextStyle": {
                            "objectId": subtitle_id,
                            "style": {
                                "fontSize": {"magnitude": 20, "unit": "PT"},
                                "fontFamily": self._config.brand_font_body,
                                "foregroundColor": {
                                    "opaqueColor": {
                                        "rgbColor": _hex_to_rgb_dict(
                                            self._config.brand_color_accent
                                        )
                                    }
                                },
                            },
                            "textRange": {"type": "ALL"},
                            "fields": "fontSize,fontFamily,foregroundColor",
                        }
                    },
                ]
            )

        return requests

    def _content_slide_requests(
        self, content: SlideContent, index: int
    ) -> list[dict]:
        slide_id = self._uid()
        title_id = self._uid()
        body_id = self._uid()

        is_section = content.slide_type == "section"
        bg_color = (
            self._config.brand_color_accent
            if is_section
            else "#FFFFFF"
        )
        title_color = (
            self._config.brand_color_text
            if is_section
            else self._config.brand_color_primary
        )

        body_text = "\n".join(
            f"\u2022  {b}" for b in content.bullets
        ) if content.bullets else content.executive_summary

        requests: list[dict] = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": str(index),
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                }
            },
            {
                "updatePageProperties": {
                    "objectId": slide_id,
                    "pageProperties": {
                        "pageBackgroundFill": {
                            "solidFill": {
                                "color": {
                                    "rgbColor": _hex_to_rgb_dict(bg_color)
                                }
                            }
                        }
                    },
                    "fields": "pageBackgroundFill",
                }
            },
            {
                "createShape": {
                    "objectId": title_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": 600, "unit": "PT"},
                            "height": {"magnitude": 60, "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": 40,
                            "translateY": 30,
                            "unit": "PT",
                        },
                    },
                }
            },
            {
                "insertText": {
                    "objectId": title_id,
                    "text": content.title,
                    "insertionIndex": 0,
                }
            },
            {
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": {
                        "fontSize": {"magnitude": 28 if is_section else 24, "unit": "PT"},
                        "bold": True,
                        "fontFamily": self._config.brand_font_title,
                        "foregroundColor": {
                            "opaqueColor": {
                                "rgbColor": _hex_to_rgb_dict(title_color)
                            }
                        },
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "fontSize,bold,fontFamily,foregroundColor",
                }
            },
        ]

        if body_text:
            requests.extend(
                [
                    {
                        "createShape": {
                            "objectId": body_id,
                            "shapeType": "TEXT_BOX",
                            "elementProperties": {
                                "pageObjectId": slide_id,
                                "size": {
                                    "width": {"magnitude": 580, "unit": "PT"},
                                    "height": {"magnitude": 280, "unit": "PT"},
                                },
                                "transform": {
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "translateX": 50,
                                    "translateY": 110,
                                    "unit": "PT",
                                },
                            },
                        }
                    },
                    {
                        "insertText": {
                            "objectId": body_id,
                            "text": body_text,
                            "insertionIndex": 0,
                        }
                    },
                    {
                        "updateTextStyle": {
                            "objectId": body_id,
                            "style": {
                                "fontSize": {"magnitude": 16, "unit": "PT"},
                                "fontFamily": self._config.brand_font_body,
                                "foregroundColor": {
                                    "opaqueColor": {
                                        "rgbColor": _hex_to_rgb_dict(
                                            self._config.brand_color_text
                                            if is_section
                                            else "#333333"
                                        )
                                    }
                                },
                            },
                            "textRange": {"type": "ALL"},
                            "fields": "fontSize,fontFamily,foregroundColor",
                        }
                    },
                ]
            )

        return requests

    # ── Public API ────────────────────────────────────────────────────

    def generate(self, deck: DeckContent) -> str:
        """Create a Google Slides presentation. Returns the presentation URL."""
        presentation = (
            self._service.presentations()
            .create(body={"title": deck.title})
            .execute()
        )
        presentation_id = presentation["presentationId"]

        # Build all batch requests
        all_requests: list[dict] = []

        # Delete the default blank slide
        default_slides = presentation.get("slides", [])
        if default_slides:
            all_requests.append(
                {"deleteObject": {"objectId": default_slides[0]["objectId"]}}
            )

        # Title slide
        all_requests.extend(self._title_slide_requests(deck))

        # Content slides
        for i, slide_content in enumerate(deck.slides, start=1):
            all_requests.extend(
                self._content_slide_requests(slide_content, i)
            )

        # Execute batch
        if all_requests:
            self._service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": all_requests},
            ).execute()

        return f"https://docs.google.com/presentation/d/{presentation_id}/edit"
