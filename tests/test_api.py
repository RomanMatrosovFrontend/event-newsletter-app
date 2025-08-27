import pytest
from fastapi import status
from app.models import NewsletterSchedule

def test_create_schedule_api(client, db_session):
    """Тест создания расписания через API"""
    schedule_data = {
        "name": "Тестовая рассылка",
        "description": "Каждый понедельник",
        "schedule_type": "cron", 
        "cron_expression": "0 10 * * 1",
        "is_active": True
    }
    
    response = client.post("/schedules/", json=schedule_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Тестовая рассылка"
    assert data["is_active"] is True

def test_get_schedules_api(client, db_session):
    """Тест получения списка расписаний"""
    response = client.get("/schedules/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

