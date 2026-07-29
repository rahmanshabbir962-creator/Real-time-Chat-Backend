from tests.conftest import signup


def auth(token): return {"Authorization": f"Bearer {token}"}


def test_message_lifecycle(client):
    user = signup(client); token = user["access_token"]
    room = client.post("/api/rooms", json={"name": "General"}, headers=auth(token)).get_json()["room"]
    new = client.post(f"/api/messages/rooms/{room['id']}", json={"content": "Hello"}, headers=auth(token))
    assert new.status_code == 201
    message_id = new.get_json()["message"]["id"]
    assert client.patch(f"/api/messages/{message_id}", json={"content": "Hello world"}, headers=auth(token)).status_code == 200
    history = client.get(f"/api/messages/rooms/{room['id']}", headers=auth(token)).get_json()
    assert history["messages"][0]["content"] == "Hello world"
    assert client.delete(f"/api/messages/{message_id}", headers=auth(token)).status_code == 204
