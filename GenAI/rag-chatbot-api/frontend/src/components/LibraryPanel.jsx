// LibraryPanel.jsx - The PDFs the chatbot can search (POST/GET/DELETE /api/v1/documents).
import { useRef, useState } from "react";
import * as api from "../api.js";
import { timeAgo } from "../format.js";
import { IconTrash, IconUpload } from "./icons.jsx";

export default function LibraryPanel({ documents, health, onChanged }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(null); // name of the file being indexed
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [armed, setArmed] = useState(null);

  async function upload(files) {
    setError(null);
    for (const file of files) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError(`${file.name} isn't a PDF. Only PDF files can be added.`);
        continue;
      }
      setUploading(file.name);
      try {
        await api.uploadDocument(file);
      } catch (e) {
        setError(`Couldn't add ${file.name}: ${e.message}`);
      }
    }
    setUploading(null);
    onChanged();
  }

  async function remove(id) {
    setArmed(null);
    try {
      await api.deleteDocument(id);
    } catch (e) {
      setError(e.message);
    }
    onChanged();
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    upload([...event.dataTransfer.files]);
  }

  return (
    <div className="library">
      <div
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {uploading ? (
          <p>Reading and indexing {uploading}…<br /><span className="quiet small">Large files can take a minute.</span></p>
        ) : (
          <>
            <button className="btn" onClick={() => inputRef.current.click()}>
              <IconUpload /> Upload PDF
            </button>
            <p className="quiet small">or drop files here, up to 25 MB each</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => { upload([...e.target.files]); e.target.value = ""; }}
        />
      </div>

      {error && <p className="msg-error" role="alert">{error}</p>}

      {documents.length === 0 ? (
        <p className="quiet">No documents yet. Upload a PDF and the chatbot will cite it in its answers.</p>
      ) : (
        <ul className="docs">
          {documents.map((d) => (
            <li key={d.id} className="doc">
              <div className="doc-info">
                <span className="doc-name" title={d.filename}>{d.filename}</span>
                <span className="quiet small">
                  {d.pages} pages, {d.chunks} chunks, added {timeAgo(d.created_at)}
                </span>
              </div>
              <button
                className={`session-delete ${armed === d.id ? "armed" : ""}`}
                onClick={() => (armed === d.id ? remove(d.id) : setArmed(d.id))}
                onBlur={() => setArmed(null)}
                aria-label={armed === d.id ? "Click again to delete" : `Delete ${d.filename}`}
              >
                {armed === d.id ? "Delete?" : <IconTrash />}
              </button>
            </li>
          ))}
        </ul>
      )}

      {health && (
        <dl className="status">
          <dt>Model</dt><dd>{health.model}</dd>
          <dt>Indexed chunks</dt><dd>{health.indexed_chunks}</dd>
          <dt>Reranker</dt><dd>{health.reranker ? "On" : "Off"}</dd>
        </dl>
      )}
    </div>
  );
}
