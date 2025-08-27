import logging
import requests
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_email_via_postmark(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None, **kwargs) -> bool:
    """
    Отправка email через Postmark API
    
    Args:
        to_email: Email получателя
        subject: Тема письма
        html_body: HTML содержимое
        text_body: Текстовая версия (опционально)
        **kwargs: Дополнительные аргументы (игнорируются) # <- Добавьте это описание
    
    Returns:
        bool: Успешно ли отправлено
    """
    if not settings.POSTMARK_API_TOKEN:
        logger.error("Postmark API token not configured")
        return False
    
    if text_body is None:
        # Создаем текстовую версию из HTML (упрощенная версия)
        text_body = html_body.replace('<br>', '\n').replace('<br/>', '\n')
        text_body = text_body.replace('</p>', '\n\n').replace('</div>', '\n')
        # Удаляем HTML теги
        import re
        text_body = re.sub('<.*?>', '', text_body)
    
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


# Заглушка для тестирования - отправляет в лог вместо реального email
def send_email_via_postmark_stub(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
    """
    Заглушка для тестирования - логирует вместо реальной отправки
    """
    logger.info(f"📧 EMAIL STUB: Would send to {to_email}")
    logger.info(f"📧 Subject: {subject}")
    logger.info(f"📧 Content length: {len(html_body)} chars")
    return True


# Для тестирования используем заглушку вместо реальной отправки
# send_email_via_postmark = send_email_via_postmark_stub