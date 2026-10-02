"""Integration tests of the HTML pages (forms, redirects, filters, escaping)."""
from app import repository


def add_task(app, title, done=False):
    """Insert straight through the repository, to set up a state quickly."""
    with app.app_context():
        task = repository.create_task(title)
        if done:
            repository.toggle_task(task["id"])
        return task["id"]


def titles(app):
    with app.app_context():
        return [t["title"] for t in repository.list_tasks()]


def test_index_shows_empty_message_on_new_database(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Nothing here yet." in response.data


def test_add_creates_task_and_redirects_to_index(client, app):
    response = client.post("/add", data={"title": "buy milk"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert titles(app) == ["buy milk"]


def test_add_ignores_blank_title(client, app):
    client.post("/add", data={"title": "   "})

    assert titles(app) == []


def test_add_truncates_title_to_the_limit(client, app):
    limit = app.config["MAX_TITLE_LENGTH"]

    client.post("/add", data={"title": "x" * (limit + 50)})

    assert titles(app) == ["x" * limit]


def test_index_lists_newest_task_first(client, app):
    add_task(app, "task-one")
    add_task(app, "task-two")

    html = client.get("/").get_data(as_text=True)

    assert html.index("task-two") < html.index("task-one")


def test_toggle_marks_task_done(client, app):
    task_id = add_task(app, "t")

    response = client.post(f"/toggle/{task_id}")

    assert response.status_code == 302
    with app.app_context():
        assert repository.list_tasks()[0]["done"] == 1


def test_edit_renames_task(client, app):
    task_id = add_task(app, "old")

    client.post(f"/edit/{task_id}", data={"title": "new"})

    assert titles(app) == ["new"]


def test_edit_with_blank_title_keeps_old_title(client, app):
    task_id = add_task(app, "old")

    client.post(f"/edit/{task_id}", data={"title": "  "})

    assert titles(app) == ["old"]


def test_delete_removes_task(client, app):
    task_id = add_task(app, "bye")

    response = client.post(f"/delete/{task_id}")

    assert response.status_code == 302
    assert titles(app) == []


def test_actions_redirect_back_to_the_referring_page(client, app):
    """The filter tab you were on must be kept after an action."""
    task_id = add_task(app, "t")

    response = client.post(f"/toggle/{task_id}", headers={"Referer": "http://localhost/?filter=done"})

    assert response.headers["Location"] == "http://localhost/?filter=done"


def test_actions_are_post_only(client):
    assert client.get("/add").status_code == 405
    assert client.get("/toggle/1").status_code == 405
    assert client.get("/delete/1").status_code == 405


def test_filters_show_the_right_tasks(client, app):
    add_task(app, "todo-task")
    add_task(app, "finished-task", done=True)

    all_page = client.get("/?filter=all").get_data(as_text=True)
    active_page = client.get("/?filter=active").get_data(as_text=True)
    done_page = client.get("/?filter=done").get_data(as_text=True)

    assert "todo-task" in all_page and "finished-task" in all_page
    assert "todo-task" in active_page and "finished-task" not in active_page
    assert "finished-task" in done_page and "todo-task" not in done_page


def test_unknown_filter_falls_back_to_all(client, app):
    add_task(app, "todo-task")
    add_task(app, "finished-task", done=True)

    html = client.get("/?filter=whatever").get_data(as_text=True)

    assert "todo-task" in html and "finished-task" in html


def test_progress_text_reflects_counts(client, app):
    add_task(app, "a")
    add_task(app, "b", done=True)

    html = client.get("/").get_data(as_text=True)

    assert "1 of 2 tasks remaining" in html
    assert "50%" in html


def test_html_in_title_is_escaped_not_executed(client, app):
    """Security (XSS): Jinja must turn < and > into entities so no script can run."""
    add_task(app, "<script>alert(1)</script>")

    html = client.get("/").get_data(as_text=True)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_quotes_in_title_cannot_break_out_of_the_input_attribute(client, app):
    """Security (XSS): the title is also placed inside value="..." of the edit form."""
    add_task(app, '"><img src=x onerror=alert(1)>')

    html = client.get("/").get_data(as_text=True)

    assert "<img src=x" not in html
