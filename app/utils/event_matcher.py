from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, _not
from typing import List
from app import models

def get_events_for_user(db: Session, user: models.User) -> List[models.Event]:
    # Получаем категории пользователя
    categories_stmt = models.user_categories.select().where(
        models.user_categories.c.user_id == user.id
    )
    categories_result = db.execute(categories_stmt).fetchall()
    user_categories = [row.category for row in categories_result]
    
    if not user_categories:
        return []  # Если нет категорий — нет событий
    
    # Получаем города пользователя
    cities_stmt = models.user_cities.select().where(
        models.user_cities.c.user_id == user.id
    )
    cities_result = db.execute(cities_stmt).fetchall()
    user_cities = [row.city for row in cities_result]
    
    if not user_cities:
        return []  # Если нет городов — нет событий
    
    # Определим основной список городов
    main_cities = {'Подгорица', 'Будва', 'Херцег-Нови', 'Тиват', 'Бар'}
    
    # Формируем условия по категориям (как было)
    cond_category = []
    for category in user_categories:
        cond_category.append(models.Event.category.like(f'%{category}%'))
    
    # Формируем условия по городам
    cond_city = []
    other_cities_selected = 'Другие города' in user_cities
    for city in user_cities:
        if city in main_cities:
            cond_city.append(models.Event.city == city)
        elif city == 'Другие города':
            # Все города, которых нет в main_cities
            cond_city.append(and_(
                models.Event.city != None,
                not_(models.Event.city.in_(main_cities))
            ))
    
    # Если других городов нет, исключаем пустые строки
    if not [c for c in user_cities if c != 'Другие города']:
        cond_city = [and_(models.Event.city != None, not_(models.Event.city.in_(main_cities)))]
    if not cond_city:
        return []  # Без городов нет событий
    
    queries = []
    for cc in cond_category:
        for c in cond_city:
            queries.append(and_(cc, c))
    
    # Отбираем события по категориям и городам, сортируем по дате
    events = db.query(models.Event).filter(
        or_(*queries)
    ).order_by(
        models.Event.created_at.desc()
    ).all()
    
    return events
