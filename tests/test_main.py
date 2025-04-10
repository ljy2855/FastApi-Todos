import pytest
from fastapi.testclient import TestClient
import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from main import app



@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# 매 테스트마다 데이터 초기화
@pytest.fixture(autouse=True)
def reset_data(client):
    # 테스트 전 모든 todo 제거
    response = client.get("/todos")
    todos = response.json()
    for todo in todos:
        client.delete(f"/todos/{todo['id']}")
    yield
    # 테스트 후도 마찬가지로 정리
    response = client.get("/todos")
    for todo in response.json():
        client.delete(f"/todos/{todo['id']}")


def test_get_todos_empty(client):
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_create_todo(client):
    todo = {"title": "Test", "description": "Test description", "completed": False}
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["title"] == "Test"
    assert json_data["description"] == "Test description"
    assert json_data["completed"] is False
    assert "id" in json_data


def test_create_todo_invalid(client):
    todo = {"title": "Only title"}  # 필수 필드 누락
    response = client.post("/todos", json=todo)
    assert response.status_code == 422


def test_get_todos_with_items(client):
    todo = {"title": "Task", "description": "Some task", "completed": False}
    client.post("/todos", json=todo)
    response = client.get("/todos")
    assert response.status_code == 200
    todos = response.json()
    assert len(todos) == 1
    assert todos[0]["title"] == "Task"


def test_update_todo(client):
    todo = {"title": "Task", "description": "Old", "completed": False}
    create_response = client.post("/todos", json=todo)
    item_id = create_response.json()["id"]

    updated = {"title": "Updated", "description": "New desc", "completed": True}
    response = client.put(f"/todos/{item_id}", json=updated)
    assert response.status_code == 200
    assert response.json()["success"] is True

    get_response = client.get("/todos")
    updated_item = get_response.json()[0]
    assert updated_item["title"] == "Updated"


def test_update_todo_not_found(client):
    updated = {"title": "Updated", "description": "New desc", "completed": True}
    response = client.put("/todos/9999", json=updated)
    assert response.status_code == 200
    assert response.json()["success"] is False


def test_delete_todo(client):
    todo = {"title": "Delete me", "description": "To delete", "completed": False}
    create_response = client.post("/todos", json=todo)
    item_id = create_response.json()["id"]

    delete_response = client.delete(f"/todos/{item_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

    get_response = client.get("/todos")
    assert all(t["id"] != item_id for t in get_response.json())


def test_delete_todo_not_found(client):
    response = client.delete("/todos/9999")
    assert response.status_code == 200
    assert response.json()["success"] is False