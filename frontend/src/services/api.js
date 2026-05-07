const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const getHeaders = () => {
  const token = localStorage.getItem("token");
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export const api = {
  async uploadFile(file, onProgress) {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE_URL}/files/upload`, {
      method: "POST",
      headers: getHeaders(),
      body: form,
    }).then((r) => r.json());
  },

  async listFiles() {
    const r = await fetch(`${BASE_URL}/files/`, { headers: getHeaders() });
    return r.json();
  },

  async getFile(id) {
    const r = await fetch(`${BASE_URL}/files/${id}`, { headers: getHeaders() });
    return r.json();
  },

  async deleteFile(id) {
    const r = await fetch(`${BASE_URL}/files/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    return r.json();
  },

  async chat(documentId, message, sessionId = null) {
    const r = await fetch(`${BASE_URL}/chat/`, {
      method: "POST",
      headers: { ...getHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId, message, session_id: sessionId }),
    });
    return r.json();
  },

  streamChat(documentId, message, sessionId, onToken, onDone) {
    fetch(`${BASE_URL}/chat/stream`, {
      method: "POST",
      headers: { ...getHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId, message, session_id: sessionId }),
    }).then(async (resp) => {
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let newSessionId = sessionId;
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "session") newSessionId = data.session_id;
            else if (data.type === "token") onToken(data.content);
            else if (data.type === "done") onDone(newSessionId);
          } catch {}
        }
      }
    });
  },

  async health() {
    const r = await fetch(`${BASE_URL}/health`);
    return r.json();
  },
};
