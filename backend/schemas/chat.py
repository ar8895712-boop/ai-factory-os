# ==============================================================
# backend/schemas/chat.py — Factory GPT & Memory Pydantic Schemas
# ==============================================================
"""
Typed schemas for Factory GPT chat messages, tool execution records,
and FAISS vector memory search outputs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolCallRecordSchema(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: str


class ChatMessageRequest(BaseModel):
    query: str = Field(description="Operator prompt or question for Factory GPT")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Optional recent message history: [{'role': 'user', 'content': '...'}]"
    )


class ChatMessageResponse(BaseModel):
    role: str = "assistant"
    content: str
    tool_calls: List[ToolCallRecordSchema] = Field(default_factory=list)
    timestamp: str


class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    machine_id: Optional[int] = None


class SimilarIncidentMatchSchema(BaseModel):
    incident_id: int
    machine_id: int
    machine_name: str
    severity: str
    category: str
    description: str
    health_score_at_time: Optional[float]
    rul_at_time: Optional[float]
    action_taken: Optional[str]
    resolution_notes: Optional[str]
    similarity_score: float
    timestamp: str


class FailurePatternSchema(BaseModel):
    category: str
    frequency: int
    affected_machines: List[str]
    common_symptoms: List[str]
    recommended_action: str
    avg_downtime_hours: float


class ToolDefinitionSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

