"""Template engine for localized notifications."""

import logging
import re
from typing import Any

import jinja2
from jinja2 import Template

from .models import NotificationTemplate

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Manages notification templates with localization."""

    def __init__(self) -> None:
        self.templates: dict[str, dict] = {}
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("templates"),
            autoescape=True,
        )
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates from JSON files."""
        # IEP Reminder Template
        self.templates["iep_reminder"] = {
            "id": "iep_reminder",
            "locales": {
                "en": {
                    "title": "IEP Meeting Reminder",
                    "body": (
                        "Reminder: IEP meeting for {{student_name}} "
                        "is scheduled for {{meeting_date}} at "
                        "{{meeting_time}}."
                    ),
                    "sms": (
                        "IEP Reminder: Meeting for {{student_name}} on "
                        "{{meeting_date}} at {{meeting_time}}"
                    ),
                },
                "es": {
                    "title": "Recordatorio de Reunión IEP",
                    "body": (
                        "Recordatorio: La reunión IEP para {{student_name}} "
                        "está programada para {{meeting_date}} a las "
                        "{{meeting_time}}."
                    ),
                    "sms": (
                        "Recordatorio IEP: Reunión para {{student_name}} el "
                        "{{meeting_date}} a las {{meeting_time}}"
                    ),
                },
            },
        }

        # Document Update Template
        self.templates["document_update"] = {
            "id": "document_update",
            "locales": {
                "en": {
                    "title": "Document Updated",
                    "body": (
                        "{{document_name}} has been updated by "
                        "{{updated_by}}. {{update_summary}}"
                    ),
                    "sms": ("Doc Update: {{document_name}} updated. Check portal."),
                },
                "es": {
                    "title": "Documento Actualizado",
                    "body": (
                        "{{document_name}} ha sido actualizado por "
                        "{{updated_by}}. {{update_summary}}"
                    ),
                    "sms": ("Actualización: {{document_name}} actualizado. " "Revise el portal."),
                },
            },
        }

    async def render(
        self,
        template_id: str,
        data: dict[str, Any],
        locale: str = "en",
    ) -> dict[str, str]:
        """Render template with data."""
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")

        template = self.templates[template_id]

        # Fallback to English if locale not found
        if locale not in template["locales"]:
            logger.warning("Locale %s not found for %s, using en", locale, template_id)
            locale = "en"

        locale_templates = template["locales"][locale]

        result = {}
        for key, template_str in locale_templates.items():
            try:
                jinja_template = Template(template_str)
                result[key] = jinja_template.render(**data)
            except (jinja2.TemplateError, ValueError) as e:
                logger.error("Template render error: %s", e)
                result[key] = template_str

        # Add metadata
        result["template_id"] = template_id
        result["locale"] = locale

        # For SMS, use sms key or fallback to body
        if "sms" not in result and "body" in result:
            result["sms_text"] = result["body"][:160]
        else:
            result["sms_text"] = result.get("sms", "")

        return result

    def get_template(
        self,
        template_id: str,
    ) -> NotificationTemplate | None:
        """Get template by ID."""
        return self.templates.get(template_id)

    def list_templates(self) -> list[str]:
        """List available template IDs."""
        return list(self.templates.keys())

    def validate_data(
        self,
        template_id: str,
        data: dict[str, Any],
    ) -> bool:
        """Validate that required variables are present."""
        if template_id not in self.templates:
            return False

        # Extract variables from template
        template = self.templates[template_id]
        required_vars = set()

        for locale_data in template["locales"].values():
            for template_str in locale_data.values():
                # Simple variable extraction
                vars_found = re.findall(r"\{\{(\w+)\}\}", template_str)
                required_vars.update(vars_found)

        # Check if all required variables are in data
        missing = required_vars - set(data.keys())
        if missing:
            logger.warning("Missing template variables: %s", missing)
            return False

        return True
