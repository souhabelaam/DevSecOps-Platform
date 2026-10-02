"""Tests of the data layer, calling the SQL functions directly (no HTTP).

The repository uses flask.g, so every test needs an application context.
"""
import pytest

from app import repository


@pytest.fixture
def ctx(app):
    with app.app_context():
        yield


def test_list_is_empty_on_new_database(ctx):
    assert repository.list_tasks() == []


def test_create_task_returns_the_new_task(ctx):
    task = repository.create_task("buy milk")

    assert task == {"id": 1, "title": "buy milk", "done": 0}


def test_created_task_is_listed(ctx):
    repository.create_task("buy milk")

    assert [t["title"] for t in repository.list_tasks()] == ["buy milk"]


def test_list_order_oldest_first_by_default_and_newest_first_on_request(ctx):
    repository.create_task("first")
    repository.create_task("second")

    assert [t["title"] for t in repository.list_tasks()] == ["first", "second"]
    assert [t["title"] for t in repository.list_tasks(newest_first=True)] == ["second", "first"]


def test_update_task_changes_the_title(ctx):
    task = repository.create_task("old")

    assert repository.update_task(task["id"], "new") is True
    assert repository.list_tasks()[0]["title"] == "new"


def test_update_missing_task_returns_false(ctx):
    assert repository.update_task(999, "x") is False


def test_toggle_flips_done_back_and_forth(ctx):
    task = repository.create_task("t")

    repository.toggle_task(task["id"])
    assert repository.list_tasks()[0]["done"] == 1

    repository.toggle_task(task["id"])
    assert repository.list_tasks()[0]["done"] == 0


def test_delete_removes_only_that_task(ctx):
    keep = repository.create_task("keep")
    drop = repository.create_task("drop")

    repository.delete_task(drop["id"])

    assert [t["id"] for t in repository.list_tasks()] == [keep["id"]]


def test_delete_missing_task_does_not_fail(ctx):
    repository.delete_task(999)  # must not raise

    assert repository.list_tasks() == []


def test_sql_injection_in_title_is_stored_as_plain_text(ctx):
    """Security: parameterized queries mean the text never becomes SQL."""
    evil = "x'); DROP TABLE tasks;--"

    repository.create_task(evil)

    tasks = repository.list_tasks()  # would raise if the table had been dropped
    assert [t["title"] for t in tasks] == [evil]


def test_sql_injection_in_id_position_is_not_executed(ctx):
    """Security: the id is bound as a parameter too, not formatted into the query."""
    repository.create_task("a")
    repository.create_task("b")

    repository.delete_task("1 OR 1=1")  # a string, so it matches no integer id

    assert len(repository.list_tasks()) == 2
