import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from bson import ObjectId
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai_service import chat_with_document, stream_chat_with_document

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    db = get_db()

    # Fetch document
    doc = await db.documents.find_one({
        "_id": ObjectId(request.document_id),
        "user_id": current_user["user_id"],
    })
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc["status"] != "ready":
        raise HTTPException(400, f"Document is still {doc['status']}")

    # Get or create session
    session_id = request.session_id
    history = []
    if session_id:
        session = await db.chat_sessions.find_one({"_id": ObjectId(session_id)})
        if session:
            history = [{"role": m["role"], "content": m["content"]} for m in session.get("messages", [])]
    else:
        result = await db.chat_sessions.insert_one({
            "document_id": request.document_id,
            "user_id": current_user["user_id"],
            "messages": [],
            "created_at": datetime.utcnow(),
        })
        session_id = str(result.inserted_id)

    # Generate answer
    result = await chat_with_document(
        question=request.message,
        text_content=doc.get("text_content", ""),
        history=history,
        transcript_segments=doc.get("transcript_segments"),
    )

    # Persist messages
    user_msg = {"role": "user", "content": request.message, "timestamp": datetime.utcnow()}
    ai_msg = {
        "role": "assistant",
        "content": result["answer"],
        "timestamp": datetime.utcnow(),
        "timestamp_reference": result.get("timestamp_reference"),
    }
    await db.chat_sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$push": {"messages": {"$each": [user_msg, ai_msg]}}},
    )

    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        timestamp_reference=result.get("timestamp_reference"),
        relevant_segment=result.get("relevant_segment"),
    )

@router.post("/stream")
async def chat_stream(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Server-Sent Events streaming endpoint."""
    db = get_db()
    doc = await db.documents.find_one({
        "_id": ObjectId(request.document_id),
        "user_id": current_user["user_id"],
    })
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc["status"] != "ready":
        raise HTTPException(400, f"Document is {doc['status']}")

    session_id = request.session_id
    history = []
    if session_id:
        session = await db.chat_sessions.find_one({"_id": ObjectId(session_id)})
        if session:
            history = [{"role": m["role"], "content": m["content"]} for m in session.get("messages", [])]
    else:
        result = await db.chat_sessions.insert_one({
            "document_id": request.document_id,
            "user_id": current_user["user_id"],
            "messages": [],
            "created_at": datetime.utcnow(),
        })
        session_id = str(result.inserted_id)

    async def event_generator():
        full_answer = ""
        # Send session_id first
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

        async for token in stream_chat_with_document(
            question=request.message,
            text_content=doc.get("text_content", ""),
            history=history,
            transcript_segments=doc.get("transcript_segments"),
        ):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Persist
        user_msg = {"role": "user", "content": request.message, "timestamp": datetime.utcnow()}
        ai_msg = {"role": "assistant", "content": full_answer, "timestamp": datetime.utcnow()}
        await db.chat_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$push": {"messages": {"$each": [user_msg, ai_msg]}}},
        )
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/sessions/{document_id}")
async def get_sessions(document_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.chat_sessions.find({
        "document_id": document_id,
        "user_id": current_user["user_id"],
    }).sort("created_at", -1)
    sessions = []
    async for s in cursor:
        s["id"] = str(s.pop("_id"))
        sessions.append(s)
    return sessions
