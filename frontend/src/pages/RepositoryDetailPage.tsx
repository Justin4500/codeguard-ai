import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, Github, Play, Star } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { ScanStatusBadge } from "@/components/common/StatusBadges";
import { StatCard } from "@/components/common/StatCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Spinner } from "@/components/ui/feedback";
import { Label, Select } from "@/components/ui/input";
import { SkeletonTable } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { repoApi, scanApi } from "@/services/endpoints";
import { formatRelative, shortSha } from "@/lib/utils";

export default function RepositoryDetailPage() {
  const { id } = useParams();
  const repoId = Number(id);
  const navigate = useNavigate();
  const { toast } = useToast();
  const [branch, setBranch] = useState<string>("");

  const repoQuery = useQuery({
    queryKey: ["repository", repoId],
    queryFn: () => repoApi.get(repoId),
    enabled: Number.isFinite(repoId),
  });

  const branchesQuery = useQuery({
    queryKey: ["repository-branches", repoId],
    queryFn: () => repoApi.branches(repoId),
    enabled: Number.isFinite(repoId),
    retry: false,
  });

  const scansQuery = useQuery({
    queryKey: ["scans", { repository_id: repoId }],
    queryFn: () => scanApi.list({ repository_id: repoId }),
    enabled: Number.isFinite(repoId),
  });

  const startScan = useMutation({
    mutationFn: () => scanApi.start(repoId, branch || undefined),
    onSuccess: (scan) => {
      toast({ title: "Scan queued", variant: "success" });
      navigate(`/scans/${scan.id}`);
    },
    onError: (err: Error) => toast({ title: "Could not start scan", description: err.message, variant: "error" }),
  });

  const repo = repoQuery.data;

  if (repoQuery.isError) {
    return <ErrorState message={(repoQuery.error as Error).message} onRetry={() => repoQuery.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <Link to="/repositories" className="inline-flex items-center gap-1.5 text-[13px] text-muted hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to repositories
      </Link>

      {!repo ? (
        <Card>
          <SkeletonTable rows={3} />
        </Card>
      ) : (
        <>
          <PageHeader
            title={
              <span className="flex items-center gap-2">
                <Github className="h-4 w-4 text-muted" />
                {repo.full_name}
              </span>
            }
            description={repo.description || "No description provided."}
            actions={
              <>
                <a href={repo.url} target="_blank" rel="noreferrer">
                  <Button variant="outline" size="sm">
                    <ExternalLink className="h-4 w-4" />
                    Open on GitHub
                  </Button>
                </a>
                <Button size="sm" onClick={() => startScan.mutate()} disabled={startScan.isPending}>
                  {startScan.isPending ? <Spinner /> : <Play className="h-4 w-4" />}
                  Start scan
                </Button>
              </>
            }
          />

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Scans" value={repo.scan_count} />
            <StatCard label="Findings" value={repo.finding_count} />
            <StatCard label="Critical" value={repo.critical_count} tone={repo.critical_count > 0 ? "critical" : "default"} />
            <StatCard label="Stars" value={repo.stars ?? 0} icon={Star} />
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Repository details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-[13px]">
                <Row label="Language" value={repo.language ?? "—"} />
                <Row label="Visibility" value={repo.visibility} />
                <Row label="Default branch" value={repo.default_branch ?? "—"} />
                <Row label="Size" value={repo.size_kb ? `${repo.size_kb.toLocaleString()} KB` : "—"} />
                <Row label="Last scanned" value={formatRelative(repo.last_scanned_at)} />
                {repo.last_scan_status && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted">Last status</span>
                    <ScanStatusBadge status={repo.last_scan_status} />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Scan this repository</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5 max-w-sm">
                  <Label htmlFor="branch-select">Branch</Label>
                  <Select
                    id="branch-select"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    disabled={branchesQuery.isLoading || !branchesQuery.data}
                  >
                    <option value="">Default ({repo.default_branch ?? "main"})</option>
                    {branchesQuery.data?.branches.map((b) => (
                      <option key={b} value={b}>
                        {b}
                      </option>
                    ))}
                  </Select>
                  {branchesQuery.isError && (
                    <p className="text-[12px] text-muted">
                      Branch list unavailable (private repo or token missing) — the default branch will be used.
                    </p>
                  )}
                </div>
                <Button onClick={() => startScan.mutate()} disabled={startScan.isPending}>
                  {startScan.isPending ? <Spinner /> : <Play className="h-4 w-4" />}
                  Run scan
                </Button>
                <p className="text-[12px] text-muted">
                  The repository is cloned to a temporary workspace, scanned with real tools, then cleaned up. Your
                  GitHub repository is never modified.
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Scan history</CardTitle>
            </CardHeader>
            <CardContent className="p-0 pb-1">
              {scansQuery.isLoading ? (
                <SkeletonTable rows={3} />
              ) : !scansQuery.data || scansQuery.data.length === 0 ? (
                <EmptyState icon={<Play className="h-5 w-5" />} title="No scans yet" description="Run a scan to see results here." />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Scan</TableHead>
                      <TableHead>Branch</TableHead>
                      <TableHead>Commit</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Findings</TableHead>
                      <TableHead>Started</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {scansQuery.data.map((scan) => (
                      <TableRow key={scan.id}>
                        <TableCell>
                          <Link to={`/scans/${scan.id}`} className="font-medium hover:text-accent">
                            #{scan.id}
                          </Link>
                        </TableCell>
                        <TableCell className="mono text-muted">{scan.branch ?? "—"}</TableCell>
                        <TableCell className="mono text-muted">{shortSha(scan.commit_sha)}</TableCell>
                        <TableCell>
                          <ScanStatusBadge status={scan.status} />
                        </TableCell>
                        <TableCell className="tabular-nums">{scan.total_findings}</TableCell>
                        <TableCell className="text-[12px] text-muted">{formatRelative(scan.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-muted">{label}</span>
      <span className="truncate text-right">{value}</span>
    </div>
  );
}
