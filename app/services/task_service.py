import logging
import time
from functools import wraps
from app.core.config import settings

logger = logging.getLogger(__name__)

def background_task_with_retry(max_retries=3, delay=60):
    """Декоратор для повтора фоновых задач при ошибках"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt} failed for {func.__name__}: {str(e)}")
                    if attempt < max_retries:
                        time.sleep(delay * attempt)
            logger.error(f"Task {func.__name__} failed after {max_retries} attempts: {str(last_error)}")
            raise last_error
        return wrapper
    return decorator

# Пример использования в email_service.py
@background_task_with_retry(max_retries=3, delay=30)
def send_email_via_postmark(to_email: str, subject: str, html_body: str):
    # существующая логика
    pass