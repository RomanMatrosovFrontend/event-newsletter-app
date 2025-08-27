import pytest
from app.models import User, Event

def test_create_user(db_session):
    """Простой тест создания пользователя"""
    user = User(email="test@example.com", is_subscribed=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_subscribed is True

def test_create_event(db_session):
    """Простой тест создания события"""
    event = Event(
        title="Тестовое событие",
        category="test",
        dates=["2024-12-01"],
        languages=["RU"],
        url="https://example.com/test"
    )
    db_session.add(event)
    db_session.commit()
    
    assert event.id is not None
    assert event.title == "Тестовое событие"
