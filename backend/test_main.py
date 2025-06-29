import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """テスト用のFastAPIクライアントを作成する"""
    return TestClient(app)


def test_read_root(client):
    """ルートエンドポイントが正常に動作することをテストする"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Task Tracker API"}


def test_health_check(client):
    """ヘルスチェックエンドポイントが正常に動作することをテストする"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_docs_endpoint(client):
    """Swagger UIエンドポイントが利用可能であることをテストする"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]