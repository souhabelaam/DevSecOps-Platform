"""Integration tests of the JSON API: request -> route -> repository -> SQLite."""
import pytest


def test_list_is_empty_at_start(client):
    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_returns_201_and_the_task(client):
    response = client.post("/api/tasks", json={"title": "buy milk"})

    assert response.status_code == 201
    assert response.get_json() == {"id": 1, "title": "buy milk", "done": 0}


def test_created_task_appears_in_the_list(client):
    client.post("/api/tasks", json={"title": "buy milk"})

    titles = [t["title"] for t in client.get("/api/tasks").get_json()]

    assert titles == ["buy milk"]


def test_create_strips_surrounding_spaces(client):
    response = client.post("/api/tasks", json={"title": "  spaced  "})

    assert response.get_json()["title"] == "spaced"


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"title": "   "}])
def test_create_rejects_missing_or_blank_title(client, payload):
    response = client.post("/api/tasks", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "title is required"}


def test_create_rejects_title_longer_than_the_limit(client, app):
    too_long = "x" * (app.config["MAX_TITLE_LENGTH"] + 1)

    response = client.post("/api/tasks", json={"title": too_long})

    assert response.status_code == 400
    assert response.get_json() == {"error": "title too long"}


def test_create_accepts_title_exactly_at_the_limit(client, app):
    at_limit = "x" * app.config["MAX_TITLE_LENGTH"]

    response = client.post("/api/tasks", json={"title": at_limit})

    assert response.status_code == 201


def test_create_with_invalid_json_body_is_a_400_not_a_crash(client):
    response = client.post("/api/tasks", data="not json", content_type="application/json")

    assert response.status_code == 400


@pytest.mark.parametrize("body", [[1, 2, 3], "text", 42, None])
def test_create_with_non_object_json_is_a_400_not_a_crash(client, body):
    """Valid JSON, but not an object: the route must answer 400, never 500."""
    response = client.post("/api/tasks", json=body)

    assert response.status_code == 400


def test_update_renames_the_task(client):
    task_id = client.post("/api/tasks", json={"title": "old"}).get_json()["id"]

    response = client.put(f"/api/tasks/{task_id}", json={"title": "new"})

    assert response.status_code == 200
    assert response.get_json() == {"id": task_id, "title": "new"}
    assert client.get("/api/tasks").get_json()[0]["title"] == "new"


def test_update_missing_task_returns_404(client):
    response = client.put("/api/tasks/999", json={"title": "new"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "task not found"}


def test_update_rejects_blank_title(client):
    task_id = client.post("/api/tasks", json={"title": "old"}).get_json()["id"]

    response = client.put(f"/api/tasks/{task_id}", json={"title": " "})

    assert response.status_code == 400


def test_non_integer_id_is_not_routed(client):
    assert client.put("/api/tasks/abc", json={"title": "x"}).status_code == 404


def test_unsupported_method_is_refused(client):
    assert client.delete("/api/tasks").status_code == 405


def test_sql_injection_title_is_stored_literally(client):
    """Security: hostile text goes in and comes out unchanged, and the table survives."""
    evil = "x'); DROP TABLE tasks;--"

    client.post("/api/tasks", json={"title": evil})

    assert [t["title"] for t in client.get("/api/tasks").get_json()] == [evil]


def test_html_in_title_is_returned_as_json_data_not_interpreted(client):
    payload = "<script>alert(1)</script>"

    client.post("/api/tasks", json={"title": payload})

    response = client.get("/api/tasks")
    assert response.mimetype == "application/json"  # browsers do not render JSON as HTML
    assert response.get_json()[0]["title"] == payload
