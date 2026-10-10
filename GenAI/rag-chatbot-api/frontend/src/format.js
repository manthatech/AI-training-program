// format.js - Small helpers for turning backend data into text for the screen.

// "2026-10-02T13:30:00+00:00" -> "3 min ago", "yesterday", "Oct 2"
export function timeAgo(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  const seconds = (Date.now() - date.getTime()) / 1000;
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
  if (seconds < 172800) return "yesterday";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// "kestrel-gadgets-customer-handbook.pdf" -> "kestrel-gadgets-custom…"
export function shortName(filename, max = 22) {
  const name = filename.replace(/\.pdf$/i, "");
  return name.length > max ? name.slice(0, max - 1) + "…" : name;
}

// What the user sees for each backend tool.
export const TOOL_LABELS = {
  search_documents: "Searched documents",
  save_memory: "Saved a note",
  calculator: "Calculated",
  get_current_time: "Checked the time",
};

// The LLM cites passages like [handbook.pdf p.4]. Turn each one into a markdown link
// "cite:handbook.pdf|4" so the Message component can draw it as a clickable citation.
const CITATION = /\[([^\[\]\n]+?\.pdf) p\.(\d+)\]/gi;

export function linkCitations(text) {
  return text.replace(CITATION, (_, file, page) => `[${file} p.${page}](cite:${encodeURIComponent(file)}|${page})`);
}

export function parseCitation(href) {
  // The markdown renderer may re-encode the link (e.g. "|" -> "%7C"), so decode first.
  const raw = decodeURIComponent(href.slice("cite:".length));
  const split = raw.lastIndexOf("|");
  return { filename: raw.slice(0, split), page: Number(raw.slice(split + 1)) };
}
