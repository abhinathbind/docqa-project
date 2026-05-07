import React, { useEffect, useState } from "react";
import { api } from "../services/api";

const FILE_ICONS = { pdf: "📄", audio: "🎵", video: "🎬" };

export function FileLibrary({ selectedDoc, onSelect }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await api.listFiles();
        if (!cancelled) setFiles(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setFiles([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    // Poll for processing status
    const interval = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  if (loading) {
    return (
      <div className="file-library">
        <div className="file-library-empty">Loading files...</div>
      </div>
    );
  }

  return (
    <div className="file-library">
      <div className="library-label">Documents</div>
      {files.length === 0 ? (
        <div className="file-library-empty">
          No files yet.<br />Upload a PDF, audio, or video to get started.
        </div>
      ) : (
        files.map((f) => (
          <div
            key={f.id}
            className={`file-item ${selectedDoc?.id === f.id ? "active" : ""}`}
            onClick={() => f.status === "ready" && onSelect(f)}
          >
            <span className="file-icon">{FILE_ICONS[f.file_type] || "📁"}</span>
            <div className="file-info">
              <div className="file-name" title={f.filename}>{f.filename}</div>
              <div className="file-meta">{f.file_type.toUpperCase()}</div>
            </div>
            <span className={`file-status ${f.status}`}>{f.status}</span>
          </div>
        ))
      )}
    </div>
  );
}
