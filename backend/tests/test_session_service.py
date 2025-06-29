import pytest
from session_service import SessionService
from models import SessionCreate, SessionStatus, SessionUpdate


class TestSessionService:
    
    @pytest.fixture
    def service(self):
        return SessionService()
    
    def test_start_new_session(self, service):
        session_data = SessionCreate(task_name="新機能開発")
        
        session = service.start_session(session_data)
        
        assert session.task_name == "新機能開発"
        assert session.status == SessionStatus.ACTIVE
        assert session.pause_time is None
        assert session.end_time is None
        assert session.total_duration == 0
        assert len(session.id) > 0
    
    def test_start_session_auto_stops_previous(self, service):
        first_session_data = SessionCreate(task_name="設計書作成")
        first_session = service.start_session(first_session_data)
        
        import time
        time.sleep(0.01)
        
        second_session_data = SessionCreate(task_name="コード実装")
        second_session = service.start_session(second_session_data)
        
        stored_first = service.get_session(first_session.id)
        assert stored_first.status == SessionStatus.STOPPED
        assert stored_first.end_time is not None
        assert stored_first.total_duration > 0
        
        assert second_session.status == SessionStatus.ACTIVE
        assert service.get_active_session() == second_session
    
    def test_pause_active_session(self, service):
        session_data = SessionCreate(task_name="テスト作成")
        session = service.start_session(session_data)
        
        import time
        time.sleep(0.01)
        
        update_data = SessionUpdate(status=SessionStatus.PAUSED)
        paused_session = service.update_session(session.id, update_data)
        
        assert paused_session.status == SessionStatus.PAUSED
        assert paused_session.pause_time is not None
        assert paused_session.total_duration > 0
        assert service.get_active_session() is None
    
    def test_resume_paused_session(self, service):
        session_data = SessionCreate(task_name="レビュー")
        session = service.start_session(session_data)
        
        import time
        time.sleep(0.01)
        
        pause_update = SessionUpdate(status=SessionStatus.PAUSED)
        service.update_session(session.id, pause_update)
        
        time.sleep(0.01)
        
        resume_update = SessionUpdate(status=SessionStatus.ACTIVE)
        resumed_session = service.update_session(session.id, resume_update)
        
        assert resumed_session.status == SessionStatus.ACTIVE
        assert resumed_session.pause_time is None
        assert resumed_session.total_duration > 0
        assert service.get_active_session() == resumed_session
    
    def test_stop_session(self, service):
        session_data = SessionCreate(task_name="ドキュメント作成")
        session = service.start_session(session_data)
        
        import time
        time.sleep(0.01)
        
        stopped_session = service.stop_session(session.id)
        
        assert stopped_session.status == SessionStatus.STOPPED
        assert stopped_session.end_time is not None
        assert stopped_session.total_duration > 0
        assert service.get_active_session() is None
    
    def test_get_active_session_when_none(self, service):
        active_session = service.get_active_session()
        assert active_session is None
    
    def test_get_session_not_found(self, service):
        with pytest.raises(ValueError, match="Session not found"):
            service.get_session("non-existent-id")
    
    def test_update_nonexistent_session(self, service):
        update_data = SessionUpdate(status=SessionStatus.PAUSED)
        
        with pytest.raises(ValueError, match="Session not found"):
            service.update_session("non-existent-id", update_data)
    
    def test_pause_already_paused_session(self, service):
        session_data = SessionCreate(task_name="バグ修正")
        session = service.start_session(session_data)
        
        pause_update = SessionUpdate(status=SessionStatus.PAUSED)
        service.update_session(session.id, pause_update)
        
        paused_again = service.update_session(session.id, pause_update)
        
        assert paused_again.status == SessionStatus.PAUSED
    
    def test_time_calculation_accuracy(self, service):
        session_data = SessionCreate(task_name="精度テスト")
        session = service.start_session(session_data)
        
        import time
        sleep_duration = 0.05
        time.sleep(sleep_duration)
        
        stopped_session = service.stop_session(session.id)
        
        assert stopped_session.total_duration >= int(sleep_duration * 1000) - 10
        assert stopped_session.total_duration <= int(sleep_duration * 1000) + 50
    
    def test_session_list_management(self, service):
        sessions = []
        for i in range(3):
            session_data = SessionCreate(task_name=f"タスク{i+1}")
            session = service.start_session(session_data)
            sessions.append(session)
            
            import time
            time.sleep(0.01)
        
        active_session = service.get_active_session()
        assert active_session.id == sessions[-1].id
        
        for session in sessions[:-1]:
            stored_session = service.get_session(session.id)
            assert stored_session.status == SessionStatus.STOPPED