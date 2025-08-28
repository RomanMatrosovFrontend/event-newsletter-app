from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from app.database import get_db
from app import models, schemas

router = APIRouter()

# CREATE - Создание нового пользователя
@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создает нового пользователя с email и списком категорий.
    """
    # Проверяем, существует ли пользователь с таким email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Создаем пользователя
    db_user = models.User(email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Добавляем категории
    if user.categories:
        for category in user.categories:
            stmt = models.user_categories.insert().values(
                user_id=db_user.id,
                category=category
            )
            db.execute(stmt)
        db.commit()
    
    # ВАЖНО: Получаем категории для возврата
    categories_stmt = models.user_categories.select().where(
        models.user_categories.c.user_id == db_user.id
    )
    categories_result = db.execute(categories_stmt).fetchall()
    categories = [row.category for row in categories_result]
    
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        categories=categories,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

# READ ALL - Получение всех пользователей
@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Возвращает список всех пользователей с пагинацией.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    
    # Для каждого пользователя получаем категории
    result = []
    for user in users:
        # Получаем категории пользователя
        categories_stmt = models.user_categories.select().where(
            models.user_categories.c.user_id == user.id
        )
        categories_result = db.execute(categories_stmt).fetchall()
        categories = [row.category for row in categories_result]
        
        user_data = schemas.User(
            id=user.id,
            email=user.email,
            categories=categories,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        result.append(user_data)
    
    return result

# READ ONE - Получение одного пользователя по ID
@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Возвращает пользователя по его ID.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Получаем категории пользователя
    categories_stmt = models.user_categories.select().where(
        models.user_categories.c.user_id == user_id
    )
    categories_result = db.execute(categories_stmt).fetchall()
    categories = [row.category for row in categories_result]
    
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        categories=categories,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

# READ BY EMAIL - Получение пользователя по email
@router.get("/email/{email}", response_model=schemas.User)
def read_user_by_email(email: str, db: Session = Depends(get_db)):
    """
    Возвращает пользователя по email.
    """
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Получаем категории пользователя
    categories_stmt = models.user_categories.select().where(
        models.user_categories.c.user_id == db_user.id
    )
    categories_result = db.execute(categories_stmt).fetchall()
    categories = [row.category for row in categories_result]
    
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        categories=categories,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

# UPDATE - Обновление пользователя
@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    Обновляет данные пользователя.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Обновляем email если передан
    if user.email is not None:
        # Проверяем, не занят ли email другим пользователем
        existing_user = db.query(models.User).filter(
            models.User.email == user.email,
            models.User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user.email
    
    # Обновляем категории если переданы
    if user.categories is not None:
        # Удаляем старые категории
        delete_stmt = models.user_categories.delete().where(
            models.user_categories.c.user_id == user_id
        )
        db.execute(delete_stmt)
        
        # Добавляем новые категории
        for category in user.categories:
            insert_stmt = models.user_categories.insert().values(
                user_id=user_id,
                category=category
            )
            db.execute(insert_stmt)
    
    db.commit()
    db.refresh(db_user)
    
    # Получаем обновленные категории
    categories_stmt = models.user_categories.select().where(
        models.user_categories.c.user_id == user_id
    )
    categories_result = db.execute(categories_stmt).fetchall()
    categories = [row.category for row in categories_result]
    
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        categories=categories,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

# UPDATE BY EMAIL - Обновление пользователя по email  
@router.put("/email/{email}", response_model=schemas.User)
def update_user_by_email(
    email: str, 
    user_data: schemas.UserEmailUpdate, 
    db: Session = Depends(get_db)
):
    """
    Обновляет пользователя по email (смена email и/или категорий).
    """
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Обновляем email если передан новый
    if user_data.new_email is not None:
        # Проверяем, не занят ли новый email другим пользователем
        existing_user = db.query(models.User).filter(
            models.User.email == user_data.new_email,
            models.User.id != db_user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_user.email = user_data.new_email

    # Обновляем категории если переданы
    if user_data.categories is not None:
        # Удаляем старые категории
        delete_stmt = models.user_categories.delete().where(
            models.user_categories.c.user_id == db_user.id
        )
        db.execute(delete_stmt)
        
        # Добавляем новые категории
        for category in user_data.categories:
            insert_stmt = models.user_categories.insert().values(
                user_id=db_user.id,
                category=category.strip()
            )
            db.execute(insert_stmt)

    db.commit()
    db.refresh(db_user)

    # Получаем обновленные категории для ответа
    categories_stmt = models.user_categories.select().where(
        models.user_categories.c.user_id == db_user.id
    )
    categories_result = db.execute(categories_stmt).fetchall()
    categories = [row.category for row in categories_result]

    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        categories=categories,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

# DELETE - Удаление пользователя
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Удаляет пользователя по ID.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Сначала удаляем категории пользователя
    delete_categories_stmt = models.user_categories.delete().where(
        models.user_categories.c.user_id == user_id
    )
    db.execute(delete_categories_stmt)
    
    # Затем удаляем пользователя
    db.delete(db_user)
    db.commit()
    
    return {"message": "User deleted successfully"}
