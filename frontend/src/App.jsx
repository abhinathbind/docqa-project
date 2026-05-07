import React, { useState } from "react";
import { FileLibrary } from "./components/FileLibrary";
import { ChatPanel } from "./components/ChatPanel";
import { UploadModal } from "./components/UploadModal";
import "./App.css";

export default function App() {
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setShowUpload(false);
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">◈</span>
            <span className="logo-text">DocQA</span>
          </div>
          <button className="upload-btn" onClick={() => setShowUpload(true)}>
            + Upload
          </button>
        </div>
        <FileLibrary
          key={refreshKey}
          selectedDoc={selectedDoc}
          onSelect={setSelectedDoc}
        />
      </aside>

      <main className="main">
        {selectedDoc ? (
          <ChatPanel doc={selectedDoc} />
        ) : (
          <div className="empty-state">
            <div className="empty-icon">◈</div>
            <h2>Select a document to start chatting</h2>
            <p>Upload PDFs, audio, or video files and ask questions about them.</p>
            <button className="upload-btn-large" onClick={() => setShowUpload(true)}>
              Upload your first file
            </button>
          </div>
        )}
      </main>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={handleUploadSuccess}
        />
      )}
    </div>
  );
}
