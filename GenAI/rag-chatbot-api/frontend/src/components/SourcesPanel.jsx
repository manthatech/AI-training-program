// SourcesPanel.jsx - The passages behind an answer. The cited one is highlighted.
import { useEffect, useRef } from "react";

export default function SourcesPanel({ message, highlighted }) {
  const refs = useRef([]);

  // Scroll the clicked citation's passage into view.
  useEffect(() => {
    if (highlighted != null) refs.current[highlighted]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [highlighted, message?.id]);

  const sources = message?.sources || [];
  if (sources.length === 0) {
    return (
      <p className="quiet">
        When an answer uses your documents, the passages it was built from appear here. Click a citation in the answer
        to jump to its passage.
      </p>
    );
  }

  return (
    <ol className="sources">
      {sources.map((s, i) => (
        <li key={`${s.doc_id}-${s.page}-${i}`} ref={(el) => (refs.current[i] = el)} className={`source ${i === highlighted ? "active" : ""}`}>
          <div className="source-head">
            <span className="source-file" title={s.filename}>{s.filename}</span>
            <span className="source-page">p.{s.page}</span>
          </div>
          <p className="source-text">{s.text || s.snippet}</p>
          <p className="source-scores">
            Similarity {s.score?.toFixed(2)}
            {s.rerank_score != null && <>, rerank {s.rerank_score.toFixed(1)}</>}
          </p>
        </li>
      ))}
    </ol>
  );
}
