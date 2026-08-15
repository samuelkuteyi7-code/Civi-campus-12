from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
import json
import re

from App.database.db import get_db
from App.models.debate import DebateRoom, DebateArgument
from App.models.user import User
from App.routes.auth import get_current_user
from App.config.settings import GEMINI_API_KEY
from App.schemas.debate import (
    DebateRoomCreate, DebateRoomResponse, DebateRoomListItem,
    ArgumentCreate, ArgumentResponse, ArgumentSubmitResult,
    SentimentBreakdown, DebateSummaryResponse
)

router = APIRouter(prefix="/debates", tags=["Civic Debate"])

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"


def call_gemini(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_URL, headers=headers, params=params, json=payload, timeout=45)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {e}"


def _sentiment(db: Session, room_id: int) -> SentimentBreakdown:
    args = db.query(DebateArgument).filter(DebateArgument.room_id == room_id).all()
    support = sum(1 for a in args if a.position == "support")
    oppose = sum(1 for a in args if a.position == "oppose")
    undecided = sum(1 for a in args if a.position == "undecided")
    total = support + oppose + undecided
    if total == 0:
        return SentimentBreakdown(support=0, oppose=0, undecided=0, support_pct=0, oppose_pct=0, undecided_pct=0, total=0)
    return SentimentBreakdown(
        support=support, oppose=oppose, undecided=undecided,
        support_pct=round(support / total * 100, 1),
        oppose_pct=round(oppose / total * 100, 1),
        undecided_pct=round(undecided / total * 100, 1),
        total=total
    )


def _to_argument_response(db: Session, a: DebateArgument) -> ArgumentResponse:
    author = db.query(User).filter(User.id == a.user_id).first()
    return ArgumentResponse(
        id=a.id, room_id=a.room_id, user_id=a.user_id,
        author_name=author.name if author else "Unknown",
        position=a.position, text=a.text, evidence_url=a.evidence_url,
        has_evidence=a.has_evidence, ai_moderation_note=a.ai_moderation_note,
        is_duplicate=a.is_duplicate, is_flagged=a.is_flagged, created_at=a.created_at
    )


@router.post("", response_model=DebateRoomResponse)
def create_room(request: DebateRoomCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    room = DebateRoom(
        question=request.question, description=request.description,
        article_id=request.article_id, institution=current_user.institution, status="open"
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return DebateRoomResponse(
        id=room.id, article_id=room.article_id, question=room.question, description=room.description,
        status=room.status, created_at=room.created_at, sentiment=_sentiment(db, room.id), arguments=[]
    )


@router.get("", response_model=list[DebateRoomListItem])
def list_rooms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DebateRoom).filter(DebateRoom.institution == current_user.institution).order_by(
        DebateRoom.created_at.desc()).all()


@router.get("/{room_id}", response_model=DebateRoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    room = db.query(DebateRoom).filter(DebateRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Debate room not found")
    args = db.query(DebateArgument).filter(DebateArgument.room_id == room_id).order_by(
        DebateArgument.created_at.asc()).all()
    return DebateRoomResponse(
        id=room.id, article_id=room.article_id, question=room.question, description=room.description,
        status=room.status, created_at=room.created_at, sentiment=_sentiment(db, room.id),
        arguments=[_to_argument_response(db, a) for a in args]
    )


@router.post("/{room_id}/arguments", response_model=ArgumentSubmitResult)
def submit_argument(room_id: int, request: ArgumentCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    room = db.query(DebateRoom).filter(DebateRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Debate room not found")
    if request.position not in ("support", "oppose", "undecided"):
        raise HTTPException(status_code=400, detail="position must be support, oppose, or undecided")

    has_evidence = 1 if request.evidence_url else 0
    existing_args = db.query(DebateArgument).filter(DebateArgument.room_id == room_id).all()
    existing_texts = "\n".join(f"- {a.text}" for a in existing_args[-20:])

    prompt = (
        f"You are CiviAI Campus's Debate Moderator for the question: \"{room.question}\"\n\n"
        f"A student just submitted this argument (position: {request.position}):\n\"{request.text}\"\n\n"
        f"Existing arguments already in this debate:\n{existing_texts or 'None yet'}\n\n"
        f"Check three things and respond in this EXACT JSON format, nothing else:\n"
        f'{{"is_duplicate": true/false, "is_abusive": true/false, "note": "one short sentence"}}'
    )

    result = call_gemini(prompt)
    is_duplicate = False
    is_abusive = False
    note = "Looks good."
    json_match = re.search(r'\{.*\}', result, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            is_duplicate = bool(parsed.get("is_duplicate", False))
            is_abusive = bool(parsed.get("is_abusive", False))
            note = parsed.get("note", note)
        except json.JSONDecodeError:
            pass

    argument = DebateArgument(
        room_id=room_id, user_id=current_user.id, position=request.position,
        text=request.text, evidence_url=request.evidence_url, has_evidence=has_evidence,
        ai_moderation_note=note, is_duplicate=1 if is_duplicate else 0, is_flagged=1 if is_abusive else 0
    )
    db.add(argument)
    db.commit()
    db.refresh(argument)

    warning = None
    if is_abusive:
        warning = "This argument was flagged as potentially abusive or off-topic."
    elif is_duplicate:
        warning = "This looks similar to an existing argument."
    elif not has_evidence:
        warning = "No evidence attached - this will show as an Opinion, not Evidence-backed."

    return ArgumentSubmitResult(argument=_to_argument_response(db, argument), warning=warning)


@router.get("/{room_id}/summary", response_model=DebateSummaryResponse)
def summarize_debate(room_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    room = db.query(DebateRoom).filter(DebateRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Debate room not found")

    args = db.query(DebateArgument).filter(DebateArgument.room_id == room_id).all()
    support_args = "\n".join(f"- {a.text}" for a in args if a.position == "support")
    oppose_args = "\n".join(f"- {a.text}" for a in args if a.position == "oppose")

    prompt = (
        f"You are CiviAI Campus's Debate Summarizer for the question: \"{room.question}\"\n\n"
        f"SUPPORT arguments:\n{support_args or 'None'}\n\n"
        f"OPPOSE arguments:\n{oppose_args or 'None'}\n\n"
        f"Respond in this exact format:\n"
        f"SUPPORT_SUMMARY: [1-2 sentences]\n"
        f"OPPOSE_SUMMARY: [1-2 sentences]\n"
        f"COMMON_GROUND: [1 sentence]"
    )

    result = call_gemini(prompt)

    def extract(label, next_label=None):
        if label not in result:
            return ""
        chunk = result.split(label, 1)[1]
        if next_label and next_label in chunk:
            chunk = chunk.split(next_label)[0]
        return chunk.strip()

    return DebateSummaryResponse(
        support_summary=extract("SUPPORT_SUMMARY:", "OPPOSE_SUMMARY:"),
        oppose_summary=extract("OPPOSE_SUMMARY:", "COMMON_GROUND:"),
        common_ground=extract("COMMON_GROUND:")
    )


@router.patch("/{room_id}/close")
def close_room(room_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    room = db.query(DebateRoom).filter(DebateRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Debate room not found")
    room.status = "closed"
    db.commit()
    return {"message": "Debate closed"}
