import pytest
from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key-that-is-long-enough-for-development"
    JWT_SECRET_KEY = "test-jwt-secret-key-that-is-long-enough-for-development"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["*"]
    SOCKETIO_MESSAGE_QUEUE = None


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove(); db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def signup(client, email="ada@example.com", username="ada"):
    response = client.post("/api/auth/signup", json={"email": email, "username": username, "password": "secure-password", "display_name": "Ada"})
    return response.get_json()
