from fastapi import FastAPI, Depends, HTTPException
from typing import Optional
from models import SessionCreate, SessionResponse
from session_service import SessionService

app = FastAPI(
    title="Task Tracker API",
    description="作業時間追跡とカテゴリ分類のためのAPI",
    version="0.1.0"
)

_session_service_instance = None

def get_session_service():
    global _session_service_instance
    if _session_service_instance is None:
        _session_service_instance = SessionService()
    return _session_service_instance

def reset_session_service():
    global _session_service_instance
    _session_service_instance = None

@app.get("/")
async def read_root():
    return {"message": "Task Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/sessions/start", response_model=SessionResponse, status_code=201)
async def start_session(
    session_data: SessionCreate,
    service: SessionService = Depends(get_session_service)
):
    session = service.start_session(session_data)
    return SessionResponse.from_session(session)

@app.get("/sessions/active", response_model=Optional[SessionResponse])
async def get_active_session(
    service: SessionService = Depends(get_session_service)
):
    session = service.get_active_session()
    if session is None:
        return None
    return SessionResponse.from_session(session)

@app.patch("/sessions/{session_id}/pause", response_model=SessionResponse)
async def pause_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    try:
        session = service.pause_session(session_id)
        return SessionResponse.from_session(session)
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found")
        elif "Cannot pause a stopped session" in str(e):
            raise HTTPException(status_code=400, detail="Cannot pause a stopped session")
        else:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/sessions/{session_id}/stop", response_model=SessionResponse)
async def stop_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    try:
        session = service.stop_session(session_id)
        return SessionResponse.from_session(session)
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)