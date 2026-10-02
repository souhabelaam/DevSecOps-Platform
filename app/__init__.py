"""Application factory: builds and wires the Flask app."""
from flask import Flask

from . import db
from .config import Config
from .routes import all_blueprints


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)  # lets tests override settings

    db.init_app(app)
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)
    return app
