from __future__ import annotations


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
