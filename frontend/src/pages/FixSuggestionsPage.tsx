import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, FileCode, Sparkles, Wrench } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { SeverityBadge } from "@/components/common/StatusBadges";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, ErrorState, Spinner } from "@/components/ui/feedback";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { fixApi, findingApi } from "@/services/endpoints";
import { formatDate } from "@/lib/utils";

export default function FixSuggestionsPage() {
  const { id } = useParams();
  const findingId = Number(id);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const findingQuery = useQuery({
    queryKey: ["finding", findingId],
    queryFn: () => findingApi.get(findingId),
    enabled: Number.isFinite(findingId),
  });

  const fixesQuery = useQuery({
    queryKey: ["finding-fixes", findingId],
    queryFn: () => fixApi.list(findingId),
    enabled: Number.isFinite(findingId),
  });

  const propose = useMutation({
    mutationFn: () => fixApi.propose(findingId),
    onSuccess: () => {
      toast({ title: "Fix proposal generated", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["finding-fixes", findingId] });
      queryClient.invalidateQueries({ queryKey: ["finding", findingId] });
    },
    onError: (err: Error) => toast({ title: "Could not generate fix", description: err.message, variant: "error" }),
  });

  const finding = findingQuery.data;

  return (
    <div className="space-y-6">
      <Link to={`/findings/${findingId}`} className="inline-flex items-center gap-1.5 text-[13px] text-muted hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to finding
      </Link>

      <PageHeader
        title="Fix suggestions"
        description={
          finding ? (
            <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <SeverityBadge severity={finding.severity} />
              <span>{finding.title}</span>
            </span>
          ) : (
            "Generate and review proposed fixes."
          )
        }
        actions={
          <Button size="sm" onClick={() => propose.mutate()} disabled={propose.isPending}>
            {propose.isPending ? <Spinner /> : <Sparkles className="h-4 w-4" />}
            Generate fix
          </Button>
        }
      />

      <Alert>
        Fixes are proposed as diffs. Nothing changes until you approve them on the review screen, and applied changes are
        validated in an isolated copy — your repository is never modified or pushed.
      </Alert>

      {findingQuery.isError && (
        <ErrorState message={(findingQuery.error as Error).message} onRetry={() => findingQuery.refetch()} />
      )}

      <Card>
        <CardHeader>
          <CardTitle>Proposals</CardTitle>
        </CardHeader>
        <CardContent className="p-0 pb-2">
          {fixesQuery.isLoading ? (
            <div className="space-y-2 p-5">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : fixesQuery.isError ? (
            <ErrorState message={(fixesQuery.error as Error).message} onRetry={() => fixesQuery.refetch()} />
          ) : !fixesQuery.data || fixesQuery.data.length === 0 ? (
            <EmptyState
              icon={<Wrench className="h-5 w-5" />}
              title="No fix proposals yet"
              description={finding?.rule_id ? `Generate a deterministic fix for rule ${finding.rule_id}.` : "Generate a fix proposal for this finding."}
              action={
                <Button size="sm" onClick={() => propose.mutate()} disabled={propose.isPending}>
                  {propose.isPending ? <Spinner /> : <Sparkles className="h-4 w-4" />}
                  Generate fix
                </Button>
              }
            />
          ) : (
            <div className="divide-y divide-border">
              {fixesQuery.data.map((fix) => (
                <div key={fix.id} className="flex flex-wrap items-center justify-between gap-3 p-5">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <FileCode className="h-4 w-4 text-muted" />
                      <span className="mono text-[13px]">{fix.file_path}</span>
                      <Badge
                        variant={fix.status === "approved" ? "success" : fix.status === "rejected" ? "muted" : "default"}
                      >
                        {fix.status}
                      </Badge>
                    </div>
                    <p className="mt-1 text-[12px] text-muted">
                      {fix.generator === "ai" ? "AI-assisted" : "Deterministic template"} · created {formatDate(fix.created_at)}
                    </p>
                    {fix.explanation && <p className="mt-1 max-w-2xl text-[13px] text-muted">{fix.explanation}</p>}
                  </div>
                  <Link to={`/fixes/${fix.id}`}>
                    <Button size="sm" variant="outline">
                      {fix.status === "approved" ? <CheckCircle2 className="h-4 w-4" /> : null}
                      Review diff
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
