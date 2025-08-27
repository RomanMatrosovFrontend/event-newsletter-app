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

router = APIRouter()

# 1. СТАТИЧЕСКИЕ маршруты ПЕРВЫМИ (чтобы не конфликтовали с {id})
@router.post("/upload-csv/")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загружает CSV файл с разделителем ; и кавычками
    """
    results = {
        "total_rows": 0,
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Читаем CSV файл
        contents = await file.read()
        content_str = contents.decode('utf-8')
        
        # Для вашего формата используем разделитель ; и кавычки "
        csv_reader = csv.DictReader(
            io.StringIO(content_str), 
            delimiter=';',
            quotechar='"'
        )
        
        rows = list(csv_reader)
        results["total_rows"] = len(rows)
        
        print(f"Found {len(rows)} rows, columns: {csv_reader.fieldnames}")
        
        # Обрабатываем каждую строку
        for index, row in enumerate(rows):
            try:
                print(f"Processing row {index + 1}: {row}")
                
                event_data = parse_csv_row(row)
                
                if not event_data:
                    results["failed"] += 1
                    results["errors"].append(f"Row {index + 2}: Missing required fields (Title or Url)")
                    continue
                
                # Проверяем существование события
                existing_event = db.query(models.Event).filter(
                    models.Event.url == event_data.url
                ).first()
                
                if existing_event:
                    results["failed"] += 1
                    results["errors"].append(f"Row {index + 2}: Event with URL '{event_data.url}' already exists")
                    continue
                
                # Создаем событие
                db_event = models.Event(**event_data.dict())
                db.add(db_event)
                db.commit()
                db.refresh(db_event)
                
                results["successful"] += 1
                print(f"Successfully added event: {db_event.title}")
                
            except Exception as e:
                db.rollback()
                results["failed"] += 1
                error_msg = f"Row {index + 2}: {str(e)}"
                results["errors"].append(error_msg)
                print(error_msg)
                continue
        
        return {
            "message": "CSV processing completed",
            "results": results
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8 encoding.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/user/{user_id}/recommended", response_model=List[schemas.Event])
def get_recommended_events(user_id: int, db: Session = Depends(get_db)):
    """
    Возвращает события, рекомендованные для пользователя по его категориям.
    """
    # Получаем пользователя
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Получаем рекомендованные события
    recommended_events = get_events_for_user(db, db_user)
    
    return recommended_events

# 2. БАЗОВЫЕ CRUD операции
@router.get("/", response_model=List[schemas.Event])
def read_events(
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """READ ALL - Получение всех событий с фильтрацией"""
    query = db.query(models.Event)
    
    # Фильтрация
    if category:
        query = query.filter(models.Event.category == category)
    if city:
        query = query.filter(models.Event.city == city)
    
    # Сортировка по created_at DESC (если поле есть)
    if hasattr(models.Event, 'created_at'):
        query = query.order_by(desc(models.Event.created_at))
    
    events = query.offset(skip).limit(limit).all()
    return events

@router.post("/", response_model=schemas.Event)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    """CREATE - Создание нового события с валидацией"""
    try:
        db_event = models.Event(**event.dict())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=422, detail="Invalid data provided")

# 3. ДИНАМИЧЕСКИЕ маршруты с {id} В КОНЦЕ
@router.get("/{event_id}", response_model=schemas.Event)
def read_event(event_id: int, db: Session = Depends(get_db)):
    """READ ONE - Получение одного события по ID"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@router.put("/{event_id}", response_model=schemas.Event)
def update_event(event_id: int, event: schemas.EventUpdate, db: Session = Depends(get_db)):
    """UPDATE - Обновление события"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = event.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """DELETE - Удаление события"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(db_event)
    db.commit()
    return {"message": "Event deleted successfully"}
