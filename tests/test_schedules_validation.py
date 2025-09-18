# tests/test_schedules_validation.py

import pytest
from fastapi import status

class TestScheduleConfigValidation:
    """Validation tests for schedule_config in /schedules endpoints."""

    @pytest.mark.parametrize("payload,missing_field", [
        (
            {
                "name": "Weekly missing days",
                "description": "Missing days for weekly",
                "schedule_config": {
                    "periodicity": "weekly",
                    "hour": 9,
                    "minute": 0,
                    "timezone": "UTC"
                },
                "is_active": True,
                "admin_timezone": "UTC"
            },
            "days"
        ),
        (
            {
                "name": "Date missing datetime",
                "description": "Missing datetime for date",
                "schedule_config": {
                    "periodicity": "date",
                    "timezone": "UTC"
                },
                "is_active": True,
                "admin_timezone": "UTC"
            },
            "datetime"
        ),
        (
            {
                "name": "Conflicting params",
                "description": "days_interval with days",
                "schedule_config": {
                    "periodicity": "interval",
                    "days_interval": 3,
                    "days": [1, 2],
                    "timezone": "UTC"
                },
                "is_active": True,
                "admin_timezone": "UTC"
            },
            "days"
        ),
    ])
    def test_create_schedule_invalid_config(self, client, payload, missing_field):
        response = client.post("/schedules/", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.json()
        assert "detail" in body
        # Error message should mention the problematic field
        assert missing_field.lower() in body["detail"].lower()

