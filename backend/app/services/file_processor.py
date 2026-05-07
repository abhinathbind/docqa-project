import os
import json
import tempfile
from pathlib import Path
from typing import Optional, List
import openai
from app.core.config import settings
from app.models.schemas import TranscriptSegment

# Lazy imports for heavy deps
def _get_pdf_reader():
    import pypdf
    return pypdf

def _get_moviepy():
    import moviepy.editor as mp
    return mp

client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file."""
    pypdf = _get_pdf_reader()
    text_parts = []
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
    return "\n\n".join(text_parts)

async def extract_audio_from_video(video_path: str) -> str:
    """Extract audio track from video and return temp wav path."""
    mp = _get_moviepy()
    video = mp.VideoFileClip(video_path)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    video.audio.write_audiofile(tmp.name, verbose=False, logger=None)
    video.close()
    return tmp.name

async def transcribe_audio(file_path: str, file_type: str) -> List[TranscriptSegment]:
    """Transcribe audio/video using OpenAI Whisper with timestamps."""
    audio_path = file_path
    tmp_path = None

    try:
        if file_type == "video":
            tmp_path = await extract_audio_from_video(file_path)
            audio_path = tmp_path

        with open(audio_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model=settings.WHISPER_MODEL,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        if hasattr(response, "segments") and response.segments:
            for seg in response.segments:
                segments.append(TranscriptSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                ))
        else:
            # Fallback: single segment with full text
            segments.append(TranscriptSegment(start=0.0, end=0.0, text=response.text))

        return segments
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

async def generate_summary(text: str, file_type: str) -> str:
    """Generate a concise summary of document/transcript content."""
    max_chars = 12000
    truncated = text[:max_chars] + ("..." if len(text) > max_chars else "")
    prompt = f"Summarize the following {file_type} content in 3-5 sentences:\n\n{truncated}"
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()
