import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from models import Session, SessionCreate, SessionUpdate, SessionStatus


class SessionService:
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._active_session_id: Optional[str] = None
    
    def start_session(self, session_data: SessionCreate) -> Session:
        if self._active_session_id:
            self._stop_session_internal(self._active_session_id)
        
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        session = Session(
            id=session_id,
            task_name=session_data.task_name,
            status=SessionStatus.ACTIVE,
            start_time=start_time,
            pause_time=None,
            end_time=None,
            total_duration=0
        )
        
        self._sessions[session_id] = session
        self._active_session_id = session_id
        
        return session
    
    def update_session(self, session_id: str, update_data: SessionUpdate) -> Session:
        session = self.get_session(session_id)
        current_time = datetime.now(timezone.utc)
        
        if update_data.status:
            if update_data.status == SessionStatus.PAUSED:
                session = self._pause_session(session, current_time)
            elif update_data.status == SessionStatus.ACTIVE:
                session = self._resume_session(session, current_time)
            elif update_data.status == SessionStatus.STOPPED:
                session = self._stop_session_internal(session_id)
        
        return session
    
    def stop_session(self, session_id: str) -> Session:
        return self._stop_session_internal(session_id)
    
    def get_session(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            raise ValueError("Session not found")
        
        return self._sessions[session_id]
    
    def get_active_session(self) -> Optional[Session]:
        if self._active_session_id and self._active_session_id in self._sessions:
            return self._sessions[self._active_session_id]
        return None
    
    def _pause_session(self, session: Session, current_time: datetime) -> Session:
        if session.status == SessionStatus.ACTIVE:
            elapsed_time = int((current_time - session.start_time).total_seconds() * 1000)
            session.total_duration += elapsed_time
            session.pause_time = current_time
        
        session.status = SessionStatus.PAUSED
        
        if self._active_session_id == session.id:
            self._active_session_id = None
        
        self._sessions[session.id] = session
        return session
    
    def _resume_session(self, session: Session, current_time: datetime) -> Session:
        if session.status == SessionStatus.PAUSED:
            if self._active_session_id:
                self._stop_session_internal(self._active_session_id)
            
            session.start_time = current_time
            session.pause_time = None
            session.status = SessionStatus.ACTIVE
            
            self._active_session_id = session.id
        
        self._sessions[session.id] = session
        return session
    
    def _stop_session_internal(self, session_id: str) -> Session:
        session = self.get_session(session_id)
        current_time = datetime.now(timezone.utc)
        
        if session.status == SessionStatus.ACTIVE:
            elapsed_time = int((current_time - session.start_time).total_seconds() * 1000)
            session.total_duration += elapsed_time
        elif session.status == SessionStatus.PAUSED and session.pause_time:
            pass
        
        session.status = SessionStatus.STOPPED
        session.end_time = current_time
        
        if self._active_session_id == session.id:
            self._active_session_id = None
        
        self._sessions[session_id] = session
        return session