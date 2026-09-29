// Run with `npm test` (node --test). Covers the pure parts of the Worker; the Container class itself needs workerd.
import assert from "node:assert/strict";
import { test } from "node:test";
import { handleSnapshot, SNAPSHOT_KEY, SNAPSHOT_PREV_KEY, type Store } from "./snapshot.ts";

function fakeStore() {
  const m = new Map<string, ArrayBuffer>();
  const store: Store = {
    async get(k) {
      const v = m.get(k);
      return v ? { arrayBuffer: async () => v } : null;
    },
    async put(k, v) {
      m.set(k, v);
    },
  };
  return { m, store };
}
const bytes = (s: string) => new TextEncoder().encode(s).buffer as ArrayBuffer;
const img = (tail: string) => bytes("SQLite format 3\u0000" + tail);
const call = (store: Store, method: string, path = "/snapshot", body?: ArrayBuffer) =>
  handleSnapshot(new Request("http://state.wasel.internal" + path, { method, body }), store);

test("GET is 404 before the first snapshot", async () => {
  assert.equal((await call(fakeStore().store, "GET")).status, 404);
});

test("PUT stores, GET returns it, second PUT keeps one generation back", async () => {
  const { m, store } = fakeStore();
  assert.equal((await call(store, "PUT", "/snapshot", img("one"))).status, 204);
  assert.deepEqual(new Uint8Array(await (await call(store, "GET")).arrayBuffer()), new Uint8Array(img("one")));
  await call(store, "PUT", "/snapshot", img("two"));
  assert.deepEqual(new Uint8Array(m.get(SNAPSHOT_PREV_KEY)!), new Uint8Array(img("one")));
  assert.deepEqual(new Uint8Array(m.get(SNAPSHOT_KEY)!), new Uint8Array(img("two")));
});

test("rejects things that are not a SQLite image, other paths and other methods", async () => {
  const { m, store } = fakeStore();
  assert.equal((await call(store, "PUT", "/snapshot", bytes("hello"))).status, 400);
  assert.equal(m.size, 0);
  assert.equal((await call(store, "GET", "/other")).status, 404);
  assert.equal((await call(store, "DELETE")).status, 405);
});
