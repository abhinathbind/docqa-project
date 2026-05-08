"""
Test suite for DocQA API — targets 95%+ coverage.
Run: pytest --cov=app --cov-report=term-missing
"""
import io
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime
from bson import ObjectId
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token, hash_password, verify_password

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_token():
    return create_access_token({"sub": "user_123", "email": "test@example.com"})

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def sample_doc_id():
    return str(ObjectId())

@pytest.fixture
def sample_session_id():
    return str(ObjectId())

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.documents = MagicMock()
    db.chat_sessions = MagicMock()
    return db

@pytest.fixture
def ready_doc(sample_doc_id):
    return {
        "_id": ObjectId(sample_doc_id),
        "user_id": "user_123",
        "filename": "test.pdf",
        "file_type": "pdf",
        "file_path": "/tmp/test.pdf",
        "file_size": 1024,
        "status": "ready",
        "text_content": "This is a sample document about machine learning.",
        "summary": "A document about ML.",
        "transcript_segments": None,
        "metadata": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

# ── Security Tests ────────────────────────────────────────────────────────────

class TestSecurity:
    def test_hash_password(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        hashed = hash_password("mypass123")
        assert verify_password("mypass123", hashed) is True

    def test_verify_password_wrong(self):
        hashed = hash_password("mypass123")
        assert verify_password("wrongpass", hashed) is False

    def test_create_access_token(self):
        token = create_access_token({"sub": "abc", "email": "a@b.com"})
        assert isinstance(token, str)
        assert len(token) > 10

    def test_create_access_token_with_expiry(self):
        from datetime import timedelta
        token = create_access_token({"sub": "abc"}, expires_delta=timedelta(minutes=5))
        assert isinstance(token, str)

# ── Health Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestHealth:
    async def test_health_ok(self):
        with patch("app.api.health.db_instance") as mock_db_inst:
            mock_db_inst.client.admin.command = AsyncMock(return_value={"ok": 1})
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

    async def test_health_db_down(self):
        with patch("app.api.health.db_instance") as mock_db_inst:
            mock_db_inst.client.admin.command = AsyncMock(side_effect=Exception("Connection refused"))
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "degraded"

# ── File Upload Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestFileUpload:
    async def test_upload_pdf_success(self, auth_headers, sample_doc_id):
        mock_db = MagicMock()
        mock_doc_id = ObjectId(sample_doc_id)
        mock_db.documents.insert_one = AsyncMock(return_value=MagicMock(inserted_id=mock_doc_id))
        mock_db.documents.create_index = AsyncMock()
        mock_db.chat_sessions.create_index = AsyncMock()

        with patch("app.api.files.get_db", return_value=mock_db), \
             patch("builtins.open", mock_open()), \
             patch("os.makedirs"), \
             patch("app.api.files._process_document", new_callable=AsyncMock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/files/upload",
                    headers=auth_headers,
                    files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
                )
            assert resp.status_code == 200
            data = resp.json()
            assert data["filename"] == "test.pdf"
            assert data["status"] == "processing"

    async def test_upload_unsupported_extension(self, auth_headers):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/files/upload",
                headers=auth_headers,
                files={"file": ("test.txt", b"hello", "text/plain")},
            )
        assert resp.status_code == 400

    async def test_list_files(self, auth_headers, ready_doc):
    mock_db = MagicMock()

    async def async_gen():
        yield ready_doc

    mock_db.documents.find.return_value.sort.return_value = async_gen()

        with patch("app.api.files.get_db", return_value=mock_db):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/files/", headers=auth_headers)
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

    async def test_get_file_not_found(self, auth_headers, sample_doc_id):
        mock_db = MagicMock()
        mock_db.documents.find_one = AsyncMock(return_value=None)
        with patch("app.api.files.get_db", return_value=mock_db):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get(f"/api/v1/files/{sample_doc_id}", headers=auth_headers)
            assert resp.status_code == 404

    async def test_delete_file(self, auth_headers, sample_doc_id, ready_doc):
        mock_db = MagicMock()
        mock_db.documents.find_one = AsyncMock(return_value=ready_doc)
        mock_db.documents.delete_one = AsyncMock()
        mock_db.chat_sessions.delete_many = AsyncMock()
        with patch("app.api.files.get_db", return_value=mock_db), \
             patch("os.path.exists", return_value=False):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.delete(f"/api/v1/files/{sample_doc_id}", headers=auth_headers)
            assert resp.status_code == 200

# ── Chat Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestChat:
    async def test_chat_success(self, auth_headers, sample_doc_id, sample_session_id, ready_doc):
        mock_db = MagicMock()
        mock_db.documents.find_one = AsyncMock(return_value=ready_doc)
        mock_db.chat_sessions.find_one = AsyncMock(return_value={
            "_id": ObjectId(sample_session_id),
            "messages": [],
        })
        mock_db.chat_sessions.update_one = AsyncMock()

        ai_result = {
            "answer": "Machine learning is a subset of AI.",
            "timestamp_reference": None,
            "relevant_segment": None,
        }

        with patch("app.api.chat.get_db", return_value=mock_db), \
             patch("app.api.chat.chat_with_document", new_callable=AsyncMock, return_value=ai_result):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/chat/",
                    headers=auth_headers,
                    json={
                        "document_id": sample_doc_id,
                        "session_id": sample_session_id,
                        "message": "What is machine learning?",
                    },
                )
            assert resp.status_code == 200
            assert "answer" in resp.json()

    async def test_chat_document_not_found(self, auth_headers, sample_doc_id):
        mock_db = MagicMock()
        mock_db.documents.find_one = AsyncMock(return_value=None)
        with patch("app.api.chat.get_db", return_value=mock_db):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/chat/",
                    headers=auth_headers,
                    json={"document_id": sample_doc_id, "message": "Hello"},
                )
            assert resp.status_code == 404

    async def test_chat_document_not_ready(self, auth_headers, sample_doc_id, ready_doc):
        ready_doc["status"] = "processing"
        mock_db = MagicMock()
        mock_db.documents.find_one = AsyncMock(return_value=ready_doc)
        with patch("app.api.chat.get_db", return_value=mock_db):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/chat/",
                    headers=auth_headers,
                    json={"document_id": sample_doc_id, "message": "Hello"},
                )
            assert resp.status_code == 400

    async def test_chat_creates_new_session(self, auth_headers, sample_doc_id, ready_doc):
        mock_db = MagicMock()
        mock_db.documents.find_one = AsyncMock(return_value=ready_doc)
        mock_db.chat_sessions.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
        mock_db.chat_sessions.update_one = AsyncMock()

        ai_result = {"answer": "Answer", "timestamp_reference": None, "relevant_segment": None}
        with patch("app.api.chat.get_db", return_value=mock_db), \
             patch("app.api.chat.chat_with_document", new_callable=AsyncMock, return_value=ai_result):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/v1/chat/",
                    headers=auth_headers,
                    json={"document_id": sample_doc_id, "message": "Hello"},
                )
            assert resp.status_code == 200
            assert "session_id" in resp.json()

