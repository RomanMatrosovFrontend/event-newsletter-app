from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
from app import models

def get_events_for_user(db: Session, user: models.User) -> List[models.Event]:
    """
    Возвращает события, которые соответствуют хотя бы одной категории пользователя.
    События сортируются по дате создания (новые сначала).
    
    Args:
        db: Сессия базы данных
        user: Объект пользователя с категориями
    
    Returns:
        List[models.Event]: Список подходящих событий
    """
    # Получаем категории пользователя из association table
    categories_stmt = models.user_categories.select().where(
        models.user_categories.c.user_id == user.id
    )
    categories_result = db.execute(categories_stmt).fetchall()
    user_categories = [row.category for row in categories_result]
    
    if not user_categories:
        return []  # Если у пользователя нет категорий
    
    # Создаем условия для фильтрации
    conditions = []
    for category in user_categories:
        # Ищем события, у которых в JSON массиве categories есть эта категория
        conditions.append(
            models.Event.category.like(f'%{category}%')
        )
    
    # Выбираем события, где есть хотя бы одно совпадение
    events = db.query(models.Event).filter(
        or_(*conditions)  # ХОТЯ БЫ ОДНО условие должно быть истинно
    ).order_by(
        models.Event.created_at.desc()  # Сортировка по дате (новые сначала)
    ).all()
    
    return events