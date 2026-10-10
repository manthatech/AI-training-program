// Composer.jsx - The message box. Enter sends, Shift+Enter starts a new line.
import { useEffect, useRef, useState } from "react";
import { IconSend, IconStop } from "./icons.jsx";

export default function Composer({ onSend, onStop, sending }) {
  const [text, setText] = useState("");
  const boxRef = useRef(null);

  // Grow the box with its text, up to a limit (the CSS max-height).
  useEffect(() => {
    const box = boxRef.current;
    box.style.height = "auto";
    box.style.height = box.scrollHeight + "px";
  }, [text]);

  function submit(event) {
    event?.preventDefault();
    const message = text.trim();
    if (!message || sending) return;
    onSend(message);
    setText("");
  }

  function onKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) submit(event);
  }

  return (
    <form className="composer" onSubmit={submit}>
      <div className="composer-box">
        <textarea
          ref={boxRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a question"
          aria-label="Message"
          maxLength={8000}
          autoFocus
        />
        {sending ? (
          <button type="button" className="send stop" onClick={onStop} aria-label="Stop the reply">
            <IconStop />
          </button>
        ) : (
          <button type="submit" className="send" disabled={!text.trim()} aria-label="Send message">
            <IconSend />
          </button>
        )}
      </div>
      <p className="composer-hint">Enter to send, Shift + Enter for a new line</p>
    </form>
  );
}
