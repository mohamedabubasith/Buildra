"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle, Loader2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getArchitecture, approveArchitecture } from "@/lib/api";
import type { Architecture } from "@/lib/types";

export default function ArchitecturePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [arch, setArch] = useState<Architecture | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getArchitecture(id)
      .then(setArch)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  const handleApprove = async () => {
    try {
      setApproving(true);
      await approveArchitecture(id);
      router.push(`/projects/${id}/tickets`);
    } catch (e) {
      setError(String(e));
      setApproving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto p-8">
        <Link href={`/projects/${id}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Project
        </Link>

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FileText className="h-6 w-6" />
              Architecture Document
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              Review the generated architecture before execution begins
            </p>
          </div>
          {arch && !arch.approved && (
            <Button onClick={handleApprove} disabled={approving} size="lg">
              {approving ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Approving...</>
              ) : (
                <><CheckCircle className="h-4 w-4" /> Approve & Generate Tickets</>
              )}
            </Button>
          )}
          {arch?.approved && (
            <div className="flex items-center gap-2 text-green-600 font-medium text-sm">
              <CheckCircle className="h-4 w-4" />
              Approved
            </div>
          )}
        </div>

        {error && <p className="text-destructive text-sm mb-4">{error}</p>}

        {loading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading architecture...
          </div>
        )}

        {!loading && !arch && (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              Architecture not generated yet. Submit your requirement first.
            </CardContent>
          </Card>
        )}

        {arch && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-muted-foreground font-mono text-xs uppercase tracking-widest">
                Generated Architecture
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap text-sm font-mono bg-muted p-6 rounded-lg overflow-auto max-h-[60vh] leading-relaxed">
                  {arch.markdown}
                </pre>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
