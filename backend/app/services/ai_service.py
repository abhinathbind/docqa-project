import json
from typing import AsyncGenerator, Optional, List
import openai
from app.core.config import settings
from app.models.schemas import TranscriptSegment

client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided document content.
Always base your answers on the provided context. If the answer is not in the context, say so clearly.
For audio/video content, if referencing a specific part, mention the approximate timestamp."""

def _build_context(text_content: str, transcript_segments: Optional[List[dict]] = None) -> str:
    if transcript_segments:
        ctx = "=== TRANSCRIPT (with timestamps) ===\n"
        for seg in transcript_segments:
            ctx += f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}\n"
        return ctx
    return f"=== DOCUMENT CONTENT ===\n{text_content[:8000]}"

def _find_relevant_timestamp(answer: str, segments: List[dict]) -> Optional[dict]:
    """Find the most relevant segment based on keywords in the answer."""
    if not segments:
        return None
    answer_lower = answer.lower()
    best_segment = None
    best_score = 0
    for seg in segments:
        words = seg["text"].lower().split()
        score = sum(1 for w in words if len(w) > 4 and w in answer_lower)
        if score > best_score:
            best_score = score
            best_segment = seg
    return best_segment if best_score > 0 else segments[0]

async def chat_with_document(
    question: str,
    text_content: str,
    history: List[dict],
    transcript_segments: Optional[List[dict]] = None,
) -> dict:
    """Single-turn Q&A with document context."""
    context = _build_context(text_content, transcript_segments)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{context}\n\n---\nQuestion: {question}"},
    ]
    # Inject last 4 history messages for continuity
    if history:
        recent = history[-4:]
        messages = [messages[0]] + recent + [messages[-1]]

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        max_tokens=800,
    )
    answer = response.choices[0].message.content.strip()

    timestamp_ref = None
    relevant_segment = None
    if transcript_segments:
        seg = _find_relevant_timestamp(answer, transcript_segments)
        if seg:
            timestamp_ref = seg["start"]
            relevant_segment = seg

    return {
        "answer": answer,
        "timestamp_reference": timestamp_ref,
        "relevant_segment": relevant_segment,
    }

async def stream_chat_with_document(
    question: str,
    text_content: str,
    history: List[dict],
    transcript_segments: Optional[List[dict]] = None,
) -> AsyncGenerator[str, None]:
    """Streaming Q&A response."""
    context = _build_context(text_content, transcript_segments)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{context}\n\n---\nQuestion: {question}"},
    ]
    if history:
        recent = history[-4:]
        messages = [messages[0]] + recent + [messages[-1]]

    stream = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        max_tokens=800,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
