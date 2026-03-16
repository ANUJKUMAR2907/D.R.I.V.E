from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
from openai import AsyncOpenAI

from database.models import User
from services.auth_service import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI assistant for D.R.I.V.E (Dynamic Road Infrastructure & Vehicle Ecosystem),
an AI-powered centralized traffic control system. You help traffic management operators by answering
questions about traffic conditions, incidents, speed limits, emergency vehicle coordination, and
general system usage. Be concise and helpful."""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    model: str


def get_openai_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")
    return AsyncOpenAI(api_key=api_key)


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    AI chat assistant for the D.R.I.V.E system.
    Uses OpenAI chat completions without unsupported parameters such as service_tier='flex'.
    """
    model = request.model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    client = get_openai_client()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        raise HTTPException(status_code=502, detail="Failed to get a response from the AI service")

    reply = response.choices[0].message.content or ""
    return ChatResponse(reply=reply, model=response.model)
