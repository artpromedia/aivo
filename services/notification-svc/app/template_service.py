"""
Template service for managing and rendering MJML email templates.
"""

import json
import logging
from pathlib import Path
from typing import Any

import aiofiles
from jinja2 import Environment, FileSystemLoader, Template
from mjml import mjml_to_html

from .config import get_settings
from .schemas import TemplateId, TemplateInfo

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing email templates."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.templates_dir = Path(self.settings.templates_path)
        self.templates_path = self.templates_dir  # Backward compatibility
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir))
        )
        self._template_configs: dict[TemplateId, dict[str, Any]] = {}
        self._loaded = False

    async def initialize(self) -> None:
        """Initialize template service and load configurations."""
        if self._loaded:
            return

        await self._load_template_configs()
        self._loaded = True
        logger.info(
            "Template service initialized with %s templates",
            len(self._template_configs)
        )

    async def _load_template_configs(self) -> None:
        """Load template configurations from JSON files."""
        # Load all template configurations
        for template_id in TemplateId:
            config_path = self.templates_dir / f"{template_id.value}.json"
            if config_path.exists():
                async with aiofiles.open(config_path) as f:
                    content = await f.read()
                    self._template_configs[template_id] = json.loads(content)
                    logger.debug(
                        "Loaded config for template: %s", template_id.value
                    )
            else:
                logger.warning(
                    "No config found for template: %s", template_id.value
                )

    async def render_template(
        self, template_id: TemplateId, data: dict[str, Any]
    ) -> dict[str, str]:
        """Render email template with provided data."""
        if not self._loaded:
            await self.initialize()

        # Get template configuration
        config = self._template_configs.get(template_id)
        if not config:
            raise ValueError(
                f"Template configuration not found: {template_id.value}"
            )

        # Validate required data
        required_fields = config.get("required_data", [])
        missing_fields = [
            field for field in required_fields if field not in data
        ]
        if missing_fields:
            raise ValueError(f"Missing required data fields: {missing_fields}")

        # Prepare template data with defaults
        template_data = {
            **config.get("defaults", {}),
            **data,
            "app_name": self.settings.from_name,
            "support_email": self.settings.from_email,
        }

        # Render subject
        subject_template = Template(config.get("subject", "Notification"))
        subject = subject_template.render(**template_data)

        # Load and render MJML template
        mjml_path = self.templates_path / f"{template_id.value}.mjml"
        if not mjml_path.exists():
            raise FileNotFoundError(f"MJML template not found: {mjml_path}")

        async with aiofiles.open(mjml_path) as f:
            mjml_content = await f.read()

        # Render Jinja2 variables in MJML
        mjml_template = Template(mjml_content)
        rendered_mjml = mjml_template.render(**template_data)

        # Convert MJML to HTML
        html_result = mjml_to_html(rendered_mjml)
        if html_result.get("errors"):
            logger.error("MJML compilation errors: %s", html_result['errors'])

        return {"html": html_result.get("html", ""), "subject": subject}

    def get_template_info(
        self, template_id: TemplateId
    ) -> TemplateInfo | None:
        """Get information about a template."""
        config = self._template_configs.get(template_id)
        if not config:
            return None

        return TemplateInfo(
            id=template_id,
            name=config.get("name", template_id.value),
            description=config.get("description", ""),
            required_data=config.get("required_data", []),
            optional_data=config.get("optional_data", []),
        )

    def list_templates(self) -> list[TemplateInfo]:
        """List all available templates."""
        templates = []
        for template_id in TemplateId:
            info = self.get_template_info(template_id)
            if info:
                templates.append(info)
        return templates

    def validate_template_data(
        self, template_id: TemplateId, data: dict[str, Any]
    ) -> bool:
        """Validate that provided data meets template requirements."""
        config = self._template_configs.get(template_id)
        if not config:
            return False

        required_fields = config.get("required_data", [])
        return all(field in data for field in required_fields)


# Global template service instance
template_service = TemplateService()
