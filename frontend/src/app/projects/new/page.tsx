"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Rocket } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { createProject, submitRequirement } from "@/lib/api";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [requirement, setRequirement] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !requirement.trim()) {
      setError("Both fields are required.");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const project = await createProject(name.trim());
      await submitRequirement(project.id, requirement.trim());
      router.push(`/projects/${project.id}`);
    } catch (e) {
      setError(String(e));
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-2xl mx-auto">
        <Link href="/dashboard" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Projects
        </Link>

        <h1 className="text-2xl font-bold mb-1">New Project</h1>
        <p className="text-muted-foreground text-sm mb-8">
          Describe what you want to build. The AI will clarify, architect, and build it.
        </p>

        <Card>
          <CardHeader>
            <CardTitle>Your Product Requirement</CardTitle>
            <CardDescription>
              Be as detailed as possible. The AI will ask clarifying questions if needed.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Project Name</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Awesome App"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium">Requirement</label>
                <Textarea
                  value={requirement}
                  onChange={(e) => setRequirement(e.target.value)}
                  placeholder="Build a task management app with user authentication, projects, tasks with priorities, due dates, and a dashboard showing overdue tasks..."
                  rows={8}
                  className="resize-none"
                />
              </div>

              {error && <p className="text-sm text-destructive">{error}</p>}

              <Button type="submit" disabled={loading} className="w-full" size="lg">
                {loading ? (
                  "Starting..."
                ) : (
                  <><Rocket className="h-4 w-4" /> Start Building</>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
