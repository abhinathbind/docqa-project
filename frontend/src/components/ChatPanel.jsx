import React, { useState, useRef, useEffect, useCallback } from "react";
import { api } from "../services/api";

const FILE_ICONS = { pdf: "📄", audio: "🎵", video: "🎬" };

function formatTime(secs) {
  if (!secs && secs !== 0) return null;
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function Message({ msg, onPlayTimestamp }) {
  return (
    <div className={`message ${msg.role}`}>
      <div className="message-avatar">
        {msg.role === "user" ? "👤" : "◈"}
      </div>
      <div className="message-body">
        <div className="message-content">
          {msg.content}
        </div>
        {msg.role === "assistant" && msg.timestamp_reference != null && (
          <div
            className="timestamp-badge"
            onClick={() => onPlayTimestamp(msg.timestamp_reference)}
          >
            ▶ Jump to {formatTime(msg.timestamp_reference)}
          </div>
        )}
      </div>
    </div>
  );
}

export function ChatPanel({ doc }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [streamingText, setStreamingText] = useState("");
  const messagesEndRef = useRef(null);
  const mediaRef = useRef(null);
  const fileUrl = `http://localhost:8000/uploads/${doc.filename}`;

  useEffect(() => {
    setMessages([]);
    setSessionId(null);
    setStreamingText("");
  }, [doc.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  const handlePlayTimestamp = useCallback((secs) => {
    if (mediaRef.current) {
      mediaRef.current.currentTime = secs;
      mediaRef.current.play();
    }
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input, id: Date.now() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    setStreamingText("");

    let accumulated = "";
    api.streamChat(
      doc.id,
      userMsg.content,
      sessionId,
      (token) => {
        accumulated += token;
        setStreamingText(accumulated);
      },
      (newSessionId) => {
        setSessionId(newSessionId);
        setMessages((m) => [...m, {
          role: "assistant",
          content: accumulated,
          id: Date.now(),
          timestamp_reference: null,
        }]);
        setStreamingText("");
        setLoading(false);
      }
    );
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <span className="chat-header-icon">{FILE_ICONS[doc.file_type]}</span>
        <div className="chat-header-info">
          <div className="chat-header-title">{doc.filename}</div>
          {doc.summary && (
            <div className="chat-header-summary">{doc.summary}</div>
          )}
        </div>
      </div>

      {/* Media player for audio/video */}
      {(doc.file_type === "audio" || doc.file_type === "video") && (
        <div className="media-player">
          {doc.file_type === "audio" ? (
            <audio ref={mediaRef} controls src={fileUrl} />
          ) : (
            <video ref={mediaRef} controls src={fileUrl} style={{ maxHeight: 200 }} />
          )}
        </div>
      )}

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 && !loading && (
          <div style={{ textAlign: "center", color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: 13, marginTop: 32 }}>
            Ask anything about this {doc.file_type}…
          </div>
        )}
        {messages.map((msg) => (
          <Message key={msg.id} msg={msg} onPlayTimestamp={handlePlayTimestamp} />
        ))}
        {streamingText && (
          <div className="message assistant">
            <div className="message-avatar">◈</div>
            <div className="message-body">
              <div className="message-content">{streamingText}</div>
            </div>
          </div>
        )}
        {loading && !streamingText && (
          <div className="message assistant">
            <div className="message-avatar">◈</div>
            <div className="message-body">
              <div className="message-content">
                <div className="typing-dots">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <div className="chat-input-row">
          <textarea
            className="chat-input"
            placeholder={`Ask about ${doc.filename}…`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={loading}
          />
          <button className="send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
