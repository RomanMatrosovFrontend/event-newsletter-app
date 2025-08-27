from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/unsubscribe", tags=["unsubscribe"])

@router.get("/{user_id}", response_model=schemas.Message)
async def unsubscribe_user(user_id: int, db: Session = Depends(get_db)):
    """
    Отписать пользователя от всех рассылок (мягкое удаление)
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Мягкое удаление - помечаем как отписавшегося
    # Вместо полного удаления из БД
    user.is_subscribed = False
    db.commit()
    
    return {"message": "You have been successfully unsubscribed from all newsletters"}