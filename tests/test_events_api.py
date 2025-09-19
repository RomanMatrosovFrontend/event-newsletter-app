# tests/test_events_api.py
import pytest
from fastapi import status
from app.models import Event
from app.routes import events
from app.main import app


class TestEventsAPI:
    """Полное тестирование всех эндпоинтов /events"""

    @pytest.fixture(autouse=True)
    def _skip_auth(self):
        """Вручную переопределяем get_current_admin для всех методов класса"""
        app.dependency_overrides[events.get_current_admin] = lambda request=None: "admin"
        yield
        app.dependency_overrides.pop(events.get_current_admin, None)

    # GET /events/
    def test_get_events_empty(self, client):
        """GET /events/ - пустой список"""
        response = client.get("/events/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_events_with_data(self, client, db_session):
        """GET /events/ - с данными"""
        event1 = Event(
            title="Концерт рок-группы",
            category="music",
            description="Отличный концерт",
            dates=["2024-12-01", "2024-12-02"],
            languages=["RU"],
            city="Москва",
            url="https://example.com/concert"
        )
        event2 = Event(
            title="IT-конференция",
            category="tech",
            dates=["2024-12-15"],
            languages=["EN", "RU"],
            city="СПб",
            url="https://example.com/tech-conf"
        )
        db_session.add_all([event1, event2])
        db_session.commit()

        response = client.get("/events/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        titles = [event["title"] for event in data]
        assert "Концерт рок-группы" in titles
        assert "IT-конференция" in titles

    def test_get_events_pagination(self, client, db_session):
        """GET /events/ - тестирование пагинации"""
        for i in range(5):
            ev = Event(
                title=f"Событие {i+1}",
                category="test",
                dates=["2024-12-01"],
                languages=["RU"],
                url=f"https://example.com/event{i+1}"
            )
            db_session.add(ev)
        db_session.commit()

        response = client.get("/events/?skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_get_events_filter_by_category(self, client, db_session):
        """GET /events/ - фильтрация по категории"""
        music_event = Event(
            title="Концерт",
            category="music",
            dates=["2024-12-01"],
            languages=["RU"],
            url="https://example.com/music"
        )
        tech_event = Event(
            title="Хакатон",
            category="tech",
            dates=["2024-12-02"],
            languages=["EN"],
            url="https://example.com/tech"
        )
        db_session.add_all([music_event, tech_event])
        db_session.commit()

        response = client.get("/events/?category=music")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "music"

    def test_get_events_filter_by_city(self, client, db_session):
        """GET /events/ - фильтрация по городу"""
        moscow_event = Event(
            title="Событие в Москве",
            category="culture",
            city="Москва",
            dates=["2024-12-01"],
            languages=["RU"],
            url="https://example.com/moscow"
        )
        spb_event = Event(
            title="Событие в СПб",
            category="culture",
            city="СПб",
            dates=["2024-12-02"],
            languages=["RU"],
            url="https://example.com/spb"
        )
        db_session.add_all([moscow_event, spb_event])
        db_session.commit()

        response = client.get("/events/?city=Москва")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["city"] == "Москва"

    def test_get_event_by_id_success(self, client, db_session):
        """GET /events/{id} - успешное получение"""
        event = Event(
            title="Конкретное событие",
            category="specific",
            description="Детальное описание",
            text="Полный текст события",
            dates=["2024-12-20"],
            languages=["RU"],
            age_restriction="18+",
            city="Казань",
            url="https://example.com/specific"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.get(f"/events/{event.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Конкретное событие"
        assert data["description"] == "Детальное описание"
        assert data["text"] == "Полный текст события"
        assert data["age_restriction"] == "18+"
        assert data["city"] == "Казань"

    def test_get_event_by_id_not_found(self, client):
        """GET /events/{id} - событие не найдено"""
        response = client.get("/events/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_event_success(self, client):
        """POST /events/ - успешное создание"""
        event_data = {
            "title": "Новое событие",
            "category": "new",
            "description": "Описание нового события",
            "text": "Подробный текст",
            "dates": ["2024-12-25", "2024-12-26"],
            "languages": ["RU", "EN"],
            "age_restriction": "16+",
            "city": "Новосибирск",
            "url": "https://example.com/new-event"
        }
        response = client.post("/events/", json=event_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Новое событие"
        assert data["category"] == "new"
        assert data["dates"] == ["2024-12-25", "2024-12-26"]
        assert data["languages"] == ["RU", "EN"]
        assert data["age_restriction"] == "16+"
        assert data["city"] == "Новосибирск"

    def test_create_event_minimal(self, client):
        """POST /events/ - минимальные обязательные поля"""
        event_data = {
            "title": "Минимальное событие",
            "dates": ["2024-12-30"],
            "languages": ["RU"],
            "url": "https://example.com/minimal"
        }
        response = client.post("/events/", json=event_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Минимальное событие"
        assert data["category"] is None
        assert data["description"] is None
        assert data["city"] is None

    def test_create_event_validation_error(self, client):
        """POST /events/ - ошибка валидации"""
        event_data = {
            "dates": [],
            "languages": []
        }
        response = client.post("/events/", json=event_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_event_success(self, client, db_session):
        """PUT /events/{id} - успешное обновление"""
        event = Event(
            title="Старое название",
            category="old",
            dates=["2024-12-01"],
            languages=["RU"],
            city="Москва",
            url="https://example.com/old"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        update_data = {
            "title": "Новое название",
            "category": "updated",
            "city": "СПб",
            "description": "Обновленное описание"
        }
        response = client.put(f"/events/{event.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Новое название"
        assert data["category"] == "updated"
        assert data["city"] == "СПб"
        assert data["description"] == "Обновленное описание"
        assert data["url"] == "https://example.com/old"

    def test_update_event_not_found(self, client):
        """PUT /events/{id} - событие не найдено"""
        response = client.put("/events/999", json={"title": "Новое название"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_event_partial(self, client, db_session):
        """PUT /events/{id} - частичное обновление"""
        event = Event(
            title="Исходное событие",
            category="original",
            description="Исходное описание",
            dates=["2024-12-01"],
            languages=["RU"],
            url="https://example.com/original"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        response = client.put(f"/events/{event.id}", json={"title": "Обновленный title"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Обновленный title"
        assert data["category"] == "original"
        assert data["description"] == "Исходное описание"

    def test_delete_event_success(self, client, db_session):
        """DELETE /events/{id} - успешное удаление"""
        event = Event(
            title="Удаляемое событие", 
            category="deletable", 
            dates=["2024-12-01"], 
            languages=["RU"], 
            url="https://example.com/deletable"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.delete(f"/events/{event.id}")
        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"]

        get_response = client.get(f"/events/{event.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_event_not_found(self, client):
        """DELETE /events/{id} - событие не найдено"""
        response = client.delete("/events/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_events_ordering(self, client, db_session):
        """Проверка наличия созданных событий"""
        import time
        event1 = Event(
            title="Первое событие", 
            category="test", 
            dates=["2024-12-01"], 
            languages=["RU"], 
            url="https://example.com/first"
        )
        db_session.add(event1)
        db_session.commit()
        time.sleep(0.01)
        event2 = Event(
            title="Второе событие", 
            category="test", 
            dates=["2024-12-02"], 
            languages=["RU"], 
            url="https://example.com/second"
        )
        db_session.add(event2)
        db_session.commit()

        response = client.get("/events/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        titles = [e["title"] for e in data]
        assert "Второе событие" in titles
        assert "Первое событие" in titles
        assert len(data) == 2

    def test_events_complex_filtering(self, client, db_session):
        """Тестирование комплексной фильтрации"""
        events_data = [
            {"title": "Концерт в Москве", "category": "music", "city": "Москва"},
            {"title": "Театр в Москве", "category": "culture", "city": "Москва"},
            {"title": "Концерт в СПб", "category": "music", "city": "СПб"},
            {"title": "IT в СПб", "category": "tech", "city": "СПб"}
        ]

        # Добавляем события в БД
        for i, data in enumerate(events_data):
            ev = Event(
                title=data["title"],
                category=data["category"],
                city=data["city"],
                dates=["2024-12-01"],
                languages=["RU"],
                url=f"https://example.com/event{i}"
            )
            db_session.add(ev)
        db_session.commit()

        # Фильтрация по категории music и городу Москва
        response = client.get("/events/?category=music&city=Москва")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Концерт в Москве"

