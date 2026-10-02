"""JSON API."""
from flask import Blueprint, current_app, jsonify, request

from .. import repository

bp = Blueprint("api", __name__, url_prefix="/api")


def _read_title():
    """Return (title, error_response). Shared by create and update."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):  # missing, invalid, or valid JSON that is not an object
        data = {}
    title = str(data.get("title", "")).strip()
    if not title:
        return None, (jsonify(error="title is required"), 400)
    if len(title) > current_app.config["MAX_TITLE_LENGTH"]:
        return None, (jsonify(error="title too long"), 400)
    return title, None


@bp.get("/tasks")
def list_tasks():
    return jsonify(repository.list_tasks())


@bp.post("/tasks")
def create_task():
    title, error = _read_title()
    if error:
        return error
    return jsonify(repository.create_task(title)), 201


@bp.put("/tasks/<int:task_id>")
def update_task(task_id):
    title, error = _read_title()
    if error:
        return error
    if not repository.update_task(task_id, title):
        return jsonify(error="task not found"), 404
    return jsonify(id=task_id, title=title)
