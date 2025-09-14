import logging
import pytz
from datetime import datetime, time
from dateutil import parser
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.combining import OrTrigger
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import newsletter_service
from app.models import NewsletterSchedule
logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(daemon=True)

# Маппинг номеров дней недели (ISO) на английские сокращения для CronTrigger
DAY_OF_WEEK_MAP = {
    1: 'mon',
    2: 'tue',
    3: 'wed',
    4: 'thu',
    5: 'fri',
    6: 'sat',
    7: 'sun'
}

def init_scheduler():
    """Инициализация планировщика при запуске приложения"""
    if not scheduler.running:
        scheduler.start()
        load_all_schedules()
        logger.info("Advanced scheduler initialized")

def load_all_schedules():
    """Загрузка всех активных расписаний из БД"""
    db = None
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
        if admin_datetime.tzinfo is None:
            admin_aware = admin_tz.localize(admin_datetime)
        else:
            admin_aware = admin_datetime.astimezone(admin_tz)
        utc_time = admin_aware.astimezone(utc_tz)
        return utc_time
    except Exception as e:
        logger.error(f"Error converting time to UTC: {str(e)}")
        return admin_datetime.replace(tzinfo=pytz.UTC)

def to_apscheduler_days(days):
    """Преобразует дни недели ISO (1—7) в строку для CronTrigger"""
    return ','.join(DAY_OF_WEEK_MAP[day] for day in days if day in DAY_OF_WEEK_MAP)

def schedule_job(schedule, db):
    job_id = f"schedule_{schedule.id}"
    config = getattr(schedule, 'schedule_config', None)
    admin_tz = schedule.admin_timezone or "UTC"
    print(f"Creating job {job_id} for schedule: {schedule.name}")
    print(f"Admin timezone: {admin_tz}")
    try:
        timezone = pytz.timezone(admin_tz)
        if config:
            periodicity = config.get("periodicity")
            if periodicity == "weekly":
                days = config.get("days", [])
                hour = config.get("hour", 0)
                minute = config.get("minute", 0)
                if not days:
                    raise ValueError("Days for weekly schedule not specified")
                # **Здесь исправляем: используем именованные дни недели**
                day_str = to_apscheduler_days(days)
                print(f"Selected days: {days}")
                print(f"Day string for CronTrigger: {day_str}")
                print(f"Time: {hour}:{minute} (timezone: {timezone})")
                trigger = CronTrigger(
                    day_of_week=day_str,
                    hour=hour,
                    minute=minute,
                    timezone=timezone
                )
            elif periodicity == "interval":
                start_date_str = config.get("start_date")
                days_interval = config.get("days_interval")
                hour = config.get("hour", 0)
                minute = config.get("minute", 0)
                if start_date_str is None or days_interval is None:
                    raise ValueError('start_date and days_interval required for interval periodicity')
                start_date = parser.parse(start_date_str)
                start_date = timezone.localize(datetime.combine(start_date, time(hour, minute)))
                trigger = IntervalTrigger(days=days_interval, start_date=start_date)
            elif periodicity == "single":
                datetime_str = config.get("datetime")
                if datetime_str is None:
                    raise ValueError('datetime required for single periodicity')
                run_date = parser.parse(datetime_str)
                trigger = DateTrigger(run_date=timezone.localize(run_date))
            else:
                raise ValueError(f"Unknown periodicity: {periodicity}")
        else:
            if schedule.schedule_type == 'cron' and schedule.cron_expression:
                trigger = CronTrigger.from_crontab(
                    schedule.cron_expression,
                    timezone=timezone
                )
            elif schedule.schedule_type == 'date' and schedule.specific_date:
                utc_time = convert_admin_time_to_utc(schedule.specific_date, admin_tz)
                trigger = DateTrigger(run_date=utc_time)
            else:
                raise ValueError('No valid scheduling data found')
        scheduler.add_job(
            run_scheduled_newsletter,
            trigger=trigger,
            args=[schedule.id],
            id=job_id,
            replace_existing=True,
            name=schedule.name
        )
        print(f"✅ Created job: {job_id}")
    except Exception as e:
        print(f"❌ Error creating job {job_id}: {str(e)}")
        logger.error(f"Failed to schedule job {job_id}: {str(e)}")

def run_scheduled_newsletter(schedule_id: int):
    logger.info(f"Запущена рассылка для расписания {schedule_id}")
    db = None
    try:
        db_generator = get_db()
        db = next(db_generator)
        schedule = db.query(NewsletterSchedule).filter(
            NewsletterSchedule.id == schedule_id
        ).first()
        if not schedule or not schedule.is_active:
            logger.warning(f"Schedule {schedule_id} not found or inactive")
            return
        logger.info(f"Running scheduled newsletter: {schedule.name}")
        schedule.last_run = datetime.utcnow()
        db.commit()
        if schedule.user_ids:
            newsletter_service.send_newsletter_to_users(db, schedule.user_ids)
        else:
            newsletter_service.send_newsletter_to_all_users(db)
    except Exception as e:
        logger.error(f"Error in scheduled newsletter {schedule_id}: {str(e)}")
    finally:
        if db:
            db.close()
            logger.info(f"Рассылка завершена для расписания {schedule_id}")

