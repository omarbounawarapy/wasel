/** The snapshot endpoint the container reaches at http://state.wasel.internal/snapshot, backed by an R2 bucket. */

export const SNAPSHOT_KEY = "wasel.sqlite";
export const SNAPSHOT_PREV_KEY = "wasel.sqlite.prev";
export const MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024;
const SQLITE_MAGIC = "SQLite format 3\u0000";

/** The part of R2Bucket used here (lets tests pass a fake). */
export interface Store {
  get(key: string): Promise<{ arrayBuffer(): Promise<ArrayBuffer> } | null>;
  put(key: string, value: ArrayBuffer): Promise<unknown>;
}

export async function handleSnapshot(req: Request, store: Store): Promise<Response> {
  if (new URL(req.url).pathname !== "/snapshot") return new Response("not found", { status: 404 });
  if (req.method === "GET") {
    const obj = await store.get(SNAPSHOT_KEY);
    if (!obj) return new Response(null, { status: 404 });
    return new Response(await obj.arrayBuffer(), { headers: { "Content-Type": "application/vnd.sqlite3" } });
  }
  if (req.method === "PUT") {
    const body = await req.arrayBuffer();
    if (body.byteLength > MAX_SNAPSHOT_BYTES) return new Response("snapshot too large", { status: 413 });
    if (new TextDecoder("latin1").decode(body.slice(0, SQLITE_MAGIC.length)) !== SQLITE_MAGIC) {
      return new Response("not a SQLite image", { status: 400 });
    }
    const current = await store.get(SNAPSHOT_KEY); // keep one generation back
    if (current) await store.put(SNAPSHOT_PREV_KEY, await current.arrayBuffer());
    await store.put(SNAPSHOT_KEY, body);
    return new Response(null, { status: 204 });
  }
  return new Response("method not allowed", { status: 405 });
}
