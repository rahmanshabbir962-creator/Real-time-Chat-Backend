from tests.conftest import signup


def auth(token): return {"Authorization": f"Bearer {token}"}


def test_create_join_and_list_public_room(client):
    owner = signup(client); token = owner["access_token"]
    created = client.post("/api/rooms", json={"name": "General", "description": "Everyone"}, headers=auth(token))
    assert created.status_code == 201
    other = signup(client, "grace@example.com", "grace")
    room_id = created.get_json()["room"]["id"]
    assert client.post(f"/api/rooms/{room_id}/join", headers=auth(other["access_token"])).status_code == 200
    listed = client.get("/api/rooms?scope=joined", headers=auth(other["access_token"])).get_json()
    assert listed["rooms"][0]["id"] == room_id

