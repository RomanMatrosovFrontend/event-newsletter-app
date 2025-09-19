import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from app.models import NewsletterSchedule
from datetime import datetime, timedelta
from app.routes import schedules
from app.main import app

class TestSchedulesAPI:
    """Полное тестирование всех эндпоинтов /schedules"""
    
    @pytest.fixture(autouse=True)  # ← ДОБАВИТЬ
    def _skip_auth(self):
        """Переопределяем get_current_admin для всех методов класса"""
        app.dependency_overrides[schedules.get_current_admin] = lambda request=None: "admin"
        yield
        app.dependency_overrides.pop(schedules.get_current_admin, None)

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
            schedule_config={
                "periodicity": "weekly",
                "days": [1],
                "hour": 10,
                "minute": 0,
                "timezone": "UTC"
            }        
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
        future_date = datetime.now() + timedelta(days=1)
        schedule = NewsletterSchedule(
            name="Конкретная рассылка",
            schedule_config={
                "periodicity": "date",
                "datetime": future_date.isoformat(),
                "timezone": "UTC"
            }
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)
        
        response = client.get(f"/schedules/{schedule.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Конкретная рассылка"
        assert data["schedule_config"]["periodicity"] == "date"
        assert data["schedule_config"]["datetime"] == future_date.isoformat()
    
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
            "schedule_config": {
                "periodicity": "weekly",
                "days": [1],
                "hour": 10,
                "minute": 0,
                "timezone": "UTC"
            },
            "is_active": True,
            "admin_timezone": "UTC"
        }
        
        with patch('app.routes.schedules.schedule_job') as mock_schedule_job:
            response = client.post("/schedules/", json=schedule_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Еженедельная рассылка"
            assert data["is_active"] is True
            
            # Проверяем поля schedule_config
            cfg = data["schedule_config"]
            assert cfg["periodicity"] == "weekly"
            assert cfg["days"] == [1]
            assert cfg["hour"] == 10
            assert cfg["minute"] == 0
            assert cfg["timezone"] == "UTC"
            
            # Проверяем что задача была добавлена в планировщик
            mock_schedule_job.assert_called_once()
    
    def test_create_schedule_date_success(self, client):
        """POST /schedules/ - создание date расписания"""
        future_date = datetime.now() + timedelta(hours=2)
        schedule_data = {
            "name": "Разовая рассылка",
            "description": "Завтра в полдень",
            "schedule_config": {
                "periodicity": "date",
                "datetime": future_date.isoformat(),
                "timezone": "UTC"
            },
            "is_active": True,
            "admin_timezone": "UTC"
        }
        with patch('app.routes.schedules.schedule_job'):
            response = client.post("/schedules/", json=schedule_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Разовая рассылка"
            cfg = data["schedule_config"]
            assert cfg["periodicity"] == "date"
            assert cfg["datetime"] == future_date.isoformat()
            assert cfg["timezone"] == "UTC"

    def test_create_schedule_with_user_ids(self, client):
        """POST /schedules/ - с конкретными пользователями"""
        schedule_data = {
            "name": "Рассылка для избранных",
            "user_ids": [1, 2, 3],
            "schedule_config": {
                "periodicity": "cron",
                "hour": 12,
                "minute": 0,
                "timezone": "UTC"
            },
            "is_active": True,
            "admin_timezone": "UTC"
        }
        
        with patch('app.routes.schedules.schedule_job'):
            response = client.post("/schedules/", json=schedule_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_ids"] == [1, 2, 3]
            # Проверяем schedule_config
            cfg = data["schedule_config"]
            assert cfg["periodicity"] == "cron"
            assert cfg["hour"] == 12
            assert cfg["minute"] == 0
            assert cfg["timezone"] == "UTC"    

    # PUT /schedules/{id}
    def test_update_schedule_success(self, client, db_session):
        """PUT /schedules/{id} - успешное обновление"""
        schedule = NewsletterSchedule(
            name="Старое название",
            schedule_config={
                "periodicity": "cron",
                "hour": 10,
                "minute": 0,
                "timezone": "UTC"
            },
            is_active=True
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)
        
        update_data = {
            "name": "Новое название",
            "schedule_config": {
                "periodicity": "cron",
                "hour": 12,
                "minute": 0,
                "timezone": "UTC"
            },
            "is_active": False
        }
       
        with patch('app.routes.schedules.scheduler') as mock_scheduler:
            mock_scheduler.get_job.return_value = MagicMock()
            mock_scheduler.remove_job.return_value = None
            
            response = client.put(f"/schedules/{schedule.id}", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Новое название"
            assert data["is_active"] is False
            cfg = data["schedule_config"]
            assert cfg["periodicity"] == "cron"
            assert cfg["hour"] == 12
            assert cfg["minute"] == 0
            assert cfg["timezone"] == "UTC"
   
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
            schedule_config={
                "periodicity": "cron",
                "hour": 10,
                "minute": 0,
                "timezone": "UTC"
            }
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
            schedule_config={
                "periodicity": "cron",
                "hour": 10,
                "minute": 0,
                "timezone": "UTC"
            }
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
            "schedule_config": {
                "periodicity": "cron",
                "hour": 10,
                "minute": 0,
                "timezone": "UTC"
            },
            "is_active": False,
            "admin_timezone": "UTC"
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
                schedule_config={
                    "periodicity": "cron",
                    "hour": 10,
                    "minute": 0,
                    "timezone": "UTC"
                }
            )
            db_session.add(schedule)
        db_session.commit()
        
        # Тестируем пагинацию
        response = client.get("/schedules/?skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Рассылка 3"  # skip=2, значит 3-й элемент первый

