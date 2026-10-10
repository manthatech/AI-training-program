// Small line icons, drawn inline so we don't need an icon library.
const base = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

export const IconPlus = () => (
  <svg {...base}><path d="M12 5v14M5 12h14" /></svg>
);
export const IconTrash = () => (
  <svg {...base}><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" /></svg>
);
export const IconClose = () => (
  <svg {...base}><path d="M6 6l12 12M18 6L6 18" /></svg>
);
export const IconMenu = () => (
  <svg {...base}><path d="M4 7h16M4 12h16M4 17h10" /></svg>
);
export const IconPanel = () => (
  <svg {...base}><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M15 4v16" /></svg>
);
export const IconSend = () => (
  <svg {...base}><path d="M5 12h13M13 6l6 6-6 6" /></svg>
);
export const IconStop = () => (
  <svg {...base}><rect x="7" y="7" width="10" height="10" rx="1.5" /></svg>
);
export const IconUpload = () => (
  <svg {...base}><path d="M12 16V4M7 9l5-5 5 5M5 20h14" /></svg>
);
export const IconRefresh = () => (
  <svg {...base}><path d="M20 11a8 8 0 1 0-2.3 5.7M20 5v6h-6" /></svg>
);

// One icon per backend tool, shown next to "Searched documents" etc.
export const IconSearch = () => (
  <svg {...base}><circle cx="11" cy="11" r="6" /><path d="M20 20l-4.5-4.5" /></svg>
);
export const IconBookmark = () => (
  <svg {...base}><path d="M7 4h10v16l-5-4-5 4z" /></svg>
);
export const IconCalc = () => (
  <svg {...base}><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M8 7h8M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01" /></svg>
);
export const IconClock = () => (
  <svg {...base}><circle cx="12" cy="12" r="8" /><path d="M12 8v4l3 2" /></svg>
);
