"use client";

import { FormEvent, useEffect, useState } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api` : "/api";

/**
 * Asks for the access token when the server runs with API_TOKEN (event and dev modes) and this browser has no
 * session yet. The token goes to POST /api/session and comes back as an HttpOnly cookie; it is never stored here.
 */
export default function AccessGate() {
  const [needed, setNeeded] = useState(false);
  const [token, setToken] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${BASE}/session`, { credentials: "include" })
      .then((r) => r.json())
      .then((s) => setNeeded(Boolean(s.required) && !s.authenticated))
      .catch(() => {});
  }, []);

  if (!needed) return null;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    const r = await fetch(`${BASE}/session`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    if (r.ok) window.location.reload();
    else setError("That token was not accepted.");
  }

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="gate-title"
         className="fixed inset-0 z-50 flex items-center justify-center bg-background p-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4">
        <h1 id="gate-title" className="text-xl font-semibold">Access token</h1>
        <p className="text-sm text-muted-foreground">
          This server is not public. Enter the access token your administrator set as API_TOKEN.
        </p>
        <input type="password" autoFocus autoComplete="current-password" value={token}
               onChange={(e) => setToken(e.target.value)} aria-label="Access token"
               className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        <button type="submit" disabled={!token}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">
          Continue
        </button>
      </form>
    </div>
  );
}
