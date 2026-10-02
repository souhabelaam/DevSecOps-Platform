"""HTML pages."""
from flask import Blueprint, current_app, redirect, render_template, request, url_for

from .. import repository

bp = Blueprint("web", __name__)

FILTERS = ("all", "active", "done")


@bp.get("/")
def index():
    current = request.args.get("filter", "all")
    if current not in FILTERS:
        current = "all"

    tasks = repository.list_tasks(newest_first=True)
    counts = {
        "all": len(tasks),
        "active": sum(1 for t in tasks if not t["done"]),
        "done": sum(1 for t in tasks if t["done"]),
    }
    if current == "active":
        tasks = [t for t in tasks if not t["done"]]
    elif current == "done":
        tasks = [t for t in tasks if t["done"]]

    return render_template("index.html", tasks=tasks, counts=counts, current=current)


@bp.post("/add")
def add():
    title = request.form.get("title", "").strip()
    if title:
        repository.create_task(title[: current_app.config["MAX_TITLE_LENGTH"]])
    return redirect(url_for("web.index"))


@bp.post("/edit/<int:task_id>")
def edit(task_id):
    title = request.form.get("title", "").strip()
    if title:
        repository.update_task(task_id, title[: current_app.config["MAX_TITLE_LENGTH"]])
    return redirect(request.referrer or url_for("web.index"))


@bp.post("/toggle/<int:task_id>")
def toggle(task_id):
    repository.toggle_task(task_id)
    return redirect(request.referrer or url_for("web.index"))


@bp.post("/delete/<int:task_id>")
def delete(task_id):
    repository.delete_task(task_id)
    return redirect(request.referrer or url_for("web.index"))
