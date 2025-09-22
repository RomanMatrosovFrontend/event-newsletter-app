from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.core.auth import get_current_admin

router = APIRouter()


@router.post("/", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    # Проверка дублирования email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Инициализируем модель с учётом is_subscribed
    db_user = models.User(
        email=user.email,
        is_subscribed=user.is_subscribed
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Сохраняем категории
    if user.categories:
        for category in user.categories:
            db.execute(
                models.user_categories.insert().values(
                    user_id=db_user.id,
                    category=category
                )
            )
    
    # Сохраняем города
    if user.cities:
        for city in user.cities:
            db.execute(
                models.user_cities.insert().values(
                    user_id=db_user.id,
                    city=city
                )
            )
    
    # Сохраняем типы подписок
    if user.subscription_types:
        for subscription_type in user.subscription_types:
            st = db.query(models.SubscriptionType).filter(
                models.SubscriptionType.code == subscription_type
            ).first()
            if st:
                db.execute(
                    models.user_subscription_types.insert().values(
                        user_id=db_user.id,
                        subscription_type_id=st.id
                    )
                )
    
    db.commit()
    
    # Формируем ответ
    categories = [
        row.category for row in db.execute(
            models.user_categories.select().where(
                models.user_categories.c.user_id == db_user.id
            )
        ).fetchall()
    ]
    cities = [
        row.city for row in db.execute(
            models.user_cities.select().where(
                models.user_cities.c.user_id == db_user.id
            )
        ).fetchall()
    ]
    subscription_types = []
    for row in db.execute(
        models.user_subscription_types.select().where(
            models.user_subscription_types.c.user_id == db_user.id
        )
    ).fetchall():
        st = db.query(models.SubscriptionType).get(row.subscription_type_id)
        if st:
            subscription_types.append(st.code)
    
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        is_subscribed=db_user.is_subscribed,
        categories=categories,
        cities=cities,
        subscription_types=subscription_types,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    users = db.query(models.User).offset(skip).limit(limit).all()
    result = []
    for u in users:
        categories = [
            row.category for row in db.execute(
                models.user_categories.select().where(
                    models.user_categories.c.user_id == u.id
                )
            ).fetchall()
        ]
        cities = [
            row.city for row in db.execute(
                models.user_cities.select().where(
                    models.user_cities.c.user_id == u.id
                )
            ).fetchall()
        ]
        subscription_types = []
        for row in db.execute(
            models.user_subscription_types.select().where(
                models.user_subscription_types.c.user_id == u.id
            )
        ).fetchall():
            st = db.query(models.SubscriptionType).get(row.subscription_type_id)
            if st:
                subscription_types.append(st.code)
        result.append(
            schemas.User(
                id=u.id,
                email=u.email,
                is_subscribed=u.is_subscribed,
                categories=categories,
                cities=cities,
                subscription_types=subscription_types,
                created_at=u.created_at,
                updated_at=u.updated_at
            )
        )
    return result


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    categories = [
        row.category for row in db.execute(
            models.user_categories.select().where(
                models.user_categories.c.user_id == user_id
            )
        ).fetchall()
    ]
    cities = [
        row.city for row in db.execute(
            models.user_cities.select().where(
                models.user_cities.c.user_id == user_id
            )
        ).fetchall()
    ]
    subscription_types = []
    for row in db.execute(
        models.user_subscription_types.select().where(
            models.user_subscription_types.c.user_id == user_id
        )
    ).fetchall():
        st = db.query(models.SubscriptionType).get(row.subscription_type_id)
        if st:
            subscription_types.append(st.code)
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        is_subscribed=db_user.is_subscribed,
        categories=categories,
        cities=cities,
        subscription_types=subscription_types,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


@router.get("/email/{email}", response_model=schemas.User)
def read_user_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    categories = [
        row.category for row in db.execute(
            models.user_categories.select().where(
                models.user_categories.c.user_id == db_user.id
            )
        ).fetchall()
    ]
    cities = [
        row.city for row in db.execute(
            models.user_cities.select().where(
                models.user_cities.c.user_id == db_user.id
            )
        ).fetchall()
    ]
    subscription_types = []
    for row in db.execute(
        models.user_subscription_types.select().where(
            models.user_subscription_types.c.user_id == db_user.id
        )
    ).fetchall():
        st = db.query(models.SubscriptionType).get(row.subscription_type_id)
        if st:
            subscription_types.append(st.code)
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        is_subscribed=db_user.is_subscribed,
        categories=categories,
        cities=cities,
        subscription_types=subscription_types,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Обновление email
    if user.email is not None:
        exists = db.query(models.User).filter(
            models.User.email == user.email,
            models.User.id != user_id
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user.email
    
    # Обновление статуса подписки
    if user.is_subscribed is not None:
        db_user.is_subscribed = user.is_subscribed
    
    # Обновление категорий
    if user.categories is not None:
        db.execute(
            models.user_categories.delete().where(
                models.user_categories.c.user_id == user_id
            )
        )
        for category in user.categories:
            db.execute(
                models.user_categories.insert().values(
                    user_id=user_id,
                    category=category
                )
            )
    
    # Обновление городов
    if user.cities is not None:
        db.execute(
            models.user_cities.delete().where(
                models.user_cities.c.user_id == user_id
            )
        )
        for city in user.cities:
            db.execute(
                models.user_cities.insert().values(
                    user_id=user_id,
                    city=city
                )
            )
    
    # Обновление типов подписок
    if user.subscription_types is not None:
        db.execute(
            models.user_subscription_types.delete().where(
                models.user_subscription_types.c.user_id == user_id
            )
        )
        for subscription_type in user.subscription_types:
            # Найти ID типа подписки по коду
            st = db.query(models.SubscriptionType).filter(
                models.SubscriptionType.code == subscription_type
            ).first()
            if st:
                db.execute(
                    models.user_subscription_types.insert().values(
                        user_id=user_id,
                        subscription_type_id=st.id
                    )
                )
    
    db.commit()
    db.refresh(db_user)
    
    # Получение данных для ответа
    categories = [
        row.category for row in db.execute(
            models.user_categories.select().where(
                models.user_categories.c.user_id == user_id
            )
        ).fetchall()
    ]
    cities = [
        row.city for row in db.execute(
            models.user_cities.select().where(
                models.user_cities.c.user_id == user_id
            )
        ).fetchall()
    ]
    subscription_types = []
    for row in db.execute(
        models.user_subscription_types.select().where(
            models.user_subscription_types.c.user_id == user_id
        )
    ).fetchall():
        st = db.query(models.SubscriptionType).get(row.subscription_type_id)
        if st:
            subscription_types.append(st.code)
    
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        is_subscribed=db_user.is_subscribed,
        categories=categories,
        cities=cities,
        subscription_types=subscription_types,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


@router.put("/email/{email}", response_model=schemas.User)
def update_user_by_email(
    email: str,
    user_data: schemas.UserEmailUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.new_email is not None:
        exists = db.query(models.User).filter(
            models.User.email == user_data.new_email,
            models.User.id != db_user.id
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user_data.new_email
    if user_data.categories is not None:
        db.execute(
            models.user_categories.delete().where(
                models.user_categories.c.user_id == db_user.id
            )
        )
        for category in user_data.categories:
            db.execute(
                models.user_categories.insert().values(
                    user_id=db_user.id,
                    category=category.strip()
                )
            )
    db.commit()
    db.refresh(db_user)
    categories = [
        row.category for row in db.execute(
            models.user_categories.select().where(
                models.user_categories.c.user_id == db_user.id
            )
        ).fetchall()
    ]
    cities = [
        row.city for row in db.execute(
            models.user_cities.select().where(
                models.user_cities.c.user_id == db_user.id
            )
        ).fetchall()
    ]
    subscription_types = []
    for row in db.execute(
        models.user_subscription_types.select().where(
            models.user_subscription_types.c.user_id == db_user.id
        )
    ).fetchall():
        st = db.query(models.SubscriptionType).get(row.subscription_type_id)
        if st:
            subscription_types.append(st.code)
    return schemas.User(
        id=db_user.id,
        email=db_user.email,
        is_subscribed=db_user.is_subscribed,
        categories=categories,
        cities=cities,
        subscription_types=subscription_types,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.execute(
        models.user_categories.delete().where(
            models.user_categories.c.user_id == user_id
        )
    )
    db.execute(
        models.user_cities.delete().where(
            models.user_cities.c.user_id == user_id
        )
    )
    db.execute(
        models.user_subscription_types.delete().where(
            models.user_subscription_types.c.user_id == user_id
        )
    )
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

