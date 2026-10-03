# ---------- Stage 1: builder (installs dependencies, then gets thrown away) ----------

# slim = small Debian-based Python image, fewer packages to patch
FROM python:3.12-slim AS builder

# no .pyc files, and print logs straight away instead of buffering them
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# put the packages in a venv so the final image can copy just that one folder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# requirements first, code later: Docker caches this layer,
# so pip only reruns when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---------- Stage 2: runtime (the image we actually ship) ----------

FROM python:3.12-slim AS runtime

# DB_PATH is read by app/config.py, so the SQLite file ends up in /data
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DB_PATH=/data/tasks.db

# unprivileged user, no login shell, no home. Fixed numeric id because
# Kubernetes' runAsNonRoot check wants a number, not a name
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# the app user must be able to write the database here
RUN mkdir /data && chown app:app /data

WORKDIR /app

# only the installed packages come over from the builder
COPY --from=builder /opt/venv /opt/venv

# app code (.dockerignore keeps .venv, .git, *.db out)
COPY --chown=app:app wsgi.py .
COPY --chown=app:app app ./app

# nothing below runs as root, including the container itself
USER 10001:10001

VOLUME ["/data"]

# documentation only, the port is still published with -p
EXPOSE 8000

# the slim image has no curl, so use Python for the check.
# 3 failures in a row -> container shows as unhealthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

# gunicorn instead of the Flask dev server. 0.0.0.0 so it is reachable from outside the container.
# JSON form makes gunicorn PID 1, so it gets the stop signal from "docker stop"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "wsgi:app"]
