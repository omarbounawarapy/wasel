// Visitor id for the public demo's sandbox (06 §1.2): a uuid v4 in localStorage["cod_visitor_id"],
// sent as X-Visitor-Id on every /api call. Falls back to a per-tab id when storage is blocked.
let memoryId: string | null = null;

function uuidv4(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  // crypto.randomUUID needs a secure context (https or localhost); build a v4 from getRandomValues instead.
  const b = new Uint8Array(16);
  crypto.getRandomValues(b);
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = [...b].map(x => x.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

export function getVisitorId(): string {
  if (typeof window === "undefined") return "";
  try {
    let id = localStorage.getItem("cod_visitor_id");
    if (!id) {
      id = uuidv4();
      localStorage.setItem("cod_visitor_id", id);
    }
    return id;
  } catch {
    memoryId = memoryId ?? uuidv4();
    return memoryId;
  }
}
