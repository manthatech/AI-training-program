// Message.jsx - One message. Assistant replies are rendered as markdown, and every
// citation like [handbook.pdf p.4] becomes a highlighted button that opens the source.
import Markdown, { defaultUrlTransform } from "react-markdown";
import { linkCitations, parseCitation, shortName, TOOL_LABELS } from "../format.js";
import { IconBookmark, IconCalc, IconClock, IconSearch } from "./icons.jsx";

const TOOL_ICONS = {
  search_documents: IconSearch,
  save_memory: IconBookmark,
  calculator: IconCalc,
  get_current_time: IconClock,
};

export default function Message({ message, focus, onCite }) {
  if (message.role === "user") {
    return (
      <div className="msg msg-user">
        <p>{message.content}</p>
      </div>
    );
  }

  const sources = message.sources || [];
  const tools = message.tool_calls || [];
  const isFocused = focus.messageId === message.id;

  // Find which source a citation points to (same file and page).
  function citationIndex(filename, page) {
    return sources.findIndex((s) => s.filename === filename && s.page === page);
  }

  const components = {
    a({ href, children }) {
      if (!href?.startsWith("cite:")) {
        return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
      }
      const { filename, page } = parseCitation(href);
      const index = citationIndex(filename, page);
      const active = isFocused && index !== -1 && focus.sourceIndex === index;
      return (
        <button
          className={`cite ${active ? "active" : ""}`}
          onClick={() => onCite(message.id, index === -1 ? null : index)}
          title={`${filename}, page ${page}`}
        >
          {shortName(filename)} p.{page}
        </button>
      );
    },
  };

  return (
    <div className="msg msg-bot">
      {tools.length > 0 && (
        <ul className="tools" aria-label="Tools used">
          {tools.map((t, i) => {
            const Icon = TOOL_ICONS[t.name] || IconSearch;
            return (
              <li key={i} className={`tool ${t.ok === false ? "failed" : ""}`} title={JSON.stringify(t.args)}>
                <Icon />
                <span>{TOOL_LABELS[t.name] || t.name}</span>
                <span className="tool-arg">{Object.values(t.args || {})[0]}</span>
              </li>
            );
          })}
        </ul>
      )}

      <div className="answer">
        {message.content ? (
          <Markdown
            components={components}
            urlTransform={(url) => (url.startsWith("cite:") ? url : defaultUrlTransform(url))}
          >
            {linkCitations(message.content)}
          </Markdown>
        ) : (
          message.streaming && <span className="thinking">Thinking</span>
        )}
        {message.streaming && message.content && <span className="caret" aria-hidden="true" />}
      </div>

      {message.error && <p className="msg-error">The reply failed: {message.error}</p>}
      {message.stopped && <p className="quiet small">Stopped.</p>}

      {sources.length > 0 && !message.streaming && (
        <button className="sources-link" onClick={() => onCite(message.id, null)}>
          {sources.length} {sources.length === 1 ? "source" : "sources"}
        </button>
      )}
    </div>
  );
}
