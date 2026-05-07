import os
import uuid
import asyncio
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.schemas import DocumentResponse, FileType
from app.services import file_processor

router = APIRouter()

ALLOWED_EXTENSIONS = {
    "pdf": FileType.PDF,
    "mp3": FileType.AUDIO, "wav": FileType.AUDIO, "m4a": FileType.AUDIO,
    "mp4": FileType.VIDEO, "mov": FileType.VIDEO, "avi": FileType.VIDEO,
}

def _ext(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()

async def _process_document(doc_id: str, file_path: str, file_type: str):
    """Background task: extract text, transcribe, summarize, update DB."""
    db = get_db()
    try:
        text_content = None
        transcript_segments = None

        if file_type == "pdf":
            text_content = await file_processor.extract_pdf_text(file_path)
        else:
            segments = await file_processor.transcribe_audio(file_path, file_type)
            transcript_segments = [s.model_dump() for s in segments]
            text_content = " ".join(s.text for s in segments)

        summary = await file_processor.generate_summary(text_content, file_type)

        await db.documents.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {
                "status": "ready",
                "text_content": text_content,
                "summary": summary,
                "transcript_segments": transcript_segments,
                "updated_at": datetime.utcnow(),
            }},
        )
    except Exception as e:
        await db.documents.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": "error", "metadata.error": str(e)}},
        )

@router.post("/upload", response_model=DocumentResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    ext = _ext(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    save_name = f"{uuid.uuid4()}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_name)

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, "File too large")

    with open(save_path, "wb") as f:
        f.write(content)

    db = get_db()
    file_type = ALLOWED_EXTENSIONS[ext].value
    doc = {
        "user_id": current_user["user_id"],
        "filename": file.filename,
        "file_type": file_type,
        "file_path": save_path,
        "file_size": len(content),
        "status": "processing",
        "text_content": None,
        "summary": None,
        "transcript_segments": None,
        "metadata": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.documents.insert_one(doc)
    doc_id = str(result.inserted_id)

    background_tasks.add_task(_process_document, doc_id, save_path, file_type)

    return DocumentResponse(
        id=doc_id,
        filename=file.filename,
        file_type=file_type,
        status="processing",
        created_at=doc["created_at"],
    )

@router.get("/", response_model=List[DocumentResponse])
async def list_files(current_user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.documents.find({"user_id": current_user["user_id"]}).sort("created_at", -1)
    docs = []
    async for doc in cursor:
        docs.append(DocumentResponse(
            id=str(doc["_id"]),
            filename=doc["filename"],
            file_type=doc["file_type"],
            status=doc["status"],
            summary=doc.get("summary"),
            created_at=doc["created_at"],
        ))
    return docs

@router.get("/{doc_id}")
async def get_file(doc_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    doc = await db.documents.find_one({"_id": ObjectId(doc_id), "user_id": current_user["user_id"]})
    if not doc:
        raise HTTPException(404, "Document not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.delete("/{doc_id}")
async def delete_file(doc_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    doc = await db.documents.find_one({"_id": ObjectId(doc_id), "user_id": current_user["user_id"]})
    if not doc:
        raise HTTPException(404, "Document not found")
    if os.path.exists(doc["file_path"]):
        os.unlink(doc["file_path"])
    await db.documents.delete_one({"_id": ObjectId(doc_id)})
    await db.chat_sessions.delete_many({"document_id": doc_id})
    return {"message": "Deleted"}
