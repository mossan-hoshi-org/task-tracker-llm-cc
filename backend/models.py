from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SessionStatus(str, Enum):
    """セッションのステータスを表すエナム"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class SessionCreate(BaseModel):
    """セッション作成時のリクエストモデル"""
    task_name: str = Field(..., min_length=1, description="作業名")
    
    @field_validator('task_name')
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        """タスク名のバリデーション"""
        # 空白のみの文字列をチェック
        if not v.strip():
            raise ValueError("Task name cannot be empty or whitespace only")
        return v.strip()


class SessionUpdate(BaseModel):
    """セッション更新時のリクエストモデル"""
    status: Optional[SessionStatus] = None


class Session(BaseModel):
    """セッションのメインモデル"""
    id: str = Field(..., description="セッションID")
    task_name: str = Field(..., description="作業名")
    status: SessionStatus = Field(..., description="セッションステータス")
    start_time: datetime = Field(..., description="開始時刻")
    pause_time: Optional[datetime] = Field(None, description="一時停止時刻")
    end_time: Optional[datetime] = Field(None, description="終了時刻")
    total_duration: int = Field(0, description="総経過時間（秒）")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class SessionResponse(BaseModel):
    """セッションのレスポンスモデル"""
    id: str
    task_name: str
    status: SessionStatus
    start_time: datetime
    pause_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration: int
    elapsed_seconds: int = Field(..., description="現在の経過時間（秒）")
    
    @classmethod
    def from_session(cls, session: Session) -> "SessionResponse":
        """Sessionモデルからレスポンスモデルを作成"""
        current_time = datetime.now(timezone.utc)
        
        # 経過時間の計算
        elapsed_seconds = session.total_duration
        
        if session.status == SessionStatus.ACTIVE:
            # アクティブな場合は開始時刻からの経過時間を追加
            elapsed_seconds += int((current_time - session.start_time).total_seconds())
        elif session.status == SessionStatus.PAUSED and session.pause_time:
            # 一時停止の場合は一時停止時刻までの経過時間を追加
            elapsed_seconds += int((session.pause_time - session.start_time).total_seconds())
        
        return cls(
            id=session.id,
            task_name=session.task_name,
            status=session.status,
            start_time=session.start_time,
            pause_time=session.pause_time,
            end_time=session.end_time,
            total_duration=session.total_duration,
            elapsed_seconds=max(0, elapsed_seconds)
        )
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )