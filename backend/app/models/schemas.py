from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class DocumentModel(BaseModel):
    id: Optional[str] = None
    user_id: str
    filename: str
    file_type: FileType
    file_path: str
    file_size: int
    status: str = "processing"  # processing | ready | error
    text_content: Optional[str] = None
    summary: Optional[str] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    timestamp_reference: Optional[float] = None  # seconds into audio/video

class ChatSession(BaseModel):
    id: Optional[str] = None
    document_id: str
    user_id: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response schemas
class ChatRequest(BaseModel):
    document_id: str
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    timestamp_reference: Optional[float] = None
    relevant_segment: Optional[TranscriptSegment] = None

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    summary: Optional[str] = None
    created_at: datetime

class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
