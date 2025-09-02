import logging
import pytz
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
        
        print(f"Found {len(active_schedules)} active schedules in database")
        
        for schedule in active_schedules:
            print(f"Loading schedule: {schedule.name} (ID: {schedule.id})")
            schedule_job(schedule, db)
            
        logger.info(f"Loaded {len(active_schedules)} active schedules")
        
    except Exception as e:
        print(f"Error loading schedules: {str(e)}")
        logger.error(f"Error loading schedules: {str(e)}")
    finally:
        if db:
            db.close()

def convert_admin_time_to_utc(admin_datetime, admin_timezone):
    """Конвертация времени из часового пояса админа в UTC"""
    try:
        if admin_timezone == "UTC":
            return admin_datetime.replace(tzinfo=pytz.UTC)
            
        admin_tz = pytz.timezone(admin_timezone)
        utc_tz = pytz.UTC
        
        # Если время naive, делаем aware в часовом поясе админа
        if admin_datetime.tzinfo is None:
            admin_aware = admin_tz.localize(admin_datetime)
        else:
            admin_aware = admin_datetime.astimezone(admin_tz)
            
        # Конвертируем в UTC и ОСТАВЛЯЕМ tzinfo
        utc_time = admin_aware.astimezone(utc_tz)
        return utc_time
        
    except Exception as e:
        logger.error(f"Error converting time to UTC: {str(e)}")
        return admin_datetime.replace(tzinfo=pytz.UTC)

def schedule_job(schedule: NewsletterSchedule, db: Session):
    """Создание задачи для конкретного расписания"""
    job_id = f"schedule_{schedule.id}"
    admin_tz = schedule.admin_timezone or "UTC"
    
    print(f"Creating job {job_id} for schedule: {schedule.name}")
    print(f"Schedule type: {schedule.schedule_type}")
    print(f"Admin timezone: {admin_tz}")
    
    try:
        if schedule.schedule_type == 'cron' and schedule.cron_expression:
            # Для cron-расписаний
            timezone = pytz.timezone(admin_tz)
            trigger = CronTrigger.from_crontab(schedule.cron_expression, timezone=timezone)
            
            scheduler.add_job(
                run_scheduled_newsletter,
                trigger=trigger,
                args=[schedule.id],
                id=job_id,
                replace_existing=True,
                name=schedule.name
            )
            
            logger.info(f"Scheduled cron job '{schedule.name}': {schedule.cron_expression} ({admin_tz})")
            print(f"✅ Created cron job: {job_id}")
            
        elif schedule.schedule_type == 'date' and schedule.specific_date:
            # Конвертируем в UTC-aware datetime
            utc_time = convert_admin_time_to_utc(schedule.specific_date, admin_tz)
            
            scheduler.add_job(
                run_scheduled_newsletter,
                trigger=DateTrigger(utc_time),
                args=[schedule.id],
                id=job_id,
                replace_existing=True,
                name=schedule.name
            )
            
            logger.info(f"Scheduled one-time job '{schedule.name}': {schedule.specific_date} ({admin_tz}) -> {utc_time} (UTC)")
            print(f"✅ Created date job: {job_id}")
            
    except Exception as e:
        print(f"❌ Error creating job {job_id}: {str(e)}")
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

