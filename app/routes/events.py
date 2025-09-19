from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import ValidationError
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io

from app.database import get_db
from app import models, schemas
from app.utils.csv_parser import parse_csv_row
from app.utils.event_matcher import get_events_for_user
from app.core.auth import get_current_admin


router = APIRouter(tags=["events"])


@router.post("/upload-csv/")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    results = {"total_rows": 0, "successful": 0, "failed": 0, "errors": []}
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        contents = await file.read()
        content_str = contents.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content_str), delimiter=';', quotechar='"')
        rows = list(reader)
        results["total_rows"] = len(rows)
        for idx, row in enumerate(rows):
            try:
                ev = parse_csv_row(row)
                if not ev:
                    results["failed"] += 1
                    results["errors"].append(f"Row {idx+2}: Missing required fields")
                    continue
                if db.query(models.Event).filter(models.Event.url == ev.url).first():
                    results["failed"] += 1
                    results["errors"].append(f"Row {idx+2}: URL exists")
                    continue
                db_event = models.Event(**ev.dict())
                db.add(db_event); db.commit(); db.refresh(db_event)
                results["successful"] += 1
            except Exception as e:
                db.rollback()
                results["failed"] += 1
                results["errors"].append(f"Row {idx+2}: {e}")
        return {"message": "CSV processing completed", "results": results}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-events/")
async def clear_all_events(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    try:
        db.query(models.Event).delete(); db.commit()
        return {"message": "All events have been deleted", "deleted": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count", response_model=schemas.EventCountResponse)
async def get_events_count(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    return schemas.EventCountResponse(count=db.query(models.Event).count())


@router.get("/user/{user_id}/recommended", response_model=List[schemas.Event])
async def get_recommended_events(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return get_events_for_user(db, user)


@router.get("/", response_model=List[schemas.Event])
async def read_events(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    q = db.query(models.Event)
    if category: q = q.filter(models.Event.category == category)
    if city:     q = q.filter(models.Event.city == city)
    if hasattr(models.Event, "created_at"):
        q = q.order_by(desc(models.Event.created_at))
    return q.offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.Event)
async def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    try:
        db_event = models.Event(**event.dict())
        db.add(db_event); db.commit(); db.refresh(db_event)
        return db_event
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception:
        db.rollback()
        raise HTTPException(status_code=422, detail="Invalid data")


@router.get("/{event_id}", response_model=schemas.Event)
async def read_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    ev = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not ev: raise HTTPException(status_code=404, detail="Not found")
    return ev


@router.put("/{event_id}", response_model=schemas.Event)
async def update_event(
    event_id: int,
    event: schemas.EventUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    ev = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not ev: raise HTTPException(status_code=404, detail="Not found")
    for f, v in event.dict(exclude_unset=True).items(): setattr(ev, f, v)
    db.commit(); db.refresh(ev)
    return ev


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    ev = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not ev: raise HTTPException(status_code=404, detail="Not found")
    db.delete(ev); db.commit()
    return {"message": "Event deleted successfully"}

