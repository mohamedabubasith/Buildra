"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Send, FileText, Ticket, Terminal, CheckCircle2,
  Loader2, AlertCircle, ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getProject, answerClarification, getSSEUrl } from "@/lib/api";
import { useSSE } from "@/hooks/useSSE";
import type { Project, SSEEvent } from "@/lib/types";

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [logs, setLogs] = useState<Array<{ level: string; message: string }>>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const { events } = useSSE(id ? getSSEUrl(id) : null);

  // Process SSE events
  useEffect(() => {
    for (const event of events) {
      if (event.type === "log") {
        setLogs((prev) => [...prev, event.data as { level: string; message: string }]);
      }
      if (event.type === "clarification_question") {
        setPendingQuestion((event.data as { question: string }).question);
      }
      if (event.type === "status_change") {
        const status = (event.data as { status: string }).status;
        setProject((p) => p ? { ...p, status: status as Project["status"] } : p);
        // Redirect to relevant page after status change
        if (status === "arch_pending") {
          setTimeout(() => router.push(`/projects/${id}/architecture`), 1500);
        }
        if (status === "arch_approved") {
          setTimeout(() => router.push(`/projects/${id}/tickets`), 1500);
        }
      }
    }
  }, [events, id, router]);

  // Scroll logs to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    getProject(id).then(setProject).catch(console.error);
  }, [id]);

  const handleAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;
    try {
      setSubmitting(true);
      await answerClarification(id, answer.trim());
      setAnswer("");
      setPendingQuestion(null);
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  const navItems = [
    { href: `/projects/${id}/architecture`, label: "Architecture", icon: FileText, status: ["arch_pending", "arch_approved", "executing", "done"] },
    { href: `/projects/${id}/tickets`, label: "Tickets", icon: Ticket, status: ["arch_approved", "executing", "done"] },
    { href: `/projects/${id}/logs`, label: "Live Logs", icon: Terminal, status: ["executing", "done", "failed"] },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto p-8">
        <Link href="/dashboard" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="h-3.5 w-3.5" />
          Dashboard
        </Link>

        <div className="flex items-center gap-3 mb-8">
          <h1 className="text-2xl font-bold">{project?.name || "Loading..."}</h1>
          {project && (
            <Badge variant="secondary">{project.status.replace("_", " ")}</Badge>
          )}
        </div>

        {/* Navigation cards */}
        {project && (
          <div className="grid grid-cols-3 gap-3 mb-8">
            {navItems.map(({ href, label, icon: Icon, status }) => {
              const available = status.includes(project.status);
              return (
                <Link key={href} href={available ? href : "#"}>
                  <Card className={`transition-all ${available ? "hover:shadow-md cursor-pointer" : "opacity-40 cursor-not-allowed"}`}>
                    <CardContent className="flex items-center gap-2 p-4">
                      <Icon className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">{label}</span>
                      {available && <ChevronRight className="h-3 w-3 ml-auto text-muted-foreground" />}
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}

        {/* Clarification Chat */}
        {pendingQuestion && (
          <Card className="mb-6 border-primary/30">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-primary" />
                Clarification Needed
              </CardTitle>
              <CardDescription>{pendingQuestion}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAnswer} className="flex gap-2">
                <Input
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Your answer..."
                  disabled={submitting}
                  className="flex-1"
                />
                <Button type="submit" disabled={submitting} size="icon">
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Status / Progress */}
        {project?.status === "clarifying" && !pendingQuestion && (
          <Card>
            <CardContent className="flex items-center gap-2 p-6 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing requirement...
            </CardContent>
          </Card>
        )}

        {project?.status === "arch_pending" && (
          <Card className="border-green-200">
            <CardContent className="flex items-center gap-2 p-6 text-green-700">
              <CheckCircle2 className="h-4 w-4" />
              Architecture generated! Redirecting...
            </CardContent>
          </Card>
        )}

        {/* Live log feed */}
        {logs.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 max-h-48 overflow-y-auto font-mono text-xs">
                {logs.map((log, i) => (
                  <div
                    key={i}
                    className={`${
                      log.level === "error" ? "text-destructive" :
                      log.level === "warn" ? "text-yellow-600" :
                      "text-muted-foreground"
                    }`}
                  >
                    {log.message}
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
