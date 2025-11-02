import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict

import emails
from emails.template import JinjaTemplate

from app.core.config import settings

# Email template directory path
EMAIL_TEMPLATES_DIR = Path(settings.EMAIL_TEMPLATES_DIR)


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
    if not settings.EMAILS_ENABLED:
        logging.warning("Email not sent, no provided configuration for email variables")
        return
    message = emails.Message(
        subject=JinjaTemplate(subject_template),
        html=JinjaTemplate(html_template),
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    if settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logging.info(f"send email result: {response}")
