from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Dispute, DecisionArtifactModel, Order, ChatMessage as ChatMessageDB
from app.services.case_service import CaseService

router = APIRouter(
    prefix="/copilot",
    tags=["Copilot"]
)

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    merchant_id: str
    case_id: Optional[str] = None
    session_id: Optional[str] = None
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str
    references: List[str] = []

@router.post("/chat", response_model=ChatResponse)
async def copilot_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Aura Assistant Endpoint
    Saves memory to PostgreSQL and returns a warm, contextual response.
    """
    session_id = request.session_id or "default-session"
    
    # Save User Message to Memory
    user_msg = ChatMessageDB(
        merchant_id=request.merchant_id,
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()
    
    # Generate Aura Response (Placeholder logic)
    if request.case_id:
        service = CaseService(db)
        case = await service.get_case(request.case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        reply = f"I've taken a look at case {request.case_id} for you. The disputed amount is ${case.dispute.dispute_amount}. What specific detail would you like me to analyze?"
        refs = [request.case_id]
    else:
        reply = f"I'm here to help with your portfolio! I've securely logged your message into my memory banks. How can I assist you with your chargebacks today?"
        refs = []
        
    # Save Aura Message to Memory
    aura_msg = ChatMessageDB(
        merchant_id=request.merchant_id,
        session_id=session_id,
        role="assistant",
        content=reply
    )
    db.add(aura_msg)
    await db.commit()
        
    return ChatResponse(response=reply, references=refs)
