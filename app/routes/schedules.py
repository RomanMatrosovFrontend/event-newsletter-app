from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services.advanced_scheduler import scheduler, schedule_job

router = APIRouter(tags=["schedules"])

@router.get("/", response_model=List[schemas.Schedule])
def get_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    schedules = db.query(models.NewsletterSchedule).offset(skip).limit(limit).all()
    
    result = []
    for schedule in schedules:
        schedule_data = schedule.__dict__.copy()
        
        # ДОБАВЬ ЭТИ СТРОКИ ДЛЯ ДИАГНОСТИКИ:
        job_id = f"schedule_{schedule.id}"
        job = scheduler.get_job(job_id)
        
        print(f"Schedule ID: {schedule.id}")
        print(f"Job ID: {job_id}")
        print(f"Job exists: {job is not None}")
        if job:
            print(f"Next run time: {job.next_run_time}")
        
        schedule_data["next_run_time"] = job.next_run_time if job else None
        result.append(schedule_data)
    
    return result

@router.get("/{schedule_id}", response_model=schemas.Schedule)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(models.NewsletterSchedule).filter(
        models.NewsletterSchedule.id == schedule_id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.post("/", response_model=schemas.Schedule)
def create_schedule(schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)):
    # Валидация cron выражения
    if schedule.schedule_type == 'cron' and schedule.cron_expression:
        try:
            from apscheduler.triggers.cron import CronTrigger
            CronTrigger.from_crontab(schedule.cron_expression)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cron expression")
    
    db_schedule = models.NewsletterSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    # Добавляем задачу в планировщик
    if db_schedule.is_active:
        schedule_job(db_schedule, db)
    
    return db_schedule

@router.put("/{schedule_id}", response_model=schemas.Schedule)
def update_schedule(schedule_id: int, schedule_data: schemas.ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.query(models.NewsletterSchedule).filter(
        models.NewsletterSchedule.id == schedule_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = schedule_data.dict(exclude_unset=True)
    
    if 'name' in update_data and update_data['name'] is None:
        update_data.pop('name')
    
    for field, value in update_data.items():
        if value is not None:  # Добавляем проверку на None
            setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

    # Обновляем задачу в планировщике
    job_id = f"schedule_{schedule.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    if schedule.is_active:
        schedule_job(schedule, db)

    return schedule

@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(models.NewsletterSchedule).filter(
        models.NewsletterSchedule.id == schedule_id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Удаляем задачу из планировщика
    job_id = f"schedule_{schedule.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}

@router.post("/{schedule_id}/run")
def run_schedule_now(schedule_id: int, db: Session = Depends(get_db)):
    """Запуск расписания вручную прямо сейчас"""
    schedule = db.query(models.NewsletterSchedule).filter(
        models.NewsletterSchedule.id == schedule_id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    from app.services.advanced_scheduler import run_scheduled_newsletter
    run_scheduled_newsletter(schedule_id)
    
    return {"message": f"Schedule '{schedule.name}' started manually"}
