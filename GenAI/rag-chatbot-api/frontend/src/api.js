// api.js - Every call to the FastAPI backend lives in this file.
// The components never call fetch() directly; they use these functions.

const BASE = import.meta.env.VITE_API_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "";

function headers(extra = {}) {
  return API_KEY ? { "X-API-Key": API_KEY, ...extra } : extra;
}

// Throw an Error with the backend's "detail" message, so the UI can show it.
async function check(response) {
  if (response.ok) return response;
  let detail = `${response.status} ${response.statusText}`;
  try {
    const body = await response.json();
    if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    // The body wasn't JSON; keep the status text.
  }
  throw new Error(detail);
}

async function getJSON(path) {
  const response = await check(await fetch(BASE + path, { headers: headers() }));
  return response.json();
}

async function sendJSON(method, path, body) {
  const response = await check(
    await fetch(BASE + path, {
      method,
      headers: headers({ "Content-Type": "application/json" }),
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  );
  return response.status === 204 ? null : response.json();
}

// ------------------------------------------------------------------ health
export const getHealth = () => getJSON("/health");

// ---------------------------------------------------------------- sessions
export const listSessions = () => getJSON("/api/v1/sessions");
export const getSession = (id) => getJSON(`/api/v1/sessions/${id}`);
export const getMessages = (id) => getJSON(`/api/v1/sessions/${id}/messages`);
export const deleteSession = (id) => sendJSON("DELETE", `/api/v1/sessions/${id}`);

// --------------------------------------------------------------- documents
export const listDocuments = () => getJSON("/api/v1/documents");
export const deleteDocument = (id) => sendJSON("DELETE", `/api/v1/documents/${id}`);

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const response = await check(
    await fetch(BASE + "/api/v1/documents", { method: "POST", headers: headers(), body: form }),
  );
  return response.json();
}

// -------------------------------------------------------------------- chat
// The stream endpoint sends Server-Sent Events, separated by a blank line:
//
//     event: token
//     data: "Hel"
//
// We read the response bit by bit, cut it into events, and call onEvent(name, data)
// for each one: session -> tool* -> token* -> sources? -> done   (or error).
export async function streamChat(message, sessionId, onEvent, signal) {
  const response = await check(
    await fetch(BASE + "/api/v1/chat/stream", {
      method: "POST",
      headers: headers({ "Content-Type": "application/json" }),
      body: JSON.stringify({ message, session_id: sessionId || null }),
      signal,
    }),
  );

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Every complete event ends with "\n\n". Keep any unfinished part in the buffer.
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop();
    for (const block of blocks) {
      const event = parseEvent(block);
      if (event) onEvent(event.name, event.data);
    }
  }
}

function parseEvent(block) {
  let name = "message";
  let data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) name = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return null;
  return { name, data: JSON.parse(data) };
}
