"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Terminal, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSSE } from "@/hooks/useSSE";
import { getSSEUrl, getLogHistory } from "@/lib/api";
import type { LogEntry } from "@/lib/types";

export default function LogsPage() {
  const { id } = useParams<{ id: string }>();
  const [history, setHistory] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  const { events, clearEvents } = useSSE(getSSEUrl(id));

  // Live log events from SSE
  const liveLines = events
    .filter((e) => e.type === "log")
    .map((e) => e.data as { level: string; message: string });

  useEffect(() => {
    getLogHistory(id).then(setHistory).catch(console.error);
  }, [id]);

  useEffect(() => {
    if (autoScroll) {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [liveLines.length, autoScroll]);

  const levelColor = (level: string) => {
    if (level === "error") return "text-red-400";
    if (level === "warn") return "text-yellow-400";
    return "text-green-400";
  };

  const allLines = [
    ...history.map((l) => ({ level: l.level, message: l.message, ts: l.created_at })),
    ...liveLines.map((l) => ({ ...l, ts: new Date().toISOString() })),
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto p-8">
        <Link href={`/projects/${id}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Project
        </Link>

        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Terminal className="h-6 w-6" />
            Live Logs
          </h1>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded"
              />
              Auto-scroll
            </label>
            <Button variant="outline" size="sm" onClick={clearEvents}>
              <Trash2 className="h-3.5 w-3.5" />
              Clear live
            </Button>
          </div>
        </div>

        <Card className="bg-zinc-950 text-zinc-100 border-zinc-800">
          <CardHeader className="border-b border-zinc-800 pb-3">
            <CardTitle className="text-xs font-mono text-zinc-400 uppercase tracking-widest">
              {allLines.length} lines
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[60vh] overflow-y-auto p-4 font-mono text-xs space-y-0.5">
              {allLines.length === 0 && (
                <p className="text-zinc-600 italic">Waiting for logs...</p>
              )}
              {allLines.map((line, i) => (
                <div key={i} className="flex gap-3">
                  <span className="text-zinc-600 select-none w-8 text-right flex-shrink-0">{i + 1}</span>
                  <span className={levelColor(line.level)}>{line.message}</span>
                </div>
              ))}
              <div ref={endRef} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
