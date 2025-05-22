from fastapi.testclient import TestClient

from trendscout.core.config import settings

def test_health_check(client: TestClient) -> None:
    """
    Test the health check endpoint.
    It should return a 200 status code and a JSON response {"status": "ok"}.
    """
    response = client.get(f"{settings.API_V1_STR}/health/")
    assert response.status_code == 200
    content = response.json()
    assert content == {"status": "ok"}
