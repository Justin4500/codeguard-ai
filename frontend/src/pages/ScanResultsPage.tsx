import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Download, FileText, Loader2, RefreshCw, XCircle } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { ScanStatusBadge, SeverityBadge } from "@/components/common/StatusBadges";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, EmptyState, ErrorState } from "@/components/ui/feedback";
import { Progress, Separator } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { downloadFile } from "@/lib/api";
import { duration, formatDate, shortSha } from "@/lib/utils";
import { findingApi, reportDownloadPath, reportFilename, scanApi } from "@/services/endpoints";
import type { Severity } from "@/types";

const SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "informational"];

export default function ScanResultsPage() {
  const { id } = useParams();
  const scanId = Number(id);
  const { toast } = useToast();
  const [downloading, setDownloading] = useState<string | null>(null);

  const scanQuery = useQuery({
    queryKey: ["scan", scanId],
    queryFn: () => scanApi.get(scanId),
    enabled: Number.isFinite(scanId),
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "queued" || s === "running" ? 1500 : false;
    },
  });

  const scan = scanQuery.data;
  const isActive = scan?.status === "queued" || scan?.status === "running";

  const findingsQuery = useQuery({
    queryKey: ["findings", { scan_id: scanId, page_size: 1 }],
    queryFn: () => findingApi.list({ scan_id: scanId, page_size: 1 }),
    enabled: Boolean(scan) && scan?.status === "completed",
  });

  const cancelScan = async () => {
    try {
      await scanApi.cancel(scanId);
      toast({ title: "Scan cancelled", variant: "info" });
      scanQuery.refetch();
    } catch (err) {
      toast({ title: "Could not cancel", description: (err as Error).message, variant: "error" });
    }
  };

  const handleDownload = async (format: "html" | "json" | "csv" | "pdf") => {
    if (!scan) return;
    setDownloading(format);
    try {
      await downloadFile(reportDownloadPath(scan.id, format), reportFilename(scan.repository_full_name ?? `scan-${scan.id}`, scan.id, format));
    } catch (err) {
      toast({ title: "Export failed", description: (err as Error).message, variant: "error" });
    } finally {
      setDownloading(null);
    }
  };

  if (scanQuery.isError) {
    return <ErrorState message={(scanQuery.error as Error).message} onRetry={() => scanQuery.refetch()} />;
  }

  if (!scan) {
    return (
      <Card>
        <CardContent className="space-y-3">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  const counts = findingsQuery.data?.severity_counts ?? {};

  return (
    <div className="space-y-6">
      <Link
        to={scan.repository_id ? `/repositories/${scan.repository_id}` : "/scans"}
        className="inline-flex items-center gap-1.5 text-[13px] text-muted hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back
      </Link>

      <PageHeader
        title={
          <span className="flex items-center gap-3">
            Scan #{scan.id}
            <ScanStatusBadge status={scan.status} />
          </span>
        }
        description={
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span>{scan.repository_full_name ?? `Repository #${scan.repository_id}`}</span>
            <span className="mono">{scan.branch ?? "—"}</span>
            {scan.commit_sha && <span className="mono">{shortSha(scan.commit_sha)}</span>}
            <span>Started {formatDate(scan.started_at ?? scan.created_at)}</span>
            {scan.duration_seconds != null && <span>· {duration(scan.duration_seconds)}</span>}
          </span>
        }
        actions={
          isActive ? (
            <Button variant="outline" size="sm" onClick={cancelScan}>
              <XCircle className="h-4 w-4" />
              Cancel
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => scanQuery.refetch()}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          )
        }
      />

      {scan.status === "failed" && (
        <Alert variant="error">
          <p className="font-medium">Scan failed</p>
          <p className="mt-0.5">{scan.error_message ?? "An unknown error occurred while scanning."}</p>
        </Alert>
      )}

      {isActive && (
        <Card>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-[13px]">
              <span className="flex items-center gap-2 text-muted">
                <Loader2 className="h-4 w-4 animate-spin text-accent" />
                {scan.stage ?? "Working…"}
              </span>
              <span className="tabular-nums text-muted">{scan.progress}%</span>
            </div>
            <Progress value={scan.progress} />
            <p className="text-[12px] text-muted">
              Files scanned: {scan.files_scanned}. This page updates automatically.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Findings summary</CardTitle>
            {scan.status === "completed" && (
              <Link to={`/findings?scan_id=${scan.id}`} className="text-[13px] text-accent hover:underline">
                View all {scan.total_findings} findings
              </Link>
            )}
          </CardHeader>
          <CardContent>
            {scan.status !== "completed" ? (
              <EmptyState
                icon={<FileText className="h-5 w-5" />}
                title="Results will appear when the scan finishes"
                description="Analysis is running in the background."
              />
            ) : scan.total_findings === 0 ? (
              <EmptyState icon={<FileText className="h-5 w-5" />} title="No findings detected" description="This scan produced no issues. Nice work." />
            ) : (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                {SEVERITIES.map((sev) => (
                  <Link
                    key={sev}
                    to={`/findings?scan_id=${scan.id}&severity=${sev}`}
                    className="rounded-lg border border-border bg-elevated p-3 transition-colors hover:border-accent/40"
                  >
                    <SeverityBadge severity={sev} />
                    <p className="mt-2 text-xl font-semibold tabular-nums">{counts[sev] ?? 0}</p>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Export report</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button className="w-full justify-start" disabled={downloading !== null} onClick={() => handleDownload("pdf")}>
              <Download className="h-4 w-4" />
              PDF report (with charts)
            </Button>
            <Button variant="outline" className="w-full justify-start" disabled={downloading !== null} onClick={() => handleDownload("html")}>
              <Download className="h-4 w-4" />
              HTML report
            </Button>
            <Button variant="outline" className="w-full justify-start" disabled={downloading !== null} onClick={() => handleDownload("json")}>
              <Download className="h-4 w-4" />
              JSON report
            </Button>
            <Button variant="outline" className="w-full justify-start" disabled={downloading !== null} onClick={() => handleDownload("csv")}>
              <Download className="h-4 w-4" />
              CSV export
            </Button>
            <p className="pt-1 text-[12px] text-muted">
              The PDF includes charts, a scan flow diagram, strengths, and every finding explained in plain language.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Tools used</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {(scan.tools_used ?? []).length === 0 && <span className="text-[13px] text-muted">No tools recorded yet.</span>}
              {(scan.tools_used ?? []).map((tool) => (
                <Badge key={tool} variant="success">
                  {tool}
                </Badge>
              ))}
            </div>
            {(scan.tools_skipped ?? []).length > 0 && (
              <>
                <Separator />
                <p className="text-[12px] font-medium uppercase tracking-wide text-muted">Skipped (not installed)</p>
                <div className="space-y-1.5">
                  {(scan.tools_skipped ?? []).map((t) => (
                    <div key={t.tool} className="text-[13px]">
                      <span className="font-medium">{t.tool}</span>
                      <span className="text-muted"> — {t.reason}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Languages detected</CardTitle>
          </CardHeader>
          <CardContent>
            {(scan.languages ?? []).length === 0 ? (
              <span className="text-[13px] text-muted">No language data available yet.</span>
            ) : (
              <div className="space-y-2">
                {(scan.languages ?? []).map((lang) => (
                  <div key={lang.language} className="flex items-center justify-between text-[13px]">
                    <span>{lang.language}</span>
                    <span className="tabular-nums text-muted">{lang.files} files</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {scan.ai_summary && (
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent className="text-[13px] leading-relaxed text-muted">{scan.ai_summary}</CardContent>
        </Card>
      )}
    </div>
  );
}
