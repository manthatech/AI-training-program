// Margin.jsx - The right-hand panel, with three tabs:
//   Sources - the passages the selected answer was built from
//   Library - upload, list and delete PDFs (the RAG knowledge base)
//   Memory  - what the bot remembers about this conversation (summary + profile)
import { IconClose } from "./icons.jsx";
import SourcesPanel from "./SourcesPanel.jsx";
import LibraryPanel from "./LibraryPanel.jsx";
import MemoryPanel from "./MemoryPanel.jsx";

const TABS = [
  ["sources", "Sources"],
  ["library", "Library"],
  ["memory", "Memory"],
];

export default function Margin(props) {
  const { tab, onTab, onClose } = props;

  return (
    <aside className="margin" aria-label="Sources, library and memory">
      <div className="margin-head">
        <div className="tabs" role="tablist">
          {TABS.map(([id, label]) => (
            <button
              key={id}
              role="tab"
              aria-selected={tab === id}
              className={`tab ${tab === id ? "active" : ""}`}
              onClick={() => onTab(id)}
            >
              {label}
            </button>
          ))}
        </div>
        <button className="icon-btn only-medium" onClick={onClose} aria-label="Close panel">
          <IconClose />
        </button>
      </div>

      <div className="margin-body" role="tabpanel">
        {tab === "sources" && <SourcesPanel message={props.message} highlighted={props.highlighted} />}
        {tab === "library" && (
          <LibraryPanel documents={props.documents} health={props.health} onChanged={props.onDocumentsChanged} />
        )}
        {tab === "memory" && <MemoryPanel sessionId={props.sessionId} version={props.memoryVersion} />}
      </div>
    </aside>
  );
}
