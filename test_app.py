import pytest
from pydantic import ValidationError

from app.schemas import UserInput


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "demo"


def test_validation_ok():
    payload = UserInput(
        username="  Priya   S ",
        user_id="p001",
        age=18,
        weight=55,
        goal="general wellness",
        intensity="medium",
    )
    assert payload.user_id == "p001"
    assert payload.username == "Priya S"


def test_validation_rejects_bad_input():
    with pytest.raises(ValidationError):
        UserInput(
            username="P",
            user_id="bad id!",
            age=5,
            weight=10,
            goal="flying",
            intensity="extreme",
        )


def test_workout_demo_without_key(client):
    data = {
        "username": "Test User",
        "user_id": "test001",
        "age": 18,
        "weight": 55,
        "goal": "general wellness",
        "intensity": "medium",
    }
    response = client.post("/api/workout", json=data)
    assert response.status_code == 200

    body = response.json()
    assert len(body["workout_plan"]["days"]) == 7
    assert body["nutrition_tip"]["tip"]


def test_feedback_demo(client):
    data = {
        "username": "Test User 2",
        "user_id": "test002",
        "age": 18,
        "weight": 55,
        "goal": "weight loss",
        "intensity": "low",
    }
    assert client.post("/api/workout", json=data).status_code == 200

    response = client.post(
        "/api/feedback",
        json={"user_id": "test002", "feedback": "Add more cardio and one rest day"},
    )
    assert response.status_code == 200

    updated = response.json()["updated_plan"]
    assert len(updated["days"]) == 7
    assert updated["days"][1]["focus"] == "Cardio emphasis"


def test_feedback_unknown_user(client):
    response = client.post(
        "/api/feedback",
        json={"user_id": "nobody123", "feedback": "More cardio please"},
    )
    assert response.status_code == 404


def test_html_flow(client):
    home = client.get("/")
    assert home.status_code == 200
    assert "Generate my 7-day plan" in home.text

    result = client.post(
        "/generate-workout",
        data={
            "username": "Html User",
            "user_id": "html001",
            "age": "25",
            "weight": "70",
            "goal": "endurance",
            "intensity": "high",
        },
    )
    assert result.status_code == 200
    assert "Html User" in result.text
    assert "Day 7" in result.text

    feedback = client.post(
        "/submit-feedback",
        data={"user_id": "html001", "feedback": "Add more cardio"},
    )
    assert feedback.status_code == 200
    assert "Updated plan" in feedback.text


def test_html_form_error_is_friendly(client):
    result = client.post(
        "/generate-workout",
        data={
            "username": "X",
            "user_id": "ok_id",
            "age": "25",
            "weight": "70",
            "goal": "endurance",
            "intensity": "high",
        },
    )
    assert result.status_code == 400
    assert "Please check your details" in result.text
    # The form keeps what the user typed.
    assert 'value="ok_id"' in result.text


def test_dashboard_and_delete(client):
    client.post(
        "/api/workout",
        json={
            "username": "Delete Me",
            "user_id": "del001",
            "age": 30,
            "weight": 80,
            "goal": "flexibility",
            "intensity": "low",
        },
    )

    dashboard = client.get("/view-all-users")
    assert dashboard.status_code == 200
    assert "del001" in dashboard.text

    delete = client.post("/admin/delete/del001", data={"admin_key": ""})
    assert delete.status_code == 200  # followed the redirect back to the dashboard
    assert "del001" not in delete.text

    users = client.get("/api/users").json()
    assert all(u["user_id"] != "del001" for u in users)
