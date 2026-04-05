"use client";

import { useEffect, useRef, useState } from "react";
import type { SSEEvent } from "@/lib/types";

export function useSSE(url: string | null) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!url) return;

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const event: SSEEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, event]);
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      // EventSource auto-reconnects; no action needed
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [url]);

  const clearEvents = () => setEvents([]);

  return { events, clearEvents };
}
