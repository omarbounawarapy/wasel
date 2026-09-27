import { useState, useEffect, useRef, useCallback } from "react";
import { getVisitorId } from "./visitor";

interface UsePollOptions<T> {
  intervalMs: number;
  fastWhile?: (data: T) => boolean;
  fastMs?: number;
  enabled?: boolean;
}

interface UsePollResult<T> {
  data: T | null;
  error: Error | null;
  failures: number;
  lastOkAt: number | null;
}

export function usePoll<T>(
  path: string,
  { intervalMs, fastWhile, fastMs, enabled = true }: UsePollOptions<T>
): UsePollResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [failures, setFailures] = useState(0);
  const [lastOkAt, setLastOkAt] = useState<number | null>(null);

  const dataRef = useRef(data);
  dataRef.current = data;
  // a ref, not state, drives the backoff: putting `failures` in the effect deps restarted the loop
  // (and refetched immediately) on every error
  const failuresRef = useRef(0);

  const fetchLoop = useCallback(async (signal: AbortSignal) => {
    try {
      const baseUrl = process.env.NODE_ENV === "development" ? "http://localhost:8000" : "";
      const url = path.startsWith("http") ? path : `${baseUrl}${path}`;
      
      const res = await fetch(url, {
        signal,
        headers: {
          "X-Visitor-Id": getVisitorId(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as T;
      if (signal.aborted) return;

      setData(json);
      setError(null);
      failuresRef.current = 0;
      setFailures(0);
      setLastOkAt(Date.now());
    } catch (err: any) {
      if (signal.aborted) return;
      setError(err);
      failuresRef.current += 1;
      setFailures(failuresRef.current);
    }
  }, [path]);

  useEffect(() => {
    if (!enabled) return;
    const ac = new AbortController();
    let timeoutId: ReturnType<typeof setTimeout>;
    let isRunning = true;

    const run = async () => {
      if (!isRunning) return;
      if (!document.hidden) {
        await fetchLoop(ac.signal);
      }
      
      if (!isRunning) return;

      let nextMs = intervalMs;
      if (fastWhile && fastMs && dataRef.current && fastWhile(dataRef.current)) {
        nextMs = fastMs;
      }
      
      if (failuresRef.current > 0) {
        nextMs = Math.min(10000, nextMs * Math.pow(1.5, failuresRef.current));
      }

      timeoutId = setTimeout(run, nextMs);
    };

    run();

    const handleVis = () => {
      if (!document.hidden && isRunning) {
        clearTimeout(timeoutId);
        run();
      }
    };
    document.addEventListener("visibilitychange", handleVis);

    return () => {
      isRunning = false;
      ac.abort();
      clearTimeout(timeoutId);
      document.removeEventListener("visibilitychange", handleVis);
    };
  }, [enabled, fetchLoop, intervalMs, fastWhile, fastMs]);

  return { data, error, failures, lastOkAt };
}
