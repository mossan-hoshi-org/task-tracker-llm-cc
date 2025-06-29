import pytest
import os
from fastapi.testclient import TestClient
from main import app, reset_gemini_service


class TestSummaryAPI:
    
    @pytest.fixture
    def client(self, monkeypatch):
        # テスト環境ではAPIキーを無効にしてモック機能を使用
        monkeypatch.setenv("GEMINI_API_KEY", "")
        reset_gemini_service()
        return TestClient(app)
    
    def test_generate_summary_success(self, client):
        request_data = {
            "sessions": [
                {"task_name": "新機能開発", "duration_ms": 3600000},
                {"task_name": "テストコード作成", "duration_ms": 1800000},
                {"task_name": "チーム会議", "duration_ms": 900000}
            ]
        }
        
        response = client.post("/summary/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
        
        for category in data["categories"]:
            assert "category" in category
            assert "subcategory" in category
            assert "total_duration_ms" in category
            assert isinstance(category["total_duration_ms"], int)
            assert category["total_duration_ms"] > 0
    
    def test_generate_summary_empty_sessions(self, client):
        request_data = {"sessions": []}
        
        response = client.post("/summary/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 0
    
    def test_generate_summary_japanese_tasks(self, client):
        request_data = {
            "sessions": [
                {"task_name": "機能要件の整理と設計書作成", "duration_ms": 2700000},
                {"task_name": "バックエンドAPI実装", "duration_ms": 5400000},
                {"task_name": "フロントエンド画面作成", "duration_ms": 4500000},
                {"task_name": "単体テスト作成", "duration_ms": 1800000},
                {"task_name": "デバッグ作業", "duration_ms": 1200000}
            ]
        }
        
        response = client.post("/summary/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["categories"]) > 0
        
        total_duration = sum(cat["total_duration_ms"] for cat in data["categories"])
        expected_total = sum(session["duration_ms"] for session in request_data["sessions"])
        assert total_duration == expected_total
    
    def test_generate_summary_categorization_logic(self, client):
        request_data = {
            "sessions": [
                {"task_name": "コード実装", "duration_ms": 1000000},
                {"task_name": "ユニットテスト", "duration_ms": 500000},
                {"task_name": "ミーティング参加", "duration_ms": 600000},
                {"task_name": "技術調査", "duration_ms": 800000},
                {"task_name": "設計レビュー", "duration_ms": 400000},
                {"task_name": "ドキュメント更新", "duration_ms": 300000}
            ]
        }
        
        response = client.post("/summary/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        categories = data["categories"]
        
        category_names = [cat["category"] for cat in categories]
        assert "開発" in category_names
        assert any(cat for cat in categories if "会議" in cat["category"] or "ミーティング" in cat["category"])
    
    def test_generate_summary_invalid_request(self, client):
        response = client.post("/summary/generate", json={})
        assert response.status_code == 422
        
        error_detail = response.json()["detail"]
        assert any("Field required" in str(error) for error in error_detail)
    
    def test_generate_summary_invalid_task_item(self, client):
        request_data = {
            "sessions": [
                {"task_name": "有効なタスク", "duration_ms": 1000},
                {"duration_ms": 2000}
            ]
        }
        
        response = client.post("/summary/generate", json=request_data)
        assert response.status_code == 422
        
        error_detail = response.json()["detail"]
        assert any("Field required" in str(error) for error in error_detail)
    
    def test_generate_summary_response_format(self, client):
        request_data = {
            "sessions": [
                {"task_name": "レスポンス形式テスト", "duration_ms": 1500000}
            ]
        }
        
        response = client.post("/summary/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "categories" in data
        assert isinstance(data["categories"], list)
        
        if len(data["categories"]) > 0:
            category = data["categories"][0]
            required_fields = ["category", "subcategory", "total_duration_ms"]
            for field in required_fields:
                assert field in category
            
            assert isinstance(category["category"], str)
            assert isinstance(category["subcategory"], str)
            assert isinstance(category["total_duration_ms"], int)