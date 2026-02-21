"""Vercel serverless function — generates a .pptx deck from an Asana project."""

from __future__ import annotations

import io
import json
import base64
import tempfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from asana_deck.asana_client import AsanaClient
from asana_deck.ai_processor import AIProcessor
from asana_deck.config import Config
from asana_deck.generators.pptx_generator import PptxGenerator


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length))

            # Required fields
            project_gid = body.get("project_gid")
            asana_token = body.get("asana_token")
            anthropic_key = body.get("anthropic_key")

            if not project_gid or not asana_token or not anthropic_key:
                self._send_error(400, "project_gid, asana_token, and anthropic_key are required")
                return

            # Optional fields
            project_name = body.get("project_name") or f"Asana Project {project_gid}"
            include_completed = body.get("include_completed", False)

            # Build config
            config = Config(
                asana_access_token=asana_token,
                anthropic_api_key=anthropic_key,
                brand_color_primary=body.get("brand_color_primary") or "#1A1A2E",
                brand_color_accent=body.get("brand_color_accent") or "#E94560",
                brand_font_title=body.get("brand_font_title") or "Calibri",
                brand_font_body=body.get("brand_font_body") or "Calibri",
            )

            # 1. Fetch tasks from Asana
            asana_client = AsanaClient(config.asana_access_token)
            tasks_by_section = asana_client.get_tasks_by_section(
                project_gid, include_completed=include_completed
            )

            total_tasks = sum(len(t) for t in tasks_by_section.values())
            if total_tasks == 0:
                self._send_error(404, "No tasks found in this project")
                return

            # 2. Process with AI
            processor = AIProcessor(config.anthropic_api_key)
            deck = processor.build_deck(project_name, tasks_by_section)

            # 3. Generate PowerPoint
            generator = PptxGenerator(config)
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "deck.pptx"
                generator.generate(deck, output_path)

                pptx_bytes = output_path.read_bytes()

            # 4. Return the file
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            self.send_header("Content-Disposition", f'attachment; filename="{project_name}.pptx"')
            self.send_header("Content-Length", str(len(pptx_bytes)))
            self.end_headers()
            self.wfile.write(pptx_bytes)

        except Exception as exc:
            self._send_error(500, str(exc))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_error(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())
