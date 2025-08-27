import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from app.models import User, Event, user_categories
from datetime import datetime

class TestUsersAPI:
    """Полное тестирование всех эндпоинтов /users"""
    
    # GET /users/
    def test_get_users_empty(self, client):
        """GET /users/ - пустой список"""
        response = client.get("/users/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_get_users_with_data(self, client, db_session):
        """GET /users/ - с данными"""
        user1 = User(email="alexey@example.com")
        user2 = User(email="maria@example.com")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Добавляем категории для первого пользователя
        stmt = user_categories.insert().values(
            user_id=user1.id,
            category="tech"
        )
        db_session.execute(stmt)
        db_session.commit()
        
        response = client.get("/users/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        
        # Проверяем поля пользователей
        emails = [user["email"] for user in data]
        assert "alexey@example.com" in emails
        assert "maria@example.com" in emails
    
    def test_get_users_pagination(self, client, db_session):
        """GET /users/ - тестирование пагинации"""
        # Создаем 5 пользователей
        for i in range(5):
            user = User(email=f"user{i+1}@example.com")
            db_session.add(user)
        db_session.commit()
        
        # Тестируем пагинацию
        response = client.get("/users/?skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
    
    # GET /users/{id}
    def test_get_user_by_id_success(self, client, db_session):
        """GET /users/{id} - успешное получение"""
        user = User(email="specific@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Добавляем категории
        for category in ["tech", "music"]:
            stmt = user_categories.insert().values(
                user_id=user.id,
                category=category
            )
            db_session.execute(stmt)
        db_session.commit()
        
        response = client.get(f"/users/{user.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "specific@example.com"
        assert "tech" in data["categories"]
        assert "music" in data["categories"]
        assert "created_at" in data
    
    def test_get_user_by_id_not_found(self, client):
        """GET /users/{id} - пользователь не найден"""
        response = client.get("/users/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # GET /users/email/{email}
    def test_get_user_by_email_success(self, client, db_session):
        """GET /users/email/{email} - успешное получение"""
        user = User(email="test@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        response = client.get("/users/email/test@example.com")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["categories"] == []  # пустые категории по умолчанию
    
    def test_get_user_by_email_not_found(self, client):
        """GET /users/email/{email} - пользователь не найден"""
        response = client.get("/users/email/notfound@example.com")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # POST /users/
    def test_create_user_success(self, client):
        """POST /users/ - успешное создание с категориями"""
        user_data = {
            "email": "new@example.com",
            "categories": ["tech", "music"]
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "tech" in data["categories"]
        assert "music" in data["categories"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_user_minimal(self, client):
        """POST /users/ - только email"""
        user_data = {
            "email": "minimal@example.com"
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "minimal@example.com"
        assert data["categories"] == []  # пустые категории
    
    def test_create_user_empty_categories(self, client):
        """POST /users/ - с пустым списком категорий"""
        user_data = {
            "email": "empty_cat@example.com",
            "categories": []
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "empty_cat@example.com"
        assert data["categories"] == []
    
    def test_create_user_duplicate_email(self, client, db_session):
        """POST /users/ - дублирование email"""
        # Создаем первого пользователя
        existing_user = User(email="duplicate@example.com")
        db_session.add(existing_user)
        db_session.commit()
        
        # Пытаемся создать с тем же email
        user_data = {
            "email": "duplicate@example.com",
            "categories": ["tech"]
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_create_user_validation_error(self, client):
        """POST /users/ - ошибка валидации"""
        user_data = {
            "email": "invalid-email"  # Невалидный email
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_user_missing_email(self, client):
        """POST /users/ - отсутствует обязательное поле email"""
        user_data = {
            "categories": ["tech"]
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # PUT /users/{id}
    def test_update_user_success(self, client, db_session):
        """PUT /users/{id} - успешное обновление email и категорий"""
        user = User(email="old@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Добавляем старые категории
        stmt = user_categories.insert().values(
            user_id=user.id,
            category="old_category"
        )
        db_session.execute(stmt)
        db_session.commit()
        
        update_data = {
            "email": "new@example.com",
            "categories": ["tech", "music"]
        }
        
        response = client.put(f"/users/{user.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "tech" in data["categories"]
        assert "music" in data["categories"]
        assert "old_category" not in data["categories"]
    
    def test_update_user_categories_only(self, client, db_session):
        """PUT /users/{id} - обновление только категорий"""
        user = User(email="categories@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        update_data = {
            "categories": ["sports", "culture"]
        }
        
        response = client.put(f"/users/{user.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "categories@example.com"  # не изменился
        assert "sports" in data["categories"]
        assert "culture" in data["categories"]
    
    def test_update_user_not_found(self, client):
        """PUT /users/{id} - пользователь не найден"""
        update_data = {"email": "new@example.com"}
        
        response = client.put("/users/999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_user_duplicate_email(self, client, db_session):
        """PUT /users/{id} - попытка установить занятый email"""
        user1 = User(email="user1@example.com")
        user2 = User(email="user2@example.com")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Пытаемся изменить email user1 на email user2
        update_data = {"email": "user2@example.com"}
        
        response = client.put(f"/users/{user1.id}", json=update_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    # DELETE /users/{id}
    def test_delete_user_success(self, client, db_session):
        """DELETE /users/{id} - успешное удаление"""
        user = User(email="deletable@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Добавляем категории
        stmt = user_categories.insert().values(
            user_id=user.id,
            category="test_category"
        )
        db_session.execute(stmt)
        db_session.commit()
        
        response = client.delete(f"/users/{user.id}")
        assert response.status_code == status.HTTP_200_OK
        assert "User deleted successfully" in response.json()["message"]
        
        # Проверяем, что пользователь действительно удален
        get_response = client.get(f"/users/{user.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_user_not_found(self, client):
        """DELETE /users/{id} - пользователь не найден"""
        response = client.delete("/users/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Дополнительные тесты
    def test_user_with_multiple_categories(self, client, db_session):
        """Тест пользователя с множественными категориями"""
        user_data = {
            "email": "multicategory@example.com",
            "categories": ["tech", "music", "sports", "culture"]
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["categories"]) == 4
        for category in ["tech", "music", "sports", "culture"]:
            assert category in data["categories"]
    
    def test_user_categories_order_independent(self, client, db_session):
        """Проверка что порядок категорий не важен"""
        # Создаем пользователя
        user_data = {
            "email": "order_test@example.com", 
            "categories": ["music", "tech", "sports"]
        }
        
        response = client.post("/users/", json=user_data)
        user_id = response.json()["id"]
        
        # Обновляем с другим порядком
        update_data = {
            "categories": ["tech", "sports", "music"]
        }
        
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Проверяем что все категории есть (порядок может быть любой)
        assert len(data["categories"]) == 3
        for category in ["tech", "sports", "music"]:
            assert category in data["categories"]
    
    def test_clear_all_user_categories(self, client, db_session):
        """Очистка всех категорий пользователя"""
        # Создаем пользователя с категориями
        user_data = {
            "email": "clear_test@example.com",
            "categories": ["tech", "music"]
        }
        
        response = client.post("/users/", json=user_data)
        user_id = response.json()["id"]
        
        # Очищаем категории
        update_data = {
            "categories": []
        }
        
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["categories"] == []
    
    def test_user_timestamps(self, client):
        """Проверка автоматических timestamp полей"""
        user_data = {
            "email": "timestamp@example.com",
            "categories": ["tech"]
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Проверяем наличие timestamp полей
        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] is not None
        
        # created_at и updated_at должны быть близкими при создании
        from datetime import datetime
        created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        assert created_at is not None
