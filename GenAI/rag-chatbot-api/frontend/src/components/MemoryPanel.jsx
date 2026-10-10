// MemoryPanel.jsx - What the bot remembers about the open conversation
// (GET /api/v1/sessions/{id}): turn count, running summary and the user profile.
import { useEffect, useState } from "react";
import * as api from "../api.js";
import { IconRefresh } from "./icons.jsx";

export default function MemoryPanel({ sessionId, version }) {
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    api
      .getSession(sessionId)
      .then((s) => !cancelled && (setSession(s), setError(null)))
      .catch((e) => !cancelled && setError(e.message));
    return () => { cancelled = true; };
  }, [sessionId, version, reload]);

  if (!sessionId) {
    return <p className="quiet">Start a conversation and this tab shows what the chatbot remembers about it.</p>;
  }
  if (error) return <p className="msg-error">{error}</p>;
  if (!session) return <p className="quiet">Loading…</p>;

  // Only show the profile fields the bot has actually filled in.
  const profile = Object.entries(session.profile || {}).filter(
    ([, value]) => value != null && value !== "" && !(Array.isArray(value) && value.length === 0),
  );

  return (
    <div className="memory">
      <div className="memory-head">
        <p>
          <strong>{session.turn}</strong> {session.turn === 1 ? "turn" : "turns"} so far. The last{" "}
          {session.recent_turns} are sent to the model word for word.
        </p>
        <button className="icon-btn" onClick={() => setReload((n) => n + 1)} aria-label="Refresh memory">
          <IconRefresh />
        </button>
      </div>

      <h3 className="panel-heading">Summary of older turns</h3>
      <p className={session.summary ? "memory-summary" : "quiet"}>
        {session.summary || "Nothing yet. Turns are summarized once they fall outside the recent window."}
      </p>

      <h3 className="panel-heading">About you</h3>
      {profile.length === 0 ? (
        <p className="quiet">Nothing yet. Mention your name, role or goals and they'll be noted here.</p>
      ) : (
        <dl className="profile">
          {profile.map(([key, value]) => (
            <div key={key}>
              <dt>{key.replace(/_/g, " ")}</dt>
              <dd>{Array.isArray(value) ? value.join(", ") : String(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
