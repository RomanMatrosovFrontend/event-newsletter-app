import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from app.models import NewsletterSchedule
from datetime import datetime, timedelta

class TestSchedulesAPI:
    """Полное тестирование всех эндпоинтов /schedules"""
    
    # GET /schedules/
    def test_get_schedules_empty(self, client):
        """GET /schedules/ - пустой список"""
        response = client.get("/schedules/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_get_schedules_with_data(self, client, db_session):
        """GET /schedules/ - с данными"""
        schedule = NewsletterSchedule(
            name="Тестовая рассылка",
            description="Описание",
            schedule_type="cron",
            cron_expression="0 10 * * 1"
        )
        db_session.add(schedule)
        db_session.commit()
        
        response = client.get("/schedules/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Тестовая рассылка"
        assert data[0]["description"] == "Описание"
    
    # GET /schedules/{id}
    def test_get_schedule_by_id_success(self, client, db_session):
        """GET /schedules/{id} - успешное получение"""
        schedule = NewsletterSchedule(
            name="Конкретная рассылка",
            schedule_type="date",
            specific_date=datetime.now() + timedelta(days=1)
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)
        
        response = client.get(f"/schedules/{schedule.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Конкретная рассылка"
        assert data["schedule_type"] == "date"
    
    def test_get_schedule_by_id_not_found(self, client):
        """GET /schedules/{id} - расписание не найдено"""
        response = client.get("/schedules/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # POST /schedules/
    def test_create_schedule_cron_success(self, client):
        """POST /schedules/ - создание cron расписания"""
        schedule_data = {
            "name": "Еженедельная рассылка",
            "description": "Каждый понедельник в 10:00",
            "schedule_type": "cron",
            "cron_expression": "0 10 * * 1",
            "is_active": True
        }
        
        with patch('app.routes.schedules.schedule_job') as mock_schedule_job:
            response = client.post("/schedules/", json=schedule_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Еженедельная рассылка"
            assert data["is_active"] is True
            assert data["cron_expression"] == "0 10 * * 1"
            
            # Проверяем что задача была добавлена в планировщик
            mock_schedule_job.assert_called_once()
    
    def test_create_schedule_date_success(self, client):
        """POST /schedules/ - создание date расписания"""
        future_date = datetime.now() + timedelta(hours=2)
        schedule_data = {
            "name": "Разовая рассылка",
            "description": "Завтра в полдень", 
            "schedule_type": "date",
            "specific_date": future_date.isoformat(),
            "is_active": True
        }
        
        with patch('app.routes.schedules.schedule_job'):
            response = client.post("/schedules/", json=schedule_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Разовая рассылка"
            assert data["schedule_type"] == "date"
    
    def test_create_schedule_invalid_cron(self, client):
        """POST /schedules/ - некорректный cron"""
        schedule_data = {
            "name": "Неверная рассылка",
            "schedule_type": "cron",
            "cron_expression": "invalid cron expression",
            "is_active": True
        }
        
        response = client.post("/schedules/", json=schedule_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_schedule_with_user_ids(self, client):
        """POST /schedules/ - с конкретными пользователями"""
        schedule_data = {
            "name": "Рассылка для избранных",
            "user_ids": [1, 2, 3],
            "schedule_type": "cron",
            "cron_expression": "0 12 * * *",
            "is_active": True
        }
        
        with patch('app.routes.schedules.schedule_job'):
            response = client.post("/schedules/", json=schedule_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_ids"] == [1, 2, 3]
    
    # PUT /schedules/{id}
    def test_update_schedule_success(self, client, db_session):
        """PUT /schedules/{id} - успешное обновление"""
        schedule = NewsletterSchedule(
            name="Старое название",
            schedule_type="cron", 
            cron_expression="0 10 * * 1",
            is_active=True
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)
        
        update_data = {
            "name": "Новое название",
            "cron_expression": "0 12 * * 2",
            "is_active": False
        }
        
        with patch('app.routes.schedules.scheduler') as mock_scheduler:
            mock_scheduler.get_job.return_value = MagicMock()
            mock_scheduler.remove_job.return_value = None
            
            response = client.put(f"/schedules/{schedule.id}", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Новое название"
            assert data["cron_expression"] == "0 12 * * 2"
            assert data["is_active"] is False
    
    def test_update_schedule_not_found(self, client):
        """PUT /schedules/{id} - расписание не найдено"""
        update_data = {"name": "Новое название"}
        
        response = client.put("/schedules/999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # DELETE /schedules/{id}  
    def test_delete_schedule_success(self, client, db_session):
        """DELETE /schedules/{id} - успешное удаление"""
        schedule = NewsletterSchedule(
            name="Удаляемая рассылка",
            schedule_type="cron",
            cron_expression="0 10 * * 1"
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)
        
        with patch('app.routes.schedules.scheduler') as mock_scheduler:
            mock_scheduler.get_job.return_value = MagicMock()
            mock_scheduler.remove_job.return_value = None
            
            response = client.delete(f"/schedules/{schedule.id}")
            
            assert response.status_code == status.HTTP_200_OK
            assert "deleted successfully" in response.json()["message"]
            
            # Проверяем что задача удалена из планировщика
            mock_scheduler.remove_job.assert_called_once()
    
    def test_delete_schedule_not_found(self, client):
        """DELETE /schedules/{id} - расписание не найдено"""
        response = client.delete("/schedules/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # POST /schedules/{id}/run
    def test_run_schedule_now_success(self, client, db_session):
        """POST /schedules/{id}/run - ручной запуск"""
        schedule = NewsletterSchedule(
            name="Запускаемая рассылка",
            schedule_type="cron",
            cron_expression="0 10 * * 1"
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)
        
        with patch('app.services.advanced_scheduler.run_scheduled_newsletter') as mock_run:
            response = client.post(f"/schedules/{schedule.id}/run")
            
            assert response.status_code == status.HTTP_200_OK
            assert "started manually" in response.json()["message"]
            
            # Проверяем что функция запуска была вызвана
            mock_run.assert_called_once_with(schedule.id)
    
    def test_run_schedule_now_not_found(self, client):
        """POST /schedules/{id}/run - расписание не найдено"""
        response = client.post("/schedules/999/run")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Граничные случаи
    def test_create_schedule_inactive(self, client):
        """POST /schedules/ - создание неактивного расписания"""
        schedule_data = {
            "name": "Неактивная рассылка",
            "schedule_type": "cron",
            "cron_expression": "0 10 * * 1", 
            "is_active": False
        }
        
        with patch('app.routes.schedules.schedule_job') as mock_schedule_job:
            response = client.post("/schedules/", json=schedule_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_active"] is False
            
            # Неактивное расписание не должно добавляться в планировщик
            mock_schedule_job.assert_not_called()
    
    def test_get_schedules_pagination(self, client, db_session):
        """GET /schedules/ - тестирование пагинации"""
        # Создаем несколько расписаний
        for i in range(5):
            schedule = NewsletterSchedule(
                name=f"Рассылка {i+1}",
                schedule_type="cron",
                cron_expression="0 10 * * 1"
            )
            db_session.add(schedule)
        db_session.commit()
        
        # Тестируем пагинацию
        response = client.get("/schedules/?skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Рассылка 3"  # skip=2, значит 3-й элемент первый
