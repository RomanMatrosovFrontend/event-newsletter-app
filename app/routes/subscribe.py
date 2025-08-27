from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.post("/api/subscribe/", response_model=schemas.SubscribeResponse)
async def subscribe(
    subscribe_data: schemas.SubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Эндпоинт для подписки пользователей через iframe.
    Принимает email и список категорий, создает или обновляет пользователя.
    """
    try:
        # Ищем пользователя по email
        db_user = db.query(models.User).filter(
            models.User.email == subscribe_data.email
        ).first()
        
        if db_user:
            # Пользователь существует - обновляем категории
            # Удаляем старые категории
            delete_stmt = models.user_categories.delete().where(
                models.user_categories.c.user_id == db_user.id
            )
            db.execute(delete_stmt)
            
            # Добавляем новые категории
            for category in subscribe_data.categories:
                insert_stmt = models.user_categories.insert().values(
                    user_id=db_user.id,
                    category=category.strip()
                )
                db.execute(insert_stmt)
            
            db.commit()
            
            return {
                "status": "success",
                "message": "User categories updated successfully"
            }
        else:
            # Пользователь не существует - создаем нового
            db_user = models.User(email=subscribe_data.email)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Добавляем категории
            for category in subscribe_data.categories:
                insert_stmt = models.user_categories.insert().values(
                    user_id=db_user.id,
                    category=category.strip()
                )
                db.execute(insert_stmt)
            
            db.commit()
            
            return {
                "status": "success", 
                "message": "User created and subscribed successfully"
            }
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing subscription: {str(e)}"
        )