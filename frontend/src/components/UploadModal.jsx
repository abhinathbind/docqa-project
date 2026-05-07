import React, { useState, useRef } from "react";
import { api } from "../services/api";

const ACCEPTED = ".pdf,.mp3,.wav,.m4a,.mp4,.mov,.avi";
const FILE_ICONS = {
  pdf: "📄",
  mp3: "🎵", wav: "🎵", m4a: "🎵",
  mp4: "🎬", mov: "🎬", avi: "🎬",
};

function getExt(name) {
  return name.split(".").pop().toLowerCase();
}

export function UploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef();

  const handleFile = (f) => {
    setError("");
    setFile(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(30);
    try {
      const result = await api.uploadFile(file);
      setProgress(100);
      if (result.error) {
        setError(result.detail || "Upload failed");
      } else {
        setTimeout(onSuccess, 400);
      }
    } catch (err) {
      setError("Upload failed. Is the backend running?");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-title">Upload a File</div>

        <div
          className={`dropzone ${dragOver ? "drag-over" : ""}`}
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            style={{ display: "none" }}
            onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
          />
          {file ? (
            <>
              <div className="dropzone-icon">{FILE_ICONS[getExt(file.name)] || "📁"}</div>
              <div className="dropzone-text" style={{ color: "var(--text)" }}>{file.name}</div>
              <div className="dropzone-hint">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
            </>
          ) : (
            <>
              <div className="dropzone-icon">⬆</div>
              <div className="dropzone-text">Drag & drop or click to browse</div>
              <div className="dropzone-hint">PDF · MP3 · WAV · M4A · MP4 · MOV · AVI · Max 100MB</div>
            </>
          )}
        </div>

        {uploading && (
          <div className="progress-bar-wrap">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
        )}

        {error && (
          <div style={{ color: "var(--error)", fontSize: 12, marginTop: 12, fontFamily: "var(--font-mono)" }}>
            {error}
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button
            className="upload-btn"
            style={{ padding: "8px 20px", fontSize: 13 }}
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? "Uploading…" : "Upload"}
          </button>
        </div>
      </div>
    </div>
  );
}
