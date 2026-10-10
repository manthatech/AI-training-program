// Thread.jsx - The conversation, or a starting screen when there are no messages yet.
import { useEffect, useRef } from "react";
import Message from "./Message.jsx";
import { shortName } from "../format.js";

export default function Thread({ messages, loading, documents, focus, onCite, onSuggest, onOpenLibrary }) {
  const endRef = useRef(null);
  const last = messages[messages.length - 1];

  // Keep the newest text in view while the reply streams in.
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length, last?.content]);

  if (loading) {
    return <div className="thread"><p className="quiet center">Loading conversation…</p></div>;
  }

  if (messages.length === 0) {
    return (
      <div className="thread">
        <Welcome documents={documents} onSuggest={onSuggest} onOpenLibrary={onOpenLibrary} />
      </div>
    );
  }

  return (
    <div className="thread" aria-live="polite">
      <div className="thread-inner">
        {messages.map((m) => (
          <Message key={m.id} message={m} focus={focus} onCite={onCite} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}

function Welcome({ documents, onSuggest, onOpenLibrary }) {
  const first = documents[0];
  const suggestions = first
    ? [
        `What topics does ${shortName(first.filename, 40)} cover?`,
        "What is the refund policy?",
        "What time is it in Tokyo right now?",
      ]
    : ["What can you help me with?", "Calculate 18% of 2,450", "What time is it in London?"];

  return (
    <div className="welcome">
      <h2 className="welcome-title">Ask about your documents</h2>
      {first ? (
        <p className="welcome-text">
          Answers come from the {documents.length === 1 ? "PDF" : `${documents.length} PDFs`} in your library, with a
          citation for every claim. Click a citation to read the passage it came from.
        </p>
      ) : (
        <p className="welcome-text">
          Your library is empty, so answers can only use general knowledge.{" "}
          <button className="link-btn" onClick={onOpenLibrary}>Upload a PDF</button> to get answers with citations.
        </p>
      )}
      <div className="suggestions">
        {suggestions.map((s) => (
          <button key={s} className="suggestion" onClick={() => onSuggest(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
