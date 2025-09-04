from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.post("/api/subscribe/", response_model=schemas.SubscribeResponse)
async def subscribe(subscribe_data: schemas.SubscribeRequest, db: Session = Depends(get_db)):
    try:
        # Ищем пользователя по email
        db_user = db.query(models.User).filter(models.User.email == subscribe_data.email).first()
        
        if db_user:
            # Пользователь существует — обновляем категории и города
            db.execute(models.user_categories.delete().where(models.user_categories.c.user_id == db_user.id))
            db.execute(models.user_cities.delete().where(models.user_cities.c.user_id == db_user.id))
            
            for category in subscribe_data.categories:
                db.execute(models.user_categories.insert().values(
                    user_id=db_user.id,
                    category=category.strip()
                ))
            
            for city in subscribe_data.cities:
                db.execute(models.user_cities.insert().values(
                    user_id=db_user.id,
                    city=city.strip()
                ))
            
            db.commit()
        else:
            # Пользователь не существует — создаём нового
            db_user = models.User(email=subscribe_data.email)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            for category in subscribe_data.categories:
                db.execute(models.user_categories.insert().values(
                    user_id=db_user.id,
                    category=category.strip()
                ))
            
            for city in subscribe_data.cities:
                db.execute(models.user_cities.insert().values(
                    user_id=db_user.id,
                    city=city.strip()
                ))
            
            db.commit()
        
        return {"status": "success", "message": "User preferences updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing subscription: {str(e)}")

