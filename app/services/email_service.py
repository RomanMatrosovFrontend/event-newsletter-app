import os
import logging
import requests
from typing import Optional
from datetime import datetime
from email.message import EmailMessage
from email.policy import SMTP

from app.core.config import settings  # Убедись, что app.core.config импортируется из твоей структуры проекта

logger = logging.getLogger(__name__)

# Путь к папке test_emails
TEST_EMAIL_DIR = './test_emails'
os.makedirs(TEST_EMAIL_DIR, exist_ok=True)

def html_to_text(html_body: str) -> str:
    """Преобразует HTML-письмо в простой текст."""
    text_body = html_body.replace('<br>', '\n').replace('<br/>', '\n')
    text_body = text_body.replace('</p>', '\n\n').replace('</div>', '\n')
    import re
    text_body = re.sub('<.*?>', '', text_body)
    return text_body

def save_email_to_file(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
    """Сохраняет письмо в MIME-формате (используется в тестовом режиме)."""
    msg = EmailMessage()
    msg['From'] = settings.POSTMARK_SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    if text_body is None:
        text_body = html_to_text(html_body)

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype='html')

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{to_email}_{now}.eml"
    with open(os.path.join(TEST_EMAIL_DIR, filename), 'wb') as f:
        f.write(msg.as_bytes(policy=SMTP))

def send_email_via_postmark(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None, **kwargs) -> bool:
    """Отправляет письмо через Postmark или сохраняет в файл (если тестовый режим)."""
    if settings.EMAIL_TEST_MODE:
        save_email_to_file(to_email, subject, html_body, text_body)
        logger.info(f"📧 Email saved to {TEST_EMAIL_DIR} (test mode) for {to_email}")
        return True

    if not settings.POSTMARK_API_TOKEN:
        logger.error("Postmark API token not configured")
        return False

    if text_body is None:
        text_body = html_to_text(html_body)

    payload = {
        "From": settings.POSTMARK_SENDER_EMAIL,
        "To": to_email,
        "Subject": subject,
        "HtmlBody": html_body,
        "TextBody": text_body,
        "MessageStream": "outbound"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": settings.POSTMARK_API_TOKEN
    }

    try:
        response = requests.post(
            "https://api.postmarkapp.com/email",
            json=payload,
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Postmark API error: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return False

def send_email_via_postmark_stub(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
    """Заглушка для тестирования — логирует операцию."""
    logger.info(f"📧 EMAIL STUB: Would send to {to_email}")
    logger.info(f"📧 Subject: {subject}")
    logger.info(f"📧 Content length: {len(html_body)} chars")
    return True

# Для ручного тестирования можно подменить функцию отправки:
# send_email_via_postmark = send_email_via_postmark_stub

