# ==============================================================
# backend/routers/chat.py — Factory GPT & Memory REST Endpoints
# ==============================================================
"""
Endpoints for Factory GPT AI assistant and FAISS Vector Memory:
- POST /api/chat/message   — Dialogue with tool calling
- GET  /api/chat/tools     — Registered tools and parameters
- POST /api/memory/search  — Semantic vector incident search
- GET  /api/memory/patterns — Common recurring failure signatures
- POST /api/memory/reindex — Rebuild FAISS index from database
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from backend.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    FailurePatternSchema,
    MemorySearchRequest,
    SimilarIncidentMatchSchema,
    ToolCallRecordSchema,
    ToolDefinitionSchema,
)
from backend.services.factory_gpt import OPENAI_TOOLS, get_factory_gpt
from backend.services.factory_memory import get_factory_memory

router = APIRouter(tags=["Factory GPT & Memory"])


# ── Chat Dialogue ─────────────────────────────────────────────────────

@router.post(
    "/api/chat/message",
    response_model=ChatMessageResponse,
    summary="Chat with Factory GPT (RAG + Autonomous Tool Calling)",
    description=(
        "Sends a query to Factory GPT. The model NEVER calculates numbers itself; "
        "it selects backend tools (get_machine_health, get_rul, explain_prediction, "
        "find_similar_incidents, run_simulation, get_business_impact) and explains "
        "the verified mathematical results in simple, professional language."
    ),
)
def chat_with_factory_gpt(req: ChatMessageRequest) -> ChatMessageResponse:
    gpt = get_factory_gpt()
    msg = gpt.ask(query=req.query, conversation_history=req.conversation_history)

    tool_call_schemas = [
        ToolCallRecordSchema(
            tool_name=tc.tool_name,
            arguments=tc.arguments,
            result=tc.result,
            timestamp=tc.timestamp,
        )
        for tc in msg.tool_calls
    ]

    return ChatMessageResponse(
        role=msg.role,
        content=msg.content,
        tool_calls=tool_call_schemas,
        timestamp=msg.timestamp,
    )


@router.get(
    "/api/chat/tools",
    response_model=List[ToolDefinitionSchema],
    summary="List available backend tools for Factory GPT",
)
def list_factory_gpt_tools() -> List[ToolDefinitionSchema]:
    tools = []
    for t in OPENAI_TOOLS:
        fn = t["function"]
        tools.append(ToolDefinitionSchema(
            name=fn["name"],
            description=fn["description"],
            parameters=fn["parameters"],
        ))
    return tools


# ── Factory Memory Endpoints ──────────────────────────────────────────

@router.post(
    "/api/memory/search",
    response_model=List[SimilarIncidentMatchSchema],
    summary="Semantic vector search across historical incidents via FAISS",
    description="Encodes query using all-MiniLM-L6-v2 and searches FAISS index using cosine similarity.",
)
def search_similar_incidents(req: MemorySearchRequest) -> List[SimilarIncidentMatchSchema]:
    memory = get_factory_memory()
    matches = memory.search_similar(
        query=req.query,
        top_k=req.top_k,
        machine_id=req.machine_id,
    )
    return [SimilarIncidentMatchSchema(**asdict(m)) for m in matches]


@router.get(
    "/api/memory/patterns",
    response_model=List[FailurePatternSchema],
    summary="Discover recurring failure patterns from memory",
    description="Aggregates past incidents to reveal frequent failure modes, affected machines, and typical resolutions.",
)
def get_failure_patterns() -> List[FailurePatternSchema]:
    memory = get_factory_memory()
    patterns = memory.learn_failure_patterns()
    return [FailurePatternSchema(**asdict(p)) for p in patterns]


@router.post(
    "/api/memory/reindex",
    summary="Rebuild FAISS index from SQLite incidents table",
)
def rebuild_memory_index() -> Dict[str, Any]:
    memory = get_factory_memory()
    memory.rebuild_index_from_db()
    return {
        "status": "success",
        "indexed_incidents_count": memory.index.ntotal,
        "embedding_dim": memory.embed_dim,
    }

