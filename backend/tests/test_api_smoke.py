from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"
    assert body["service"] == "cloudcampus-backend"


def test_openapi_contains_critical_routes():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    expected_paths = {
        "/api/auth/login",
        "/api/auth/me",
        "/api/aws/sync",
        "/api/resources/",
        "/api/optimization/scan",
        "/api/optimization/recommendations",
        "/api/ml/dataset/collect",
        "/api/ml/dataset/summary",
        "/api/ml/anomalies/detect",
        "/api/ml/anomalies",
        "/api/ml/cost-data/collect",
        "/api/ml/cost-forecast",
        "/api/dashboard/overview",
    }

    missing_paths = expected_paths - set(paths)

    assert not missing_paths, (
        f"Missing API routes: {missing_paths}"
    )


def test_protected_endpoint_requires_token():
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_dashboard_requires_token():
    response = client.get(
        "/api/dashboard/overview"
    )

    assert response.status_code == 401


def test_frontend_cors_preflight():
    response = client.options(
        "/api/dashboard/overview",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": (
                "authorization,content-type"
            ),
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:5173"
    )