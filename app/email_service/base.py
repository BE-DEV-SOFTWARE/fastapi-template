import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict

import brevo_python
from brevo_python.rest import ApiException
from jinja2 import Template

from app.core.config import settings

# Email template directory path
EMAIL_TEMPLATES_DIR = Path(settings.EMAIL_TEMPLATES_DIR)

# Configure Brevo API (only if API key is provided)
api_instance = None
if settings.BREVO_API_KEY:
    configuration = brevo_python.Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY
    api_instance = brevo_python.TransactionalEmailsApi(
        brevo_python.ApiClient(configuration)
    )


class EmailTemplate(str, Enum):
    TEST = "test_email"
    NEW_ACCOUNT = "new_account"
    RESET_PASSWORD = "reset_password"
    VERIFICATION_CODE = "verification_code"

    def filename(self) -> str:
        return f"{self.value}.html"

    def file_path(self) -> Path:
        return Path(EMAIL_TEMPLATES_DIR / self.filename())

    def file(self) -> str:
        with open(self.file_path()) as f:
            return f.read()


def send_email(
    email_to: str,
    subject_template: str = "",
    html_template: str = "",
    environment: Dict[str, Any] = {},
) -> None:
    if not settings.ENABLE_EMAIL_SERVICE:
        logging.info("Email service is disabled. Email not sent.")
        return

    if not settings.EMAILS_ENABLED:
        logging.warning("Email not sent, no provided configuration for email variables")
        return

    project_name = settings.PROJECT_NAME
    # Subject template may already include project name, so use it as is or add prefix
    subject = subject_template if subject_template else project_name
    signature = f"The {project_name} Team"
    environment["signature"] = signature
    environment["project_name"] = project_name
    environment["web_app_url"] = settings.WEB_APP_URL or ""
    # Render the HTML template with Jinja
    template = Template(html_template)
    rendered_html = template.render(**environment)

    # Prepare Brevo email data
    sender = {
        "name": settings.EMAILS_FROM_NAME or project_name,
        "email": settings.EMAILS_FROM_EMAIL,
    }

    to = [
        {
            "email": email_to,
            "name": email_to,
        }
    ]

    reply_to = {
        "name": settings.EMAILS_FROM_NAME or project_name,
        "email": settings.EMAILS_FROM_EMAIL,
    }

    if api_instance is None:
        logging.error(
            "Brevo API instance not initialized. Check BREVO_API_KEY configuration."
        )
        return

    send_smtp_email = brevo_python.SendSmtpEmail(
        to=to,
        reply_to=reply_to,
        html_content=rendered_html,
        sender=sender,
        subject=subject,
    )

    try:
        # Send the transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        logging.info(f"Brevo email sent successfully: {api_response}")
    except ApiException as e:
        logging.error(f"Exception when calling Brevo API: {e}")
