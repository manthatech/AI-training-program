// Sidebar.jsx - The list of conversations (GET /api/v1/sessions).
import { useState } from "react";
import { IconClose, IconPlus, IconTrash } from "./icons.jsx";
import { timeAgo } from "../format.js";

export default function Sidebar({ sessions, activeId, onOpen, onNew, onDelete, onClose }) {
  // Deleting asks once: the first click arms the button, the second click deletes.
  const [armed, setArmed] = useState(null);

  return (
    <aside className="sidebar" aria-label="Conversations">
      <div className="sidebar-head">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          RAG Chatbot
        </div>
        <button className="icon-btn only-narrow" onClick={onClose} aria-label="Close conversations">
          <IconClose />
        </button>
      </div>

      <button className="new-chat" onClick={onNew}>
        <IconPlus /> New conversation
      </button>

      <nav className="session-list">
        {sessions.length === 0 && <p className="quiet pad">Your conversations will be listed here.</p>}
        {sessions.map((s) => (
          <div key={s.id} className={`session ${s.id === activeId ? "active" : ""}`}>
            <button className="session-open" onClick={() => onOpen(s.id)} aria-current={s.id === activeId}>
              <span className="session-title">{s.title || "Untitled conversation"}</span>
              <span className="session-meta">
                {timeAgo(s.updated_at)}, {s.message_count} messages
              </span>
            </button>
            <button
              className={`session-delete ${armed === s.id ? "armed" : ""}`}
              onClick={() => (armed === s.id ? onDelete(s.id) : setArmed(s.id))}
              onBlur={() => setArmed(null)}
              aria-label={armed === s.id ? "Click again to delete" : "Delete conversation"}
              title={armed === s.id ? "Click again to delete" : "Delete conversation"}
            >
              {armed === s.id ? "Delete?" : <IconTrash />}
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
