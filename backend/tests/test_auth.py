from __future__ import annotations

from app.extensions import db
from app.models import User
from app.security.passwords import hash_password


def test_signup_creates_user(client):
    response = client.post(
        "/api/v1/signup",
        json={"email": "user@example.com", "password": "Password123!", "full_name": "Test User"},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert "access_token" in payload["data"]


def test_login_returns_tokens(client, app):
    with app.app_context():
        db.session.add(
            User(
                email="existing@example.com",
                password_hash=hash_password("Password123!"),
                full_name="Existing User",
            )
        )
        db.session.commit()

    response = client.post(
        "/api/v1/login",
        json={"email": "existing@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "refresh_token" in payload["data"]
