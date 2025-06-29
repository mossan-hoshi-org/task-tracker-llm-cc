from fastapi import FastAPI, Depends, HTTPException
from typing import Optional
from models import SessionCreate, SessionResponse, SummaryRequest, SummaryResponse
from session_service import SessionService
from gemini_service import GeminiService
import os
from dotenv import load_dotenv

load_dotenv()

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

_gemini_service_instance = None

def get_gemini_service():
    global _gemini_service_instance
    if _gemini_service_instance is None:
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        _gemini_service_instance = GeminiService(api_key, model_name)
    return _gemini_service_instance

def reset_gemini_service():
    global _gemini_service_instance
    _gemini_service_instance = None

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

@app.post("/summary/generate", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryRequest,
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    try:
        summary = await gemini_service.categorize_tasks(request.sessions)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)