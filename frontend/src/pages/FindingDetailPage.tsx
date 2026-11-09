import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Lightbulb, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { CodeViewer } from "@/components/common/CodeViewer";
import { PageHeader } from "@/components/common/PageHeader";
import { FindingStatusBadge, SeverityBadge } from "@/components/common/StatusBadges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, ErrorState, Spinner } from "@/components/ui/feedback";
import { Label, Select } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { findingApi } from "@/services/endpoints";
import { formatDate } from "@/lib/utils";

const STATUSES = ["open", "confirmed", "false_positive", "fix_proposed", "fixed", "ignored"];

export default function FindingDetailPage() {
  const { id } = useParams();
  const findingId = Number(id);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [explanation, setExplanation] = useState<string | null>(null);

  const findingQuery = useQuery({
    queryKey: ["finding", findingId],
    queryFn: () => findingApi.get(findingId),
    enabled: Number.isFinite(findingId),
  });

  const finding = findingQuery.data;

  useEffect(() => {
    setExplanation(null);
  }, [findingId]);

  const updateStatus = useMutation({
    mutationFn: (status: string) => findingApi.update(findingId, { status }),
    onSuccess: () => {
      toast({ title: "Status updated", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["finding", findingId] });
      queryClient.invalidateQueries({ queryKey: ["findings"] });
    },
    onError: (err: Error) => toast({ title: "Update failed", description: err.message, variant: "error" }),
  });

  const explain = useMutation({
    mutationFn: () => findingApi.explain(findingId),
    onSuccess: (res) => setExplanation(res.explanation),
    onError: (err: Error) => toast({ title: "Explanation failed", description: err.message, variant: "error" }),
  });

  if (findingQuery.isError) {
    return <ErrorState message={(findingQuery.error as Error).message} onRetry={() => findingQuery.refetch()} />;
  }

  if (!finding) {
    return (
      <Card>
        <CardContent className="space-y-3">
          <Skeleton className="h-6 w-1/2" />
          <Skeleton className="h-40 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Link to="/findings" className="inline-flex items-center gap-1.5 text-[13px] text-muted hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to findings
      </Link>

      <PageHeader
        title={finding.title}
        description={
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[13px]">
            <SeverityBadge severity={finding.severity} />
            <span className="text-muted">{finding.category}</span>
            {finding.rule_id && <span className="mono text-muted">{finding.rule_id}</span>}
            {finding.cwe && <span className="mono text-muted">{finding.cwe}</span>}
          </span>
        }
        actions={
          <Link to={`/findings/${finding.id}/fixes`}>
            <Button size="sm">
              <Wrench className="h-4 w-4" />
              Review fixes
            </Button>
          </Link>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Location</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="mono text-[13px] text-muted">
                {finding.file_path ?? "—"}
                {finding.line_number ? `:${finding.line_number}` : ""}
                {finding.end_line && finding.end_line !== finding.line_number ? `-${finding.end_line}` : ""}
              </div>
              {finding.code_excerpt ? (
                <CodeViewer
                  value={finding.code_excerpt}
                  path={finding.file_path}
                  height={280}
                />
              ) : (
                <Alert>No code excerpt was captured for this finding.</Alert>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>What is this?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-[13px] leading-relaxed">
              <p className="text-muted">{finding.description ?? "No description available."}</p>
              {finding.remediation && (
                <div className="rounded-md border border-border bg-elevated p-4">
                  <p className="mb-1 text-[12px] font-medium uppercase tracking-wide text-muted">Remediation</p>
                  <p>{finding.remediation}</p>
                </div>
              )}
              <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" onClick={() => explain.mutate()} disabled={explain.isPending}>
                  {explain.isPending ? <Spinner /> : <Lightbulb className="h-4 w-4" />}
                  Explain this finding
                </Button>
                <span className="text-[12px] text-muted">Uses AI when configured, otherwise a built-in explanation.</span>
              </div>
              {explanation && (
                <div className="rounded-md border border-accent/25 bg-accent/5 p-4 whitespace-pre-wrap">{explanation}</div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Properties</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-[13px]">
              <Field label="Status">
                <FindingStatusBadge status={finding.status} />
              </Field>
              <Field label="Tool">
                <span className="mono">{finding.tool}</span>
              </Field>
              <Field label="Kind">
                <span>{finding.kind}</span>
              </Field>
              <Field label="Detected">
                <span>{formatDate(finding.created_at)}</span>
              </Field>
              {finding.confidence != null && (
                <Field label="Confidence">
                  <span className="tabular-nums">{Math.round(finding.confidence * 100)}%</span>
                </Field>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Triage</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="status-select">Set status</Label>
                <Select
                  id="status-select"
                  value={finding.status}
                  onChange={(e) => updateStatus.mutate(e.target.value)}
                  disabled={updateStatus.isPending}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, " ")}
                    </option>
                  ))}
                </Select>
              </div>
              <Link to={`/scans/${finding.scan_id}`} className="block text-[13px] text-accent hover:underline">
                View source scan #{finding.scan_id}
              </Link>
              <Link to={`/repositories/${finding.repository_id}`} className="block text-[13px] text-accent hover:underline">
                View repository
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted">{label}</span>
      <span>{children}</span>
    </div>
  );
}
