"""Asana API client — fetches tasks and sections from a project board."""

from __future__ import annotations

import asana
from asana.rest import ApiException

from asana_deck.models import AsanaTask


class AsanaClient:
    """Thin wrapper around the Asana Python SDK."""

    # Fields we request for each task
    TASK_FIELDS = [
        "gid",
        "name",
        "notes",
        "assignee.name",
        "due_on",
        "tags.name",
        "custom_fields.name",
        "custom_fields.display_value",
        "completed",
        "memberships.section.name",
    ]

    def __init__(self, access_token: str) -> None:
        configuration = asana.Configuration()
        configuration.access_token = access_token
        self._api_client = asana.ApiClient(configuration)
        self._tasks_api = asana.TasksApi(self._api_client)
        self._sections_api = asana.SectionsApi(self._api_client)

    def get_sections(self, project_gid: str) -> list[dict]:
        """Return ordered list of sections (columns) for a project."""
        try:
            resp = self._sections_api.get_sections_for_project(
                project_gid, opt_fields=["gid", "name"]
            )
            return [{"gid": s["gid"], "name": s["name"]} for s in resp]
        except ApiException as exc:
            raise RuntimeError(
                f"Failed to fetch sections for project {project_gid}: {exc}"
            ) from exc

    def get_tasks(
        self,
        project_gid: str,
        *,
        include_completed: bool = False,
    ) -> list[AsanaTask]:
        """Fetch all tasks from an Asana project and return them as models."""
        try:
            raw_tasks = self._tasks_api.get_tasks_for_project(
                project_gid,
                opt_fields=self.TASK_FIELDS,
            )
        except ApiException as exc:
            raise RuntimeError(
                f"Failed to fetch tasks for project {project_gid}: {exc}"
            ) from exc

        tasks: list[AsanaTask] = []
        for raw in raw_tasks:
            if raw.get("completed") and not include_completed:
                continue

            # Extract section name from memberships
            section = ""
            for membership in raw.get("memberships", []):
                sec = membership.get("section")
                if sec:
                    section = sec.get("name", "")
                    break

            # Extract custom fields as name→display_value mapping
            custom_fields: dict[str, str] = {}
            for cf in raw.get("custom_fields", []):
                if cf.get("display_value"):
                    custom_fields[cf["name"]] = cf["display_value"]

            # Extract tags
            tags = [t["name"] for t in raw.get("tags", []) if t.get("name")]

            # Extract assignee
            assignee_data = raw.get("assignee")
            assignee = assignee_data.get("name", "") if assignee_data else ""

            tasks.append(
                AsanaTask(
                    gid=raw["gid"],
                    name=raw.get("name", ""),
                    notes=raw.get("notes", ""),
                    section=section,
                    assignee=assignee,
                    due_on=raw.get("due_on"),
                    tags=tags,
                    custom_fields=custom_fields,
                    completed=raw.get("completed", False),
                )
            )

        return tasks

    def get_tasks_by_section(
        self,
        project_gid: str,
        *,
        include_completed: bool = False,
    ) -> dict[str, list[AsanaTask]]:
        """Fetch tasks grouped by their board section (column)."""
        tasks = self.get_tasks(
            project_gid, include_completed=include_completed
        )
        grouped: dict[str, list[AsanaTask]] = {}
        for task in tasks:
            key = task.section or "Uncategorized"
            grouped.setdefault(key, []).append(task)
        return grouped
