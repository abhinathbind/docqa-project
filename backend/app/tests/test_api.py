import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.services.ai_service import _find_relevant_timestamp


class TestSecurity:
    def test_hash_password(self):
        hashed = hash_password("pass123")
        assert hashed != "pass123"
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        hashed = hash_password("pass123")
        assert verify_password("pass123", hashed) is True

    def test_verify_password_wrong(self):
        hashed = hash_password("pass123")
        assert verify_password("wrong", hashed) is False

    def test_create_access_token(self):
        token = create_access_token({"sub": "abc", "email": "a@b.com"})
        assert isinstance(token, str)
        assert len(token) > 10

    def test_settings_exist(self):
        assert settings.MONGODB_DB == "docqa"
        assert settings.ALGORITHM == "HS256"

    def test_settings_app_name(self):
        assert settings.APP_NAME == "DocQA"


class TestAIService:
    def test_find_relevant_timestamp_no_segments(self):
        result = _find_relevant_timestamp("some answer", [])
        assert result is None

    def test_find_relevant_timestamp_with_match(self):
        segments = [
            {"start": 10.0, "end": 20.0, "text": "neural networks are powerful"},
            {"start": 25.0, "end": 35.0, "text": "deep learning applications"},
        ]
        result = _find_relevant_timestamp("neural networks discussed here", segments)
        assert result is not None
        assert result["start"] == 10.0

    def test_find_relevant_timestamp_fallback(self):
        segments = [{"start": 5.0, "end": 10.0, "text": "hello world"}]
        result = _find_relevant_timestamp("completely different xyz", segments)
        assert result == segments[0]

    def test_find_relevant_timestamp_multiple(self):
        segments = [
            {"start": 0.0, "end": 5.0, "text": "introduction"},
            {"start": 5.0, "end": 10.0, "text": "machine learning models training"},
            {"start": 10.0, "end": 15.0, "text": "conclusion"},
        ]
        result = _find_relevant_timestamp("machine learning models", segments)
        assert result["start"] == 5.0


@pytest.mark.asyncio
class TestAIServiceAsync:
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

    async def test_chat_with_history(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Follow-up answer."
        with patch("app.services.ai_service.client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            from app.services.ai_service import chat_with_document
            result = await chat_with_document(
                question="Follow-up?",
                text_content="Context text",
                history=[{"role": "user", "content": "Q"}, {"role": "assistant", "content": "A"}],
            )
            assert result["answer"] == "Follow-up answer."

    async def test_generate_summary(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is a summary."
        with patch("app.services.file_processor.client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            from app.services.file_processor import generate_summary
            summary = await generate_summary("Long document text here...", "pdf")
            assert summary == "This is a summary."

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


class TestConfig:
    def test_max_file_size(self):
        assert settings.MAX_FILE_SIZE_MB == 100

    def test_token_expire(self):
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_mongodb_db_name(self):
        assert "docqa" in settings.MONGODB_DB

    def test_openai_model(self):
        assert "gpt" in settings.OPENAI_MODEL

    def test_whisper_model(self):
        assert settings.WHISPER_MODEL == "whisper-1"

    def test_allowed_origins_is_list(self):
        assert isinstance(settings.ALLOWED_ORIGINS, list)

    def test_upload_dir(self):
        assert settings.UPLOAD_DIR is not None


class TestSchemas:
    def test_file_type_enum(self):
        from app.models.schemas import FileType
        assert FileType.PDF == "pdf"
        assert FileType.AUDIO == "audio"
        assert FileType.VIDEO == "video"

    def test_transcript_segment(self):
        from app.models.schemas import TranscriptSegment
        seg = TranscriptSegment(start=1.0, end=2.0, text="hello")
        assert seg.start == 1.0
        assert seg.text == "hello"

    def test_chat_message(self):
        from app.models.schemas import ChatMessage
        msg = ChatMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_chat_request(self):
        from app.models.schemas import ChatRequest
        req = ChatRequest(document_id="abc123", message="test")
        assert req.document_id == "abc123"
        assert req.session_id is None

    def test_document_response(self):
        from app.models.schemas import DocumentResponse
        doc = DocumentResponse(
            id="123",
            filename="test.pdf",
            file_type="pdf",
            status="ready",
            created_at=datetime.utcnow()
        )
        assert doc.filename == "test.pdf"