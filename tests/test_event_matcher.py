import pytest
from app.utils.event_matcher import get_events_for_user
from app.models import User, Event, user_categories

def test_get_events_for_user_with_category(db_session):
    """Тест подбора событий по категории пользователя"""
    # Создаем пользователя
    user = User(email="test@example.com", is_subscribed=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Создаем события
    event1 = Event(title="Концерт", category="music", dates=["2024-12-01"], languages=["RU"], url="https://example.com/1")
    event2 = Event(title="Конференция", category="tech", dates=["2024-12-02"], languages=["RU"], url="https://example.com/2")
    db_session.add_all([event1, event2])
    db_session.commit()
    
    # Добавляем пользователю категорию "music"
    db_session.execute(
        user_categories.insert().values(user_id=user.id, category="music")
    )
    db_session.commit()
    
    # Тестируем
    events = get_events_for_user(db_session, user)
    
    assert len(events) == 1
    assert events[0].category == "music"
    assert events[0].title == "Концерт"
