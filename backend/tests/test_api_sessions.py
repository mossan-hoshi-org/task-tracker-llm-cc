import pytest
from fastapi.testclient import TestClient
from main import app, reset_session_service
from models import SessionStatus


class TestSessionsAPI:
    
    @pytest.fixture
    def client(self):
        reset_session_service()
        return TestClient(app)
    
    def test_start_session_success(self, client):
        response = client.post(
            "/sessions/start",
            json={"task_name": "新機能開発"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["task_name"] == "新機能開発"
        assert data["status"] == SessionStatus.ACTIVE
        assert "start_time" in data
        assert data["pause_time"] is None
        assert data["end_time"] is None
        assert data["total_duration"] == 0
        assert len(data["id"]) > 0
    
    def test_start_session_empty_task_name(self, client):
        response = client.post(
            "/sessions/start",
            json={"task_name": ""}
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("String should have at least 1 character" in str(error) for error in error_detail)
    
    def test_start_session_whitespace_only_task_name(self, client):
        response = client.post(
            "/sessions/start",
            json={"task_name": "   "}
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("Task name cannot be empty or whitespace only" in str(error) for error in error_detail)
    
    def test_start_session_missing_task_name(self, client):
        response = client.post(
            "/sessions/start",
            json={}
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("Field required" in str(error) for error in error_detail)
    
    def test_start_session_auto_stops_previous(self, client):
        first_response = client.post(
            "/sessions/start",
            json={"task_name": "最初のタスク"}
        )
        assert first_response.status_code == 201
        first_session_id = first_response.json()["id"]
        
        second_response = client.post(
            "/sessions/start", 
            json={"task_name": "2番目のタスク"}
        )
        assert second_response.status_code == 201
        
        active_response = client.get("/sessions/active")
        assert active_response.status_code == 200
        active_data = active_response.json()
        
        assert active_data is not None
        assert active_data["id"] != first_session_id
        assert active_data["task_name"] == "2番目のタスク"
        assert active_data["status"] == SessionStatus.ACTIVE
    
    def test_start_session_japanese_task_name(self, client):
        japanese_task = "機能要件の整理と設計書作成"
        response = client.post(
            "/sessions/start",
            json={"task_name": japanese_task}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == japanese_task
    
    def test_start_session_response_format(self, client):
        response = client.post(
            "/sessions/start",
            json={"task_name": "レスポンス形式テスト"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        required_fields = ["id", "task_name", "status", "start_time", "pause_time", "end_time", "total_duration"]
        for field in required_fields:
            assert field in data
        
        assert isinstance(data["id"], str)
        assert isinstance(data["task_name"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["start_time"], str)
        assert isinstance(data["total_duration"], int)
    
    def test_get_active_session_when_none(self, client):
        response = client.get("/sessions/active")
        assert response.status_code == 200
        assert response.json() is None
    
    def test_get_active_session_when_exists(self, client):
        start_response = client.post(
            "/sessions/start",
            json={"task_name": "アクティブセッションテスト"}
        )
        assert start_response.status_code == 201
        session_id = start_response.json()["id"]
        
        active_response = client.get("/sessions/active")
        assert active_response.status_code == 200
        active_data = active_response.json()
        
        assert active_data is not None
        assert active_data["id"] == session_id
        assert active_data["task_name"] == "アクティブセッションテスト"
        assert active_data["status"] == SessionStatus.ACTIVE
    
    def test_pause_session_success(self, client):
        start_response = client.post(
            "/sessions/start",
            json={"task_name": "一時停止テスト"}
        )
        assert start_response.status_code == 201
        session_id = start_response.json()["id"]
        
        pause_response = client.patch(f"/sessions/{session_id}/pause")
        assert pause_response.status_code == 200
        pause_data = pause_response.json()
        
        assert pause_data["id"] == session_id
        assert pause_data["status"] == SessionStatus.PAUSED
        assert pause_data["pause_time"] is not None
        assert pause_data["total_duration"] >= 0
    
    def test_resume_session_success(self, client):
        start_response = client.post(
            "/sessions/start",
            json={"task_name": "再開テスト"}
        )
        assert start_response.status_code == 201
        session_id = start_response.json()["id"]
        
        pause_response = client.patch(f"/sessions/{session_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == SessionStatus.PAUSED
        
        resume_response = client.patch(f"/sessions/{session_id}/pause")
        assert resume_response.status_code == 200
        resume_data = resume_response.json()
        
        assert resume_data["id"] == session_id
        assert resume_data["status"] == SessionStatus.ACTIVE
        assert resume_data["pause_time"] is None
    
    def test_pause_nonexistent_session(self, client):
        response = client.patch("/sessions/nonexistent-id/pause")
        assert response.status_code == 404
        error_detail = response.json()["detail"]
        assert "Session not found" in error_detail
    
    def test_pause_stopped_session(self, client):
        start_response = client.post(
            "/sessions/start",
            json={"task_name": "停止済みセッションテスト"}
        )
        assert start_response.status_code == 201
        session_id = start_response.json()["id"]
        
        client.post(f"/sessions/{session_id}/stop")
        
        pause_response = client.patch(f"/sessions/{session_id}/pause")
        assert pause_response.status_code == 400
        error_detail = pause_response.json()["detail"]
        assert "Cannot pause a stopped session" in error_detail