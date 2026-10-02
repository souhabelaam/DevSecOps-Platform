"""Entry point. `python wsgi.py` for development, `gunicorn wsgi:app` in production."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
