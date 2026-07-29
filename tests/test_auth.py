from tests.conftest import signup


def test_signup_login_and_refresh(client):
    data = signup(client)
    assert data["user"]["email"] == "ada@example.com"
    login = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "secure-password"})
    assert login.status_code == 200
    refresh = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {login.get_json()['refresh_token']}"})
    assert refresh.status_code == 200
    assert refresh.get_json()["access_token"]


def test_login_rejects_bad_password(client):
    signup(client)
    response = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong"})
    assert response.status_code == 401

