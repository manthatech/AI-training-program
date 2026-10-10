// App.jsx - The whole screen, and the state shared between its parts.
//
//   ┌────────────┬──────────────────────────┬──────────────┐
//   │ Sidebar    │ Thread + Composer        │ Margin       │
//   │ (sessions) │ (the conversation)       │ sources /    │
//   │            │                          │ library /    │
//   │            │                          │ memory       │
//   └────────────┴──────────────────────────┴──────────────┘
//
// Sending a message (send() below):
//   1. show the user's message and an empty assistant message right away
//   2. stream the reply from /api/v1/chat/stream, filling the assistant message in
//   3. when the stream says "done", refresh the session list (the title may be new)
import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "./api.js";
import Sidebar from "./components/Sidebar.jsx";
import Thread from "./components/Thread.jsx";
import Composer from "./components/Composer.jsx";
import Margin from "./components/Margin.jsx";
import { IconMenu, IconPanel } from "./components/icons.jsx";

let localId = 0;
const nextId = () => `local-${++localId}`;

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingThread, setLoadingThread] = useState(false);
  const [sending, setSending] = useState(false);

  const [documents, setDocuments] = useState([]);
  const [health, setHealth] = useState(null);
  const [backendError, setBackendError] = useState(null);

  // Which assistant message's sources the margin shows, and which source is highlighted.
  const [focus, setFocus] = useState({ messageId: null, sourceIndex: null });
  const [marginTab, setMarginTab] = useState("sources");
  const [memoryVersion, setMemoryVersion] = useState(0); // bump to make the memory tab reload

  // On small screens the sidebar and margin are drawers.
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [marginOpen, setMarginOpen] = useState(false);

  const abortRef = useRef(null);

  // ------------------------------------------------------------- loading data
  const refreshSessions = useCallback(async () => {
    try {
      setSessions(await api.listSessions());
      setBackendError(null);
    } catch (error) {
      setBackendError(error.message);
    }
  }, []);

  const refreshDocuments = useCallback(async () => {
    try {
      const [docs, status] = await Promise.all([api.listDocuments(), api.getHealth()]);
      setDocuments(docs);
      setHealth(status);
    } catch (error) {
      setBackendError(error.message);
    }
  }, []);

  useEffect(() => {
    refreshSessions();
    refreshDocuments();
  }, [refreshSessions, refreshDocuments]);

  async function openSession(id) {
    abortRef.current?.abort();
    setSidebarOpen(false);
    setActiveId(id);
    setFocus({ messageId: null, sourceIndex: null });
    setMessages([]);
    setLoadingThread(true);
    try {
      setMessages(await api.getMessages(id));
    } catch (error) {
      setBackendError(error.message);
    } finally {
      setLoadingThread(false);
    }
  }

  function startNewChat() {
    abortRef.current?.abort();
    setSidebarOpen(false);
    setActiveId(null);
    setMessages([]);
    setFocus({ messageId: null, sourceIndex: null });
  }

  async function removeSession(id) {
    await api.deleteSession(id);
    if (id === activeId) startNewChat();
    refreshSessions();
  }

  // ------------------------------------------------------------------ sending
  // Change one message in the list (found by id) without touching the others.
  function updateMessage(id, change) {
    setMessages((list) => list.map((m) => (m.id === id ? { ...m, ...change(m) } : m)));
  }

  async function send(text) {
    const userMsg = { id: nextId(), role: "user", content: text };
    const botId = nextId();
    const botMsg = { id: botId, role: "assistant", content: "", sources: [], tool_calls: [], streaming: true };
    setMessages((list) => [...list, userMsg, botMsg]);
    setSending(true);

    const controller = new AbortController();
    abortRef.current = controller;
    let sessionId = activeId;

    try {
      await api.streamChat(
        text,
        activeId,
        (event, data) => {
          if (event === "session") {
            sessionId = data.session_id;
            setActiveId(sessionId);
          } else if (event === "tool") {
            updateMessage(botId, (m) => ({ tool_calls: [...m.tool_calls, { ...data, ok: true }] }));
          } else if (event === "token") {
            updateMessage(botId, (m) => ({ content: m.content + data }));
          } else if (event === "sources") {
            updateMessage(botId, () => ({ sources: data }));
            setFocus({ messageId: botId, sourceIndex: null });
          } else if (event === "done") {
            updateMessage(botId, () => ({ tool_calls: data.tool_calls, streaming: false }));
          } else if (event === "error") {
            updateMessage(botId, () => ({ error: data.detail, streaming: false }));
          }
        },
        controller.signal,
      );
    } catch (error) {
      const stopped = error.name === "AbortError";
      updateMessage(botId, () => ({ error: stopped ? null : error.message, stopped, streaming: false }));
    } finally {
      updateMessage(botId, () => ({ streaming: false }));
      setSending(false);
      abortRef.current = null;
      refreshSessions();
      // The summary and profile are updated just after the reply finishes, so wait a moment.
      if (sessionId) setTimeout(() => setMemoryVersion((v) => v + 1), 2500);
    }
  }

  function stop() {
    abortRef.current?.abort();
  }

  // ---------------------------------------------------------------- citations
  function showSources(messageId, sourceIndex = null) {
    setFocus({ messageId, sourceIndex });
    setMarginTab("sources");
    setMarginOpen(true);
  }

  function openLibrary() {
    setMarginTab("library");
    setMarginOpen(true);
  }

  // The margin shows the focused message's sources, or else the latest message that has some.
  const focusedMessage =
    messages.find((m) => m.id === focus.messageId) ||
    [...messages].reverse().find((m) => m.role === "assistant" && m.sources?.length);

  const activeTitle = sessions.find((s) => s.id === activeId)?.title;

  return (
    <div className={`app ${sidebarOpen ? "sidebar-open" : ""} ${marginOpen ? "margin-open" : ""}`}>
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onOpen={openSession}
        onNew={startNewChat}
        onDelete={removeSession}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="main">
        <header className="topbar">
          <button className="icon-btn only-narrow" onClick={() => setSidebarOpen(true)} aria-label="Show conversations">
            <IconMenu />
          </button>
          <h1 className="topbar-title">{activeId ? activeTitle || "Conversation" : "New conversation"}</h1>
          <button className="icon-btn only-medium" onClick={() => setMarginOpen(true)} aria-label="Show sources, library and memory">
            <IconPanel />
          </button>
        </header>

        {backendError && (
          <div className="banner" role="alert">
            Can't reach the backend: {backendError}. Start it with <code>uvicorn app.main:app --reload</code> in the{" "}
            <code>backend</code> folder, then{" "}
            <button className="link-btn" onClick={() => { refreshSessions(); refreshDocuments(); }}>
              try again
            </button>
            .
          </div>
        )}

        <Thread
          messages={messages}
          loading={loadingThread}
          documents={documents}
          focus={focus}
          onCite={showSources}
          onSuggest={send}
          onOpenLibrary={openLibrary}
        />
        <Composer onSend={send} onStop={stop} sending={sending} />
      </main>

      <Margin
        tab={marginTab}
        onTab={setMarginTab}
        onClose={() => setMarginOpen(false)}
        message={focusedMessage}
        highlighted={focusedMessage?.id === focus.messageId ? focus.sourceIndex : null}
        documents={documents}
        health={health}
        onDocumentsChanged={refreshDocuments}
        sessionId={activeId}
        memoryVersion={memoryVersion}
      />

      <div className="scrim" onClick={() => { setSidebarOpen(false); setMarginOpen(false); }} />
    </div>
  );
}
