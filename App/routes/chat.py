import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from anthropic import Anthropic

from App.database.db import get_db
from App.models.chat import ChatSession, ChatMessage
from App.models.promise import Promise
from App.models.sug_profile import SUGProfile
from App.models.user import User
from App.routes.auth import get_current_user
from App.config.settings import ANTHROPIC_API_KEY
from App.schemas.chat import ChatSessionResponse, ChatMessageResponse, ChatSendRequest, ChatSendResponse

router = APIRouter(prefix="/chat", tags=["AI Campus Copilot"])

claude_client = Anthropic(api_key=ANTHROPIC_API_KEY)
CLAUDE_MODEL = "claude-sonnet-5"


def call_claude(system_prompt: str, messages: list[dict]) -> str:
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=400,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"Sorry, I couldn't process that right now. ({e})"


def build_campus_context(db: Session, institution: str) -> str:
    promises = db.query(Promise).filter(Promise.institution == institution).all()
    officers = db.query(SUGProfile).filter(SUGProfile.institution == institution).all()

    context = f"CAMPUS: {institution}\n\nSUG PROMISES:\n"
    if promises:
        for p in promises[:20]:
            context += f"- {p.title} ({p.status}, {p.percent_complete}% complete, dept: {p.department or 'N/A'})\n"
    else:
        context += "No promises tracked yet.\n"

    context += "\nSUG OFFICERS:\n"
    if officers:
        for o in officers[:20]:
            context += f"- {o.name}, {o.position}" + (f" ({o.term})" if o.term else "") + "\n"
    else:
        context += "No SUG officer profiles added yet.\n"

    return context


@router.post("/new", response_model=ChatSessionResponse)
def new_chat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = ChatSession(user_id=current_user.id, title="New chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(
        ChatSession.updated_at.desc()).all()


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_messages(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return db.query(ChatMessage).filter(ChatMessage.chat_session_id == session_id).order_by(
        ChatMessage.created_at.asc()).all()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    db.query(ChatMessage).filter(ChatMessage.chat_session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "Chat deleted"}


@router.post("/{session_id}", response_model=ChatSendResponse)
def send_message(session_id: int, request: ChatSendRequest, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    user_msg = ChatMessage(chat_session_id=session_id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()

    history = db.query(ChatMessage).filter(ChatMessage.chat_session_id == session_id).order_by(
        ChatMessage.created_at.asc()).all()
    # Claude's messages API takes actual conversation turns rather than a
    # flattened text blob — role/content pairs, same roles your DB already
    # stores ("user"/"assistant"), so this maps over directly.
    claude_messages = [{"role": m.role, "content": m.content} for m in history[-10:]]

    context = build_campus_context(db, current_user.institution)

    system_prompt = (
        f"You are CiviAI Campus Copilot, an AI assistant helping students at {current_user.institution} "
        f"understand what's happening on their campus \u2014 SUG promises, officers, and general civic questions.\n\n"
        f"REAL CAMPUS DATA:\n{context}\n\n"
        f"Respond helpfully and conversationally to the student's latest message. Keep answers VERY SHORT \u2014 "
        f"2-3 sentences maximum unless the student explicitly asks for more detail. Get straight to the point. "
        f"Ground your answer in the real campus data above when relevant. "
        f"If you don't have data to answer something, say so honestly rather than making it up."
    )

    reply = call_claude(system_prompt, claude_messages)

    assistant_msg = ChatMessage(chat_session_id=session_id, role="assistant", content=reply)
    db.add(assistant_msg)

    if session.title == "New chat":
        session.title = request.message[:40]
    session.updated_at = datetime.utcnow()
    db.commit()

    return ChatSendResponse(reply=reply)
