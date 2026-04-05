"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Folder, Clock, CheckCircle, XCircle, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getProjects, deleteProject } from "@/lib/api";
import type { Project, ProjectStatus } from "@/lib/types";

const statusConfig: Record<ProjectStatus, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" | "outline" }> = {
  new: { label: "New", variant: "secondary" },
  clarifying: { label: "Clarifying", variant: "warning" },
  arch_pending: { label: "Architecture", variant: "warning" },
  arch_approved: { label: "Ready", variant: "success" },
  executing: { label: "Executing", variant: "default" },
  done: { label: "Done", variant: "success" },
  failed: { label: "Failed", variant: "destructive" },
};

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      const data = await getProjects();
      setProjects(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (!confirm("Delete this project?")) return;
    await deleteProject(id);
    setProjects((p) => p.filter((x) => x.id !== id));
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-muted-foreground text-sm mt-1">Your AI-generated software projects</p>
        </div>
        <Link href="/projects/new">
          <Button>
            <Plus className="h-4 w-4" />
            New Project
          </Button>
        </Link>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading projects...
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {!loading && !error && projects.length === 0 && (
        <Card className="text-center py-16">
          <CardContent>
            <Folder className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No projects yet.</p>
            <Link href="/projects/new">
              <Button className="mt-4">Create your first project</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => {
          const cfg = statusConfig[project.status] ?? { label: project.status, variant: "secondary" };
          return (
            <Link key={project.id} href={`/projects/${project.id}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{project.name}</CardTitle>
                    <Badge variant={cfg.variant as never}>{cfg.label}</Badge>
                  </div>
                  <CardDescription>
                    {new Date(project.created_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <button
                    onClick={(e) => handleDelete(project.id, e)}
                    className="text-xs text-muted-foreground hover:text-destructive transition-colors"
                  >
                    Delete
                  </button>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
