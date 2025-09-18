import pytest
from fastapi import status
from app.models import User, user_categories
from sqlalchemy import select

class TestSubscribeAPI:
    def test_subscribe_new_user(self, client, db_session):
        data = {
            "email": "newuser@example.com",
            "categories": ["tech", "music"],
            "cities": ["Москва"],
            "subscription_types": ["daily"]
        }
        response = client.post("/api/subscribe/", json=data)
        assert response.status_code == status.HTTP_200_OK
        assert "User created and subscribed successfully" in response.json()["message"]

    def test_subscribe_existing_user(self, client, db_session):
        user = User(email="existing@example.com")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        data = {
            "email": "existing@example.com",
            "categories": ["new_cat1", "new_cat2"],
            "cities": ["Санкт-Петербург"],
            "subscription_types": ["weekly"]
        }
        response = client.post("/api/subscribe/", json=data)
        assert response.status_code == status.HTTP_200_OK
        assert "User categories updated successfully" in response.json()["message"]

class TestUnsubscribeAPI:
    def test_unsubscribe_success(self, client, db_session):
        user = User(email="unsubscribe@example.com", is_subscribed=True)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        response = client.get(f"/api/unsubscribe/{user.id}")
        assert response.status_code == status.HTTP_200_OK

        db_session.refresh(user)
        assert not user.is_subscribed

    def test_unsubscribe_not_found(self, client):
        response = client.get("/api/unsubscribe/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unsubscribe_invalid_id(self, client):
        response = client.get("/api/unsubscribe/notanid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_unsubscribe_by_email_success(self, client, db_session):
        """POST /api/unsubscribe/ - успешная отписка по email"""
        user = User(email="unsubscribe@example.com", is_subscribed=True)
        db_session.add(user)
        db_session.commit()

        data = {"email": "unsubscribe@example.com"}
        response = client.post("/api/unsubscribe/", json=data)

        assert response.status_code == status.HTTP_200_OK
        assert "Successfully unsubscribed" in response.json()["message"]

        # Проверяем что пользователь отписан
        db_session.refresh(user)
        assert not user.is_subscribed

    def test_unsubscribe_by_email_not_found(self, client):
        """POST /api/unsubscribe/ - email не найден"""
        data = {"email": "notfound@example.com"}
        response = client.post("/api/unsubscribe/", json=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unsubscribe_invalid_email_format(self, client):
        """POST /api/unsubscribe/ - невалидный формат email"""
        data = {"email": "invalid-email"}
        response = client.post("/api/unsubscribe/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

