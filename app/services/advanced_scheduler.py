import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import newsletter_service
from app.models import NewsletterSchedule

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)

def init_scheduler():
    """Инициализация планировщика при запуске приложения"""
    if not scheduler.running:
        scheduler.start()
        load_all_schedules()
        logger.info("Advanced scheduler initialized")

def load_all_schedules():
    """Загрузка всех активных расписаний из БД"""
    try:
        db_generator = get_db()
        db = next(db_generator)
        
        active_schedules = db.query(NewsletterSchedule).filter(
            NewsletterSchedule.is_active == True
        ).all()
        
        for schedule in active_schedules:
            schedule_job(schedule, db)
            
        logger.info(f"Loaded {len(active_schedules)} active schedules")
        
    except Exception as e:
        logger.error(f"Error loading schedules: {str(e)}")
    finally:
        if db:
            db.close()

def schedule_job(schedule: NewsletterSchedule, db: Session):
    """Создание задачи для конкретного расписания"""
    job_id = f"schedule_{schedule.id}"
    
    try:
        if schedule.schedule_type == 'cron' and schedule.cron_expression:
            # Для cron-расписаний
            trigger = CronTrigger.from_crontab(schedule.cron_expression)
            scheduler.add_job(
                run_scheduled_newsletter,
                trigger=trigger,
                args=[schedule.id],
                id=job_id,
                replace_existing=True,
                name=schedule.name
            )
            logger.info(f"Scheduled cron job '{schedule.name}': {schedule.cron_expression}")
            
        elif schedule.schedule_type == 'date' and schedule.specific_date:
            # Для одноразовых расписаний
            scheduler.add_job(
                run_scheduled_newsletter,
                trigger=DateTrigger(schedule.specific_date),
                args=[schedule.id],
                id=job_id,
                replace_existing=True,
                name=schedule.name
            )
            logger.info(f"Scheduled one-time job '{schedule.name}': {schedule.specific_date}")
            
    except Exception as e:
        logger.error(f"Error scheduling job {job_id}: {str(e)}")

def run_scheduled_newsletter(schedule_id: int):
    """Запуск рассылки по расписанию"""
    db = None
    try:
        db_generator = get_db()
        db = next(db_generator)
        
        # Получаем расписание
        schedule = db.query(NewsletterSchedule).filter(
            NewsletterSchedule.id == schedule_id
        ).first()
        
        if not schedule or not schedule.is_active:
            logger.warning(f"Schedule {schedule_id} not found or inactive")
            return
        
        logger.info(f"Running scheduled newsletter: {schedule.name}")
        
        # Обновляем время последнего запуска
        schedule.last_run = datetime.utcnow()
        db.commit()
        
        # Запускаем рассылку для конкретных пользователей или всех
        if schedule.user_ids:
            # Рассылка только выбранным пользователям
            newsletter_service.send_newsletter_to_users(db, schedule.user_ids)
        else:
            # Рассылка всем подписанным пользователям
            newsletter_service.send_newsletter_to_all_users(db)
            
    except Exception as e:
        logger.error(f"Error in scheduled newsletter {schedule_id}: {str(e)}")
    finally:
        if db:
            db.close()
