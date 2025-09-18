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
        job_id = f"schedule_{schedule.id}"
        job = scheduler.get_job(job_id)
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
    # Валидация schedule_config
    cfg = schedule.schedule_config
    if cfg.periodicity == "weekly" and not cfg.days:
        raise HTTPException(status_code=422, detail="Days for weekly schedule not specified")
    if cfg.periodicity == "date" and not cfg.datetime:
        raise HTTPException(status_code=422, detail="Datetime for date schedule not specified")
    if cfg.days_interval and cfg.days:
        raise HTTPException(status_code=422, detail="Cannot specify both days_interval and days")

    db_schedule = models.NewsletterSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
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
    # Валидация schedule_config при обновлении
    if "schedule_config" in update_data:
        cfg_data = update_data["schedule_config"]
        cfg = schemas.ScheduleConfig(**cfg_data)
        if cfg.periodicity == "weekly" and not cfg.days:
            raise HTTPException(status_code=422, detail="Days for weekly schedule not specified")
        if cfg.periodicity == "date" and not cfg.datetime:
            raise HTTPException(status_code=422, detail="Datetime for date schedule not specified")
        if cfg.days_interval and cfg.days:
            raise HTTPException(status_code=422, detail="Cannot specify both days_interval and days")

    if 'name' in update_data and update_data['name'] is None:
        update_data.pop('name')

    for field, value in update_data.items():
        if value is not None:
            setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

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
    job_id = f"schedule_{schedule.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}

@router.post("/{schedule_id}/run")
def run_schedule_now(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(models.NewsletterSchedule).filter(
        models.NewsletterSchedule.id == schedule_id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    from app.services.advanced_scheduler import run_scheduled_newsletter
    run_scheduled_newsletter(schedule_id)
    return {"message": f"Schedule '{schedule.name}' started manually"}

