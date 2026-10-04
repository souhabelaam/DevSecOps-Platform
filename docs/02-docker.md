# Phase 2: Docker

The app is packaged as a small, locked-down container image. Every later phase (scanning,
Kubernetes, AWS) runs this same image.

## The Dockerfile in short

Two stages:

1. **builder** installs the Python packages into a virtual environment.
2. **runtime** copies only that environment and the app code. Compilers, pip caches and
   build leftovers stay behind, so the shipped image is smaller and has less to attack.

| Choice | Why |
|---|---|
| `python:3.12-slim` | Small Debian-based base, fewer packages to patch |
| Non-root user, fixed id `10001`, no login shell, no home | A hacked app does not get root. A numeric id lets Kubernetes' `runAsNonRoot` check verify it. `USER 10001:10001` is also what Hadolint asks for (DL3066) |
| `gunicorn` instead of the Flask dev server | The dev server is not meant for real traffic. In JSON form it runs as PID 1 and receives `docker stop` correctly |
| `DB_PATH=/data/tasks.db` and `VOLUME /data` | The database lives outside the image, in a volume, so data survives container replacement |
| `HEALTHCHECK` with Python's `urllib` | The slim image has no `curl`. Exec form (DL3025). Docker shows `(healthy)` or `(unhealthy)` |
| Packages pinned in `requirements.txt` | Same build gives the same result (`Flask==3.1.0`, `gunicorn==23.0.0`) |
| `requirements.txt` copied before the code | Docker caches that layer, so pip reruns only when dependencies change |

## `.dockerignore`

Keeps these out of the build context: `.git`, virtual environments, caches, `*.db`, `.env`,
keys and certificates, and also the deployment files (`k8s/`, `terraform/`, the CI files).
Result: faster builds, a smaller image, and no way to bake a secret into a layer.

## Verified locally

| Check | Result |
|---|---|
| Runs as non-root | `uid=10001` |
| Health | `docker ps` shows `(healthy)`, `/health` returns 200 |
| Data survives | Tasks are still there after the container is removed and recreated on the volume `tt-data` |

```
docker build -t task-tracker:1.0 .
docker run -d --name tt -p 8000:8000 -v tt-data:/data task-tracker:1.0
```

## One fix that came from the pipeline

The first CI run failed in Hadolint on two rules: the healthcheck was in shell form
(DL3025) and the `USER` was a name instead of a number (DL3066). Both were fixed in the
Dockerfile, which is the point of linting it automatically (doc 04).

## Hardening added later, outside the image

The same image gets extra restrictions where it runs: read-only filesystem, dropped Linux
capabilities, no privilege escalation and memory limits, in Kubernetes (doc 05) and in the
AWS boot script (doc 09).
