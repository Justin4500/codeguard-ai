import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, ShieldCheck, Undo2, XCircle } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { DiffViewer, languageFromPath } from "@/components/common/CodeViewer";
import { PageHeader } from "@/components/common/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, ErrorState, Spinner } from "@/components/ui/feedback";
import { Separator } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { fixApi } from "@/services/endpoints";
import { formatDate } from "@/lib/utils";

export default function PatchReviewPage() {
  const { id } = useParams();
  const fixId = Number(id);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const fixQuery = useQuery({
    queryKey: ["fix", fixId],
    queryFn: () => fixApi.get(fixId),
    enabled: Number.isFinite(fixId),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["fix", fixId] });
    queryClient.invalidateQueries({ queryKey: ["finding-fixes"] });
    queryClient.invalidateQueries({ queryKey: ["finding"] });
  };

  const approve = useMutation({
    mutationFn: () => fixApi.approve(fixId),
    onSuccess: (res) => {
      toast({ title: "Fix applied", description: res.message, variant: "success" });
      invalidate();
    },
    onError: (err: Error) => toast({ title: "Apply failed", description: err.message, variant: "error" }),
  });

  const reject = useMutation({
    mutationFn: () => fixApi.reject(fixId),
    onSuccess: () => {
      toast({ title: "Proposal rejected", variant: "info" });
      invalidate();
    },
    onError: (err: Error) => toast({ title: "Reject failed", description: err.message, variant: "error" }),
  });

  const revert = useMutation({
    mutationFn: () => fixApi.revert(fixId),
    onSuccess: () => {
      toast({ title: "Fix reverted", description: "The original file was restored.", variant: "success" });
      invalidate();
    },
    onError: (err: Error) => toast({ title: "Revert failed", description: err.message, variant: "error" }),
  });

  const fix = fixQuery.data;

  if (fixQuery.isError) {
    return <ErrorState message={(fixQuery.error as Error).message} onRetry={() => fixQuery.refetch()} />;
  }

  if (!fix) {
    return (
      <Card>
        <CardContent className="space-y-3">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-72 w-full" />
        </CardContent>
      </Card>
    );
  }

  const isApproved = fix.status === "approved";
  const isRejected = fix.status === "rejected";
  const language = languageFromPath(fix.file_path);

  return (
    <div className="space-y-6">
      <Link to={`/findings/${fix.finding_id}/fixes`} className="inline-flex items-center gap-1.5 text-[13px] text-muted hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to fix suggestions
      </Link>

      <PageHeader
        title="Patch review"
        description={
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="mono">{fix.file_path}</span>
            <Badge variant={isApproved ? "success" : isRejected ? "muted" : "default"}>{fix.status}</Badge>
            <span className="text-muted">{fix.generator === "ai" ? "AI-assisted" : "Deterministic template"}</span>
          </span>
        }
        actions={
          <>
            {!isApproved && !isRejected && (
              <>
                <Button variant="outline" size="sm" onClick={() => reject.mutate()} disabled={reject.isPending}>
                  {reject.isPending ? <Spinner /> : <XCircle className="h-4 w-4" />}
                  Reject
                </Button>
                <Button size="sm" onClick={() => approve.mutate()} disabled={approve.isPending}>
                  {approve.isPending ? <Spinner /> : <CheckCircle2 className="h-4 w-4" />}
                  Approve &amp; apply
                </Button>
              </>
            )}
            {isApproved && (
              <Button variant="outline" size="sm" onClick={() => revert.mutate()} disabled={revert.isPending}>
                {revert.isPending ? <Spinner /> : <Undo2 className="h-4 w-4" />}
                Revert
              </Button>
            )}
          </>
        }
      />

      {fix.explanation && <Alert variant="default">{fix.explanation}</Alert>}

      {isApproved && (
        <Alert variant="success">
          <p className="flex items-center gap-2 font-medium">
            <ShieldCheck className="h-4 w-4" />
            Applied & validated
          </p>
          {fix.validation_output && <p className="mt-1 whitespace-pre-wrap">{fix.validation_output}</p>}
        </Alert>
      )}

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>Proposed change</CardTitle>
          <span className="text-[12px] text-muted">{formatDate(fix.created_at)}</span>
        </CardHeader>
        <CardContent className="space-y-4">
          <DiffViewer original={fix.original_code} modified={fix.proposed_code} language={language} height={380} />

          <details className="rounded-md border border-border bg-elevated p-4">
            <summary className="cursor-pointer text-[13px] font-medium">Unified diff</summary>
            <Separator className="my-3" />
            <pre className="mono overflow-x-auto whitespace-pre-wrap text-muted">{fix.diff}</pre>
          </details>
        </CardContent>
      </Card>
    </div>
  );
}
