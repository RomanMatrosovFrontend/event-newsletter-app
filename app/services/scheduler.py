import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.database import get_db
from app.services import newsletter_service

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)

def schedule_newsletters():
    """Запланировать все регулярные рассылки"""
    # Пример: ежедневно в 10:00 по Москве
    scheduler.add_job(
        func=run_scheduled_newsletter,
        trigger=CronTrigger(hour=10, minute=0, timezone="Europe/Moscow"),
        id="daily_newsletter",
        replace_existing=True,
    )
    logger.info("Scheduled newsletters initialized")

def run_scheduled_newsletter():
    """Запуск рассылки по расписанию"""
    try:
        logger.info("Starting scheduled newsletter run...")
        # Используем отдельную сессию для фоновой задачи
        db_generator = get_db()
        db = next(db_generator)
        newsletter_service.send_newsletter_to_all_users(db)
        logger.info("Scheduled newsletter completed successfully")
    except Exception as e:
        logger.error(f"Error in scheduled newsletter: {str(e)}")
    finally:
        if db:
            db.close()

def start_scheduler():
    """Запустить планировщик (вызывается в main.py)"""
    if not scheduler.running:
        scheduler.start()
        schedule_newsletters()