# ── File Processor Service Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
class TestFileProcessor:
    async def test_extract_pdf_text(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Hello from PDF"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("app.services.file_processor._get_pdf_reader") as mock_pypdf:
            mock_pypdf.return_value.PdfReader.return_value = mock_reader
            with patch("builtins.open", mock_open(read_data=b"fake pdf")):
                from app.services.file_processor import extract_pdf_text
                text = await extract_pdf_text("/fake/path.pdf")
            assert "Hello from PDF" in text

    async def test_generate_summary(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is a summary."

        with patch("app.services.file_processor.client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            from app.services.file_processor import generate_summary
            summary = await generate_summary("Long document text here...", "pdf")
            assert summary == "This is a summary."

# ── AI Service Tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAIService:
    async def test_chat_with_document(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "The answer is 42."

        with patch("app.services.ai_service.client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            from app.services.ai_service import chat_with_document
            result = await chat_with_document(
                question="What is the answer?",
                text_content="The document says the answer is 42.",
                history=[],
            )
            assert result["answer"] == "The answer is 42."
            assert result["timestamp_reference"] is None

    async def test_chat_with_transcript_timestamps(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "The speaker discusses neural networks."
        segments = [
            {"start": 10.0, "end": 20.0, "text": "neural networks are powerful"},
            {"start": 25.0, "end": 35.0, "text": "deep learning applications"},
        ]

        with patch("app.services.ai_service.client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            from app.services.ai_service import chat_with_document
            result = await chat_with_document(
                question="What does the speaker discuss?",
                text_content="neural networks are powerful deep learning applications",
                history=[],
                transcript_segments=segments,
            )
            assert result["timestamp_reference"] is not None

    async def test_find_relevant_timestamp_no_match(self):
        from app.services.ai_service import _find_relevant_timestamp
        segments = [{"start": 5.0, "end": 10.0, "text": "hello world"}]
        result = _find_relevant_timestamp("completely unrelated answer xyz", segments)
        # Falls back to first segment
        assert result == segments[0]

    async def test_chat_with_history(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Follow-up answer."
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]

        with patch("app.services.ai_service.client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            from app.services.ai_service import chat_with_document
            result = await chat_with_document(
                question="Follow-up?",
                text_content="Context text",
                history=history,
            )
            assert result["answer"] == "Follow-up answer."
