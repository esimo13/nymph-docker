from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ResumeData(BaseModel):
    """Schema for parsed resume data"""
    personal_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    certifications: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    languages: List[Dict[str, Any]]

class ResumeResponse(BaseModel):
    """Schema for resume response"""
    job_id: str
    status: str
    data: Optional[ResumeData] = None
    error: Optional[str] = None

class ChatMessageSchema(BaseModel):
    """Schema for chat message in requests"""
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str
    resume_data: Optional[Dict[str, Any]] = None
    chat_history: List[ChatMessageSchema] = []
    session_id: Optional[str] = None
    resume_id: Optional[int] = None

class ChatResponse(BaseModel):
    """Schema for chat response"""
    response: str
    session_id: str
    message_count: int

class ChatHistoryMessage(BaseModel):
    """Schema for chat history message"""
    role: str
    content: str
    timestamp: str
    order: int

class ChatSessionInfo(BaseModel):
    """Schema for chat session information"""
    session_id: str
    resume_id: Optional[int]
    created_at: str
    message_count: int
    last_message_time: Optional[str]
