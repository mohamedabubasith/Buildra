"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Play, Loader2, CheckCircle2, XCircle, Clock, ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getTickets, executeProject } from "@/lib/api";
import { getSSEUrl } from "@/lib/api";
import { useSSE } from "@/hooks/useSSE";
import type { Ticket } from "@/lib/types";

const statusIcon = {
  pending: <Clock className="h-3.5 w-3.5 text-muted-foreground" />,
  in_progress: <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />,
  done: <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />,
  failed: <XCircle className="h-3.5 w-3.5 text-destructive" />,
};

const statusBadge = {
  pending: "secondary" as const,
  in_progress: "default" as const,
  done: "success" as const,
  failed: "destructive" as const,
};

export default function TicketsPage() {
  const { id } = useParams<{ id: string }>();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const { events } = useSSE(getSSEUrl(id));

  // Apply live ticket/task updates
  useEffect(() => {
    for (const event of events) {
      if (event.type === "ticket_update") {
        const { id: tid, status } = event.data as { id: string; status: string };
        setTickets((prev) =>
          prev.map((t) => t.id === tid ? { ...t, status: status as Ticket["status"] } : t)
        );
      }
      if (event.type === "task_update") {
        const { id: tsid, status } = event.data as { id: string; status: string };
        setTickets((prev) =>
          prev.map((t) => ({
            ...t,
            tasks: t.tasks.map((task) =>
              task.id === tsid ? { ...task, status: status as typeof task.status } : task
            ),
          }))
        );
      }
    }
  }, [events]);

  useEffect(() => {
    getTickets(id)
      .then(setTickets)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  const handleExecute = async () => {
    try {
      setExecuting(true);
      setError(null);
      await executeProject(id);
    } catch (e) {
      setError(String(e));
      setExecuting(false);
    }
  };

  const toggleExpand = (ticketId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(ticketId) ? next.delete(ticketId) : next.add(ticketId);
      return next;
    });
  };

  const doneCount = tickets.filter((t) => t.status === "done").length;
  const isExecuting = tickets.some((t) => t.status === "in_progress");

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto p-8">
        <Link href={`/projects/${id}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Project
        </Link>

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Tickets</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {tickets.length > 0 ? `${doneCount} / ${tickets.length} done` : "Generated from architecture"}
            </p>
          </div>
          <div className="flex gap-2">
            <Link href={`/projects/${id}/logs`}>
              <Button variant="outline">View Logs</Button>
            </Link>
            <Button onClick={handleExecute} disabled={executing || isExecuting || tickets.length === 0}>
              {executing || isExecuting ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Executing...</>
              ) : (
                <><Play className="h-4 w-4" /> Execute All</>
              )}
            </Button>
          </div>
        </div>

        {error && <p className="text-destructive text-sm mb-4">{error}</p>}

        {loading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading tickets...
          </div>
        )}

        {!loading && tickets.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              No tickets yet. Approve the architecture to generate tickets.
            </CardContent>
          </Card>
        )}

        {/* Progress bar */}
        {tickets.length > 0 && (
          <div className="mb-6">
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${(doneCount / tickets.length) * 100}%` }}
              />
            </div>
          </div>
        )}

        <div className="space-y-3">
          {tickets.map((ticket) => {
            const isOpen = expanded.has(ticket.id);
            return (
              <Card key={ticket.id} className={ticket.status === "failed" ? "border-destructive/50" : ""}>
                <CardHeader
                  className="cursor-pointer pb-3"
                  onClick={() => toggleExpand(ticket.id)}
                >
                  <div className="flex items-center gap-3">
                    {statusIcon[ticket.status] || statusIcon.pending}
                    <CardTitle className="text-base flex-1">{ticket.title}</CardTitle>
                    <Badge variant={statusBadge[ticket.status] ?? "secondary"}>
                      {ticket.status.replace("_", " ")}
                    </Badge>
                    {isOpen ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                  </div>
                </CardHeader>

                {isOpen && (
                  <CardContent className="pt-0">
                    <p className="text-sm text-muted-foreground mb-3">{ticket.description}</p>
                    <p className="text-xs font-medium mb-2">Acceptance Criteria</p>
                    <p className="text-xs text-muted-foreground mb-4">{ticket.acceptance_criteria}</p>

                    <div className="space-y-2">
                      <p className="text-xs font-medium">Tasks ({ticket.tasks.filter((t) => t.status === "done").length}/{ticket.tasks.length})</p>
                      {ticket.tasks.map((task) => (
                        <div key={task.id} className="flex items-center gap-2 text-sm pl-2 border-l-2 border-muted">
                          {statusIcon[task.status] || statusIcon.pending}
                          <span className={task.status === "done" ? "line-through text-muted-foreground" : ""}>{task.title}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
