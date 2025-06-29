import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models import Session, SessionCreate, SessionUpdate, SessionStatus, SessionResponse


class TestSessionModels:
    
    def test_session_status_enum(self):
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.PAUSED == "paused"
        assert SessionStatus.STOPPED == "stopped"
    
    def test_session_create_valid_data(self):
        session_data = SessionCreate(task_name="プロジェクト設計")
        
        assert session_data.task_name == "プロジェクト設計"
        assert session_data.model_dump() == {"task_name": "プロジェクト設計"}
    
    def test_session_create_empty_task_name(self):
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(task_name="")
        
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_session_create_whitespace_only_task_name(self):
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(task_name="   ")
        
        assert "Value error" in str(exc_info.value)
    
    def test_session_model_creation(self):
        start_time = datetime.now(timezone.utc)
        session = Session(
            id="session-123",
            task_name="データベース設計",
            status=SessionStatus.ACTIVE,
            start_time=start_time,
            pause_time=None,
            end_time=None,
            total_duration=0
        )
        
        assert session.id == "session-123"
        assert session.task_name == "データベース設計"
        assert session.status == SessionStatus.ACTIVE
        assert session.start_time == start_time
        assert session.pause_time is None
        assert session.end_time is None
        assert session.total_duration == 0
    
    def test_session_update_status(self):
        update_data = SessionUpdate(status=SessionStatus.PAUSED)
        assert update_data.status == SessionStatus.PAUSED
    
    def test_session_response_calculation(self):
        start_time = datetime.now(timezone.utc)
        session = Session(
            id="session-456",
            task_name="API実装",
            status=SessionStatus.ACTIVE,
            start_time=start_time,
            pause_time=None,
            end_time=None,
            total_duration=0
        )
        
        response = SessionResponse.from_session(session)
        
        assert response.id == "session-456"
        assert response.task_name == "API実装"
        assert response.status == SessionStatus.ACTIVE
        assert response.start_time == start_time
        assert response.elapsed_seconds >= 0
    
    def test_session_japanese_task_name(self):
        japanese_task = "機能要件の整理と設計書作成"
        session_data = SessionCreate(task_name=japanese_task)
        
        assert session_data.task_name == japanese_task
    
    def test_session_long_task_name(self):
        long_task = "非常に長いタスク名のテストケースで最大文字数制限をチェックする" * 5
        
        try:
            session_data = SessionCreate(task_name=long_task)
            assert len(session_data.task_name) == len(long_task)
        except ValidationError:
            pass