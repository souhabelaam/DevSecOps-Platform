"""Smoke test: is the app alive? Docker and Kubernetes probes rely on this route."""


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